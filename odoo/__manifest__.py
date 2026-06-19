{
    'name': 'NN Fund Management',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Fund Management',
    'summary': 'Incoming funds, allocations, requisitions, bills and transfers '
               'with GM/MD approval and a full audit trail',
    'description': """
NN Fund Management
===================
Tracks incoming funds, allocation to projects/expense heads, fund
requisitions, bills against approved requisitions, and transfers between
projects/expense heads - all gated by a configurable GM -> MD approval
workflow with a structured audit trail.

Core design principle: every balance (available, on hold, assigned,
spent) is a computed value derived live from the current state of the
underlying transactional records, never a manually maintained counter.
This is the main structural defence against double spending.
    """,
    'author': 'Tabassum',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'project'],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/fund_sequences.xml',
    ],
    'installable': True,
    'application': True,
}
