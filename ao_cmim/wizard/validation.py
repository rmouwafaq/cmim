
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields,exceptions, api, _
from openerp.exceptions import UserError

class validation_cotisation (models.TransientModel):
    _name = 'cmim.validation.cotisation'
    
    @api.onchange('fiscal_date')
    def onchange_field_id(self):
         if self.fiscal_date:
            periodes = self.env['date.range'].search([])
            ids = []
            dec_year = datetime.strptime(self.fiscal_date, '%Y-%m-%d').year
            for periode in periodes :
                duree =  (datetime.strptime(periode.date_end, '%Y-%m-%d') - datetime.strptime(periode.date_start, '%Y-%m-%d')).days
                if duree>88 and duree <92 and dec_year == datetime.strptime(periode.date_end, '%Y-%m-%d').year and dec_year == datetime.strptime(periode.date_start, '%Y-%m-%d').year:
                    ids.append(periode.id)
            return {'domain':{'date_range_id': [('id', 'in', ids)]}}
    @api.model
    def _get_domain(self):
        periodes = self.env['date.range'].search([])
        ids = []
        for periode in periodes :
            duree =  (datetime.strptime(periode.date_end, '%Y-%m-%d') - datetime.strptime(periode.date_start, '%Y-%m-%d')).days
            if duree>88 and duree <92:
                ids.append(periode.id)
        return [('id', 'in', ids)]
    
    @api.onchange('fiscal_date')
    def onchange_fiscal_date(self):
        if(self.fiscal_date):
            print self.fiscal_date
            date = str(datetime.strptime(self.fiscal_date, '%Y-%m-%d').year) + "-1-1"
            mydate = datetime.strptime(date, '%Y-%m-%d')
            self.fiscal_date = mydate
            
    fiscal_date = fields.Date(string="Annee fiscale")
    date_range_id = fields.Many2one('date.range', 'Periode', domain=lambda self: self._get_domain())
    
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
                  ('date_range_id.id','=',self.date_range_id.id),
                  ('fiscal_date','=',self.fiscal_date)]
        
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
    