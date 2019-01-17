# -*- coding: utf-8 -*-
# © 2019 Agile Organisation
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Partner Overdue',
    'version': '9.0.1.0.2',
    'category': 'Account',
    'author': "Ayoub Zahid",
    'website': 'http://www.agilorg.com',
    'license': 'AGPL-3',
    'depends': [
        'account','ao_cmim'
    ],
    'data': [
        'reports/report_overdue.xml',
    ],
    'installable': True,
    'auto_install': False,
}
