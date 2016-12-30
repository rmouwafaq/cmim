
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields,exceptions, api, _
from openerp.exceptions import UserError

class validation_cotisation (models.TransientModel):
    _name = 'cmim.validation.cotisation'
    
    payroll_year_id =  fields.Many2one('py.year', 'Calendrier', required=True)
    payroll_period_id = fields.Many2one('py.period', 'Periode', domain="[('payroll_year_id','=',payroll_year_id)]", required=True)
    collectivite_ids = fields.Many2many('res.partner','validation_collectivite', 'validation_id', 'partner_id', "Collectivites", domain = "[('customer','=',True),('is_company','=',True)]")
    cotisation_ids = fields.Many2many('cmim.cotisation','validation_cotisation', 'validation_id', 'cotisaion_id', "Cotisations")
    state = fields.Selection(selection=[('init', 'Init'),
                                        ('select', 'Select'),
                                        ('validate', 'Validate')],
                                        string='Etat', 
                                        default = 'init',required=True)
    
    @api.multi
    def suivant_act(self, vals):
        col_ids = [x.id for x in self.collectivite_ids]       
        domain = [('collectivite_id.id','in',col_ids),('state','=','draft'),
                  ('payroll_year_id.id','=',self.payroll_year_id.id),
                  ('payroll_period_id.id','=',self.payroll_period_id.id)]
        records=self.env['cmim.cotisation'].search(domain)
        so_ids = [x.id for x in records]
        self.write({ 'state': 'select', 'cotisation_ids': [(6,0,so_ids)] })
        
        return {
                'type': 'ir.actions.act_window',
                'res_model': 'cmim.validation.cotisation',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': self.id,
                'view_id': 'ao_cmim.view_validation_cotisation',
                'views': [(False, 'form')],
                'target':'new',
            }
                
        
    @api.multi
    def valider_act(self):
        for cotisation in self.cotisation_ids:
            cotisation.action_validate()
            
        self.state="validate"    
        return {
                'type': 'ir.actions.act_window',
                'res_model': 'cmim.cotisation',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': self.id,
                'view_id': 'ao_cmim.cotisation_tree_view',
                'views': [(False, 'tree')],
                'domain':[('id', 'in', [x.id for x in self.cotisation_ids])],
                'target':'self',
            }
                
    @api.multi 
    def retour_act(self):
        self.state="init"
        return {
                'type': 'ir.actions.act_window',
                'res_model': 'cmim.validation.cotisation',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': self.id,
                'view_id': 'ao_cmim.view_validation_cotisation',
                'views': [(False, 'form')],
                'target':'new',
            }
        
    @api.multi
    def annuler_act(self):
        if(self.state=="select"):
            self.unlink(self.id)
        return True
    