
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields,exceptions, api, _
from openerp.exceptions import UserError

class reglement(models.Model):
    _inherit = 'account.payment'
    _default = { 'payment_type' : 'inbound',
                'partner_type': 'customer',
                }
    import_flag = fields.Boolean('Par import', default=False)
    secteur_id = fields.Many2one('cmim.secteur',
        string='Secteur',
        related='partner_id.secteur_id', store=True
    )
    payroll_year_id =  fields.Many2one('py.year', 'Calendrier')
    payroll_period_id = fields.Many2one('py.period', 'Periode', domain="[('payroll_year_id','=',payroll_year_id)]")