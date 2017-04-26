# -*- coding: utf-8 -*-
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, exceptions, api, _
from openerp.exceptions import UserError
class calcul_cotisation (models.TransientModel):
    _name = 'cmim.calcul.cotisation'
    _sql_constraints = [
        ('fiscal_date', "check(fiscal_date > 1999)", _("Valeur incorrecte pour l'an comptable !"))
    ]
        
    @api.onchange('fiscal_date')
    def onchange_fiscal_date(self):
        if(self.fiscal_date):
            periodes = self.env['date.range'].search([])
            ids = []
            for periode in periodes :
                duree = (datetime.strptime(periode.date_end, '%Y-%m-%d') - datetime.strptime(periode.date_start, '%Y-%m-%d')).days
                if duree > 88 and duree < 92 and self.fiscal_date == datetime.strptime(periode.date_end, '%Y-%m-%d').year and self.fiscal_date == datetime.strptime(periode.date_start, '%Y-%m-%d').year:
                    ids.append(periode.id)
            return {'domain':{'date_range_id': [('id', 'in', ids)]}}
    
    fiscal_date = fields.Integer(string="Annee Comptable", required=True, default= datetime.now().year )
    date_range_id = fields.Many2one('date.range', 'Periode', required=True)
    collectivite_ids = fields.Many2many('res.partner', 'calcul_cotisation_collectivite', 'calcul_id', 'partner_id', "Collectivites", domain="[('customer','=',True),('is_company','=',True)]", required=True)
    
    
    @api.multi
    def create_cotisation_product_lines(self, cotisation_obj):
        cotisation_assure_lines = self.env['cmim.cotisation.assure.line'].search([('cotisation_id.id', '=', cotisation_obj.id)])
        cotisation_product_obj = self.env['cmim.cotisation.product']
        for line in cotisation_assure_lines:
            cotisation_product_obj = cotisation_product_obj.search([('cotisation_id.id', '=', cotisation_obj.id),
                                                                    ('product_id.id', '=', line.product_id.id),
                                                                    ('code', '=', line.code)])
            
            if(cotisation_product_obj):
                cotisation_product_obj.write({'montant': cotisation_product_obj.montant + line.montant})
            else:
                cotisation_product_obj = cotisation_product_obj.create({'cotisation_id': cotisation_obj.id,
                                                                        'product_id': line.product_id.id,
                                                                        'code': line.code,
                                                                        'montant' : line.montant
                                                                        })
                cotisation_obj.write({'cotisation_product_ids': [(4, cotisation_product_obj.id)]})
        return True
    
    
    @api.multi
    def can_calculate(self, collectivite_id):
        res = True
        if(self.env['cmim.cotisation'].search([('collectivite_id', '=', collectivite_id),
                                               ('state', '=', 'valide'),
                                               ('date_range_id.id', '=', self.date_range_id.id)])):
            res = False
        draft_cotisation = self.env['cmim.cotisation'].search([('collectivite_id', '=', collectivite_id),
                                               ('state', '=', 'draft'),
                                               ('date_range_id.id', '=', self.date_range_id.id)])
        if draft_cotisation:
            draft_cotisation.unlink()
        return res
        
    
    @api.multi
    def calcul_per_collectivite(self, declaration_id, contrat_line_ids):
        cotisation_line_list = []
        for contrat in contrat_line_ids:
            #test sur applicabilite regle
#             if (contrat.regle_id.type_assure == 'all' or contrat.regle_id.type_assure == declaration_id.assure_id.statut)\
#                 and not contrat.regle_id.secteur_id or contrat.regle_id.secteur_id.id == declaration_id.assure_id.collectivite_id.secteur_id.id\
#                 and datetime.datetime.strptime(valid_date, '%Y-%m-%d').date()>= datetime.datetime.now().date() :
            if 1==1:
                cotisation_line_dict = {'declaration_id': declaration_id.id,
                                        'name': contrat.product_id.short_name,
                                        'contrat_line_id' : contrat.id}
                
                cotisation_line_dict['taux'] = contrat.regle_id.tarif_id.montant
                cotisation_line_dict['base'] = -1
                if contrat.regle_id.tarif_id.type == 'p':
                    if contrat.regle_id.regle_base_id.code == 'SALPL':
                        cotisation_line_dict['base'] = declaration_id.base_calcul
                    elif contrat.regle_id.regle_base_id.code == 'TA':
                        cotisation_line_dict['base'] = declaration_id.base_trancheA
                    elif contrat.regle_id.regle_base_id.code == 'TB':
                        cotisation_line_dict['base'] = declaration_id.base_trancheB
                    elif contrat.regle_id.regle_base_id:
                        cotisation_line_dict['base'] = self.env['cmim.cotisation.assure.line'].search([('regle_id', '=', contrat.regle_id.regle_base_id.id)]).montant
                    
                
                cotisation_line_list.append((0, 0, cotisation_line_dict))
        return cotisation_line_list
    
    
    @api.multi 
    def calcul_engine(self):
        cotisation_ids = []
        cotiation_to_create=[]
        for col in self.collectivite_ids:
            if not self.can_calculate(col.id):
                raise exceptions.Warning(
                    _("vous avez valide des cotisations pour une ou plusieurs collectivites. \nImpossible de lancer le calcul pour les memes periodes"))
            else:
                cotisation_dict = { 'date_range_id': self.date_range_id.id,
                                    'fiscal_date': self.fiscal_date,
                                    'collectivite_id': col.id,
                                    'cotisation_assure_ids' : [],
                                    'name' : 'Cotisation Brouillon',
                                    }
                cotisation_dict.setdefault('cotisation_assure_ids', [])
                declaration_ids = self.env['cmim.declaration'].search([('collectivite_id.id', '=', col.id), 
                                                                       ('date_range_id.id', '=', self.date_range_id.id)])
                for declaration_id in declaration_ids:
                    
                    cotisation_dict['cotisation_assure_ids'].extend(self.calcul_per_collectivite(declaration_id, col.contrat_id.contrat_line_ids))
                    
                cotiation_to_create.append(cotisation_dict)
        for c in cotiation_to_create:
            cotisation_ids.append(self.env['cmim.cotisation'].create(c).id)
        view_id = self.env.ref('ao_cmim.cotisation_tree_view').id
        if len(cotisation_ids) > 0:
            return{ 
                    'res_model':'cmim.cotisation',
                    'type': 'ir.actions.act_window',
                    'res_id': self.id,
                    'view_mode':'tree,form',
                    'views' : [(view_id, 'tree'), (False, 'form')],
                    'view_id': 'ao_cmim.cotisation_tree_view',
                    'domain':[('id', 'in', cotisation_ids)],
                    'target':'self',
                    }
        else:
            return True
            
