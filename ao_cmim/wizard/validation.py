# -*- coding: utf-8 -*-
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields,exceptions, api, _
from openerp.exceptions import UserError

class validation_cotisation (models.TransientModel):
    _name = 'cmim.validation.cotisation'
    # _sql_constraints = [
    #     ('fiscal_date', "check(fiscal_date > 1999)", _(u"Valeur incorrecte pour l'année comptable !"))
    # ]
    # @api.onchange('fiscal_date')
    # def onchange_fiscal_date(self):
    #     if(self.fiscal_date):
    #         periodes = self.env['date.range'].search([])
    #         ids = []
    #         for periode in periodes :
    #             duree = (datetime.strptime(periode.date_end, '%Y-%m-%d') - datetime.strptime(periode.date_start, '%Y-%m-%d')).days
    #             if duree > 88 and duree < 92 and self.fiscal_date == datetime.strptime(periode.date_end, '%Y-%m-%d').year and self.fiscal_date == datetime.strptime(periode.date_start, '%Y-%m-%d').year:
    #                 ids.append(periode.id)
    #         return {'domain':{'date_range_id': [('id', 'in', ids)]}}
    #
    # fiscal_date = fields.Integer(string=u"Année Comptable", required=True, default= datetime.now().year )
    date_range_id = fields.Many2one('date.range', u'Période',
                                    domain="[('type_id', '=', type_id), ('active', '=', True)]", required=True)
    type_id = fields.Many2one('date.range.type', u'Type de péride', domain="[('active', '=', True)]", required=True)
    collectivite_ids = fields.Many2many('res.partner','validation_collectivite', 'validation_id', 'partner_id', u"Collectivités", domain = "[('customer','=',True),('is_company','=',True)]")
    cotisation_ids = fields.Many2many('cmim.cotisation','validation_cotisation', 'validation_id', 'cotisaion_id', "Cotisations")
    state = fields.Selection(selection=[('init', 'Init'), ('select', 'Select'), ('validate', 'Validate')],
                             string='Etat', default='init', required=True)
    
    @api.multi
    def suivant_act(self, vals):
        if not self.collectivite_ids:
            raise exceptions.Warning(_(u"Veuillez séléctionner les collectivités"))

        domain = [('collectivite_id.id', 'in', self.collectivite_ids.ids), ('state', '=', 'draft'),
                  ('date_range_id.id', '=', self.date_range_id.id),
                  ('type_id', '=', self.type_id.id)]
        
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
        if len(self.cotisation_ids) != 0:
            for cotisation in self.cotisation_ids:
                cotisation.action_validate()

            self.state="validate"
            view_id = self.env.ref('ao_cmim.cotisation_tree_view').id
            return {'name' : u'Cotisations validées',
                    'views' : [(view_id, 'tree'),(False, 'form')],
                    'type': 'ir.actions.act_window',
                    'res_model': 'cmim.cotisation',
                    'view_mode': 'tree,form',
                    'res_id': self.id,
                    'view_id': 'ao_cmim.cotisation_tree_view',
                    'domain':[('id', 'in', [x.id for x in self.cotisation_ids])],
                    'target':'self',
                }
        else:
            return True
            
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
    