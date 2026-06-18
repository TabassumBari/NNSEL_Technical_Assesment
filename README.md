# NN Fund Management (`nn_fund_management`)

> **Status: work in progress.** This README is being written alongside the
> code, not after it, so the *Assumptions* and *Known Limitations* sections
> reflect real decisions made during development rather than a
> reconstruction after the fact. Sections marked **TODO** will be filled in
> as the corresponding part of the module is built.

An Odoo custom module to track incoming funds, allocate them to projects or
expense heads, run fund requisitions and bills against approved
requisitions, and transfer funds between projects/expense heads — all
gated by a configurable GM → MD approval workflow with a full audit trail,
structured so the same money can never be allocated, transferred or spent
more than once.

## Odoo Version

Built and tested against **Odoo 17.0** (Community).

## Required Dependencies

Odoo apps only — no third-party Python packages beyond what a standard
Odoo 17 installation already requires:

- `base`
- `mail` (chatter / activity tracking on every document)
- `project` (the existing `project.project` model is extended rather than
  reinvented — see Architecture below)

## Architecture (short explanation)

The module is built around two reusable abstract mixins rather than
duplicating logic across the allocation / requisition / transfer models:

**`fund.balance.mixin`** — gives any allocation *target* (`project.project`,
extended in place, and a new `expense.head` model) a consistent set of
balance fields: `total_allocated`, `requisition_hold`, `transfer_hold`,
`reserved_unspent`, `total_spent`, `incoming_transfers`,
`outgoing_transfers`, `available_fund`. Every one of these is a **computed,
non-stored field** — there is no counter anywhere that gets manually
incremented or decremented as a request moves through its workflow.
Each balance is recalculated from the *current* state of the related
allocation/requisition/transfer/bill records every time it's read. This is
the structural defence against double spending: there's no running total
that can drift, get forgotten on a cancel path, or get double-applied by a
repeat click — there's simply nothing to keep in sync.

The same principle is used for `fund.account` (the source side): `received`,
`held`, `assigned` and `available` are computed the same way, from
`fund.incoming` and `fund.allocation` records.

**`fund.approval.mixin`** — the shared GM → MD workflow used by
`fund.allocation`, `fund.requisition` and `fund.transfer` (the latter two
not yet built — see Progress below). Approvers are `res.groups` membership
(`GM Approver`, `MD Approver`), not hardcoded users, so reassigning an
approver is a Settings change, not a code change. Every `action_*` method
starts by checking the record's current `state`, so a repeated click on
Approve raises an error rather than silently re-approving.

**`fund.audit.log`** is one shared, structured audit table for every fund
document (polymorphic via `res_model`/`res_id`, the same pattern Odoo uses
internally for `mail.message`). No security group has create/write access
to it directly — entries can only be appended via `_log_audit()` using
`sudo()`, so the trail can't be edited or deleted through the UI.

Cross-model references (e.g. an allocation's destination being *either* a
project *or* an expense head) use Odoo's `Reference` field type rather than
two separate optional `Many2one` fields, which keeps the "must be a project
or an expense head, not both" rule enforceable in one place.

## Progress So Far

**Implemented:**
- Module scaffold, manifest, security groups (`Fund User`, `Finance User`,
  `GM Approver`, `MD Approver`, `Fund Administrator`)
- `fund.audit.mixin` / `fund.audit.log` (structured audit trail)
- `fund.approval.mixin` (GM → MD workflow, not yet attached to a concrete
  model)
- `fund.balance.mixin`, applied to `expense.head` (new) and `project.project`
  (extended)
- `fund.account` (bank/cash/other accounts, computed balances)
- `fund.incoming` (incoming funds, draft → confirmed → cancelled, unique
  transaction reference per account, Finance-only confirmation)

**Not yet implemented:**
- `fund.allocation`, `fund.requisition`, `fund.bill`, `fund.transfer`
- All views/menus (the module currently has no UI)
- Record rules for multi-company data isolation
- Automated tests
- Dockerfile / docker-compose
- Screen recording, Git remote / push to a public repository

Per the brief's explicit allowance that full completion isn't mandatory,
the bonus features (configurable approval rule engine, bank email
integration, dashboard) are intentionally out of scope for this submission
in favour of a solid, well-tested core (sections 2–10 of the brief).

## Installation Instructions

*(Generic instructions for now; will be updated with exact `docker compose`
commands once the Docker setup is added.)*

1. Clone this repository.
2. Make the repository's folder available on Odoo's `addons-path` — either
   by placing it inside an existing custom addons directory named
   `nn_fund_management`, or by pointing `addons-path` at the parent
   directory of the clone.
3. Restart the Odoo server so it picks up the new addon.
4. In Odoo, enable developer mode, go to **Apps**, click **Update Apps
   List**, then search for and install **NN Fund Management**.

## Configuration Steps

*(Will be expanded as more models/security rules are added.)*

1. Go to **Settings → Users & Companies → Groups** and assign each user to
   the appropriate group(s): `Fund User`, `Finance User`, `GM Approver`,
   `MD Approver`, `Fund Administrator`.
2. Create one or more **Fund Accounts** (bank/cash/other) under the Fund
   Management app.
3. Create **Expense Heads** for non-project spending categories (e.g.
   Office Rent, Salary, Utilities).

## Testing Instructions

**TODO** — automated tests have not been written yet. For now, the
implemented pieces can be exercised manually:
1. As a Finance user, create a Fund Account.
2. Record an Incoming Fund against it and confirm it — verify
   `available_balance` on the account increases by the confirmed amount.
3. Try confirming the same incoming fund twice, or as a non-Finance user —
   both should be blocked with a clear error.
4. Try creating a second incoming fund with the same transaction reference
   on the same account — should be blocked by the database constraint.

## Assumptions

- "Project" allocation targets use Odoo's existing `project.project` model
  (extended with fund balance fields) rather than a new parallel model, to
  avoid duplicating functionality already provided by the standard Project
  app.
- Incoming funds require only a single Finance-user confirmation, not the
  GM → MD workflow — the brief specifies the two-level approval explicitly
  for allocations, requisitions and transfers, but only "confirmation" for
  incoming funds.
- Balance fields are intentionally non-stored computed fields (see
  Architecture) rather than stored + recomputed-on-write counters, trading
  a small amount of read performance for structural correctness.
- One shared `fund.audit.log` model is used for every document type instead
  of a separate audit table per model.

## Known Limitations

- There is currently no reversal flow for a *confirmed* incoming fund entry
  — once confirmed, it cannot be cancelled or deleted. (Bills, per the
  brief, do get a reversal flow once `fund.bill` is built.) A future
  iteration would add a proper offsetting-entry reversal rather than
  mutating the original record.
- Non-stored computed balance fields mean balance-heavy list/kanban views
  will issue several extra queries per record on each load. Acceptable at
  this scale; would be revisited (e.g. selectively stored + recomputed via
  explicit invalidation) if the dataset grew large.
- Multi-company record rules are not yet in place — see Progress above.
- (List will grow as remaining models are built — e.g. transfer/requisition
  edge cases, bonus features intentionally left out.)
