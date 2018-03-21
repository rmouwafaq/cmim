from openerp import models, fields,exceptions, api, _

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
    @api.onchange('partner_type')
    def _onchange_partner_type(self):
        # Set partner_id domain
        if self.partner_type:
            return {'domain': {'partner_id': [(self.partner_type, '=', True),
                                              ('type_entite', '=', 'c')]}}
class AccountInvoice(models.Model):
     
    _inherit = "account.invoice"
     
    cotisation_id = fields.One2many('cmim.cotisation', 'invoice_id', 'Cotisation')