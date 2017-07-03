# -*- coding: utf-8 -*-
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, exceptions, api, _
from openerp.exceptions import UserError
import test
class calcul_cotisation (models.TransientModel):
    _name = 'cmim.calcul.cotisation'
    _sql_constraints = [
        ('fiscal_date', "check(fiscal_date > 1999)", _("Valeur incorrecte pour l'an comptable !"))
    ]
    fiscal_date = fields.Integer(string=u"Année Comptable", required=True, default=datetime.now().year)
    date_range_id = fields.Many2one('date.range', u'Période', required=True)
    collectivite_ids = fields.Many2many('res.partner', 'calcul_cotisation_collectivite', 'calcul_id', 'partner_id', "Collectivites", domain="[('type_entite', '=', 'c'), ('contrat_id', '!=', None), ('customer','=',True),('is_company','=',True)]", required=True)

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
    def get_tarifs(self, collectivite_id):
        res = {}
        for param in collectivite_id.parametrage_ids:
            if param.regle_id.type != 'tabat':
                regle = param.regle_id.regle_tarif_id.id
                if not regle in res.keys():
                    res.update({regle : param.tarif_id})
        return res
    
    @api.multi
    def get_taux_abattement(self, declaration_id):
        mt = 100.0
        for param in declaration_id.collectivite_id.parametrage_ids:
            if param.regle_id.type== 'tabat' :
                if param.tarif_id.type == 'f':
                    raise exceptions.Warning(
                    _(u"L'abattement se base toujours sur des tarifs en pourcentage! Vérifiez le paramétrage des règles de calcul chez la collectivité %s" %declaration_id.collectivite_id.name))
            
                elif self.get_applicabilite(param.regle_id, declaration_id):
                        mt -= param.tarif_id.montant
        return mt/100
    
    def get_applicabilite(self, regle_id, declaration_id):
        test_applicabilite_statut = False
        test_applicabilite_secteur = True
        test_applicabilite_date = True
        if not regle_id.statut_ids:
            test_applicabilite_statut = True
        else:
            statuts = []
            if regle_id.type == 'trsc':
                rsc_ids = declaration_id.assure_id.search([('id_num_famille', '=', declaration_id.assure_id.id_num_famille),
                                                            ('type_entite', '=', 'rsc')])
                for rsc in rsc_ids:
                    statuts.extend(rsc.get_statut_in_periode(regle_id.statut_ids.ids, 
                                                            declaration_id.date_range_id.date_start, 
                                                            declaration_id.date_range_id.date_end))
            else: 
                statuts = declaration_id.assure_id.get_statut_in_periode(regle_id.statut_ids.ids, 
                                                            declaration_id.date_range_id.date_start, 
                                                            declaration_id.date_range_id.date_end)
            if len(statuts)>0:
                test_applicabilite_statut = True
        #############################################################
        if not regle_id.secteur_ids:
            test_applicabilite_secteur = True
        elif declaration_id.secteur_id.id in [x.id for x in regle_id.secteur_ids]:
            test_applicabilite_secteur = True
        else:
            test_applicabilite_secteur = False
        #############################################################
        if not regle_id.debut_applicabilite and not regle_id.fin_applicabilite:
            test_applicabilite_date = True
        elif regle_id.debut_applicabilite and declaration_id.date_range_id.date_start >= regle_id.debut_applicabilite:
            test_applicabilite_date = True
        elif regle_id.fin_applicabilite and regle_id.fin_applicabilite >= declaration_id.date_range_id.date_end:
            test_applicabilite_date = True
        else:
            test_applicabilite_date = False
        return test_applicabilite_statut and test_applicabilite_secteur and test_applicabilite_date
    
    def get_montant_cotisation_line(self, tarif_id, base):
        res = 0.0
        if tarif_id.type == 'f':
            res = tarif_id.montant
        else:
            res = (base * tarif_id.montant) / 100
        return res
    @api.multi
    def calcul_per_collectivite(self, declaration_id, contrat_line_ids, dict_tarifs):
        cotisation_line_list = []
        dict_bases = {}
        taux_abattement = self.get_taux_abattement(declaration_id)
        for contrat in contrat_line_ids:
            if self.get_applicabilite(contrat.regle_id, declaration_id):
                cotisation_line_dict = {'declaration_id': declaration_id.id,
                                        'name': contrat.product_id.short_name,
                                        'contrat_line_id' : contrat.id}
                
                selected_tarif_id = dict_tarifs.get(contrat.regle_id.regle_tarif_id.id)
                if not selected_tarif_id:
                    selected_tarif_id = contrat.regle_id.regle_tarif_id.default_tarif_id
                cotisation_line_dict['taux'] = selected_tarif_id.montant
                cotisation_line_dict['base'] = 1
                cotisation_line_dict['tarif_id'] = selected_tarif_id.id
                cotisation_line_dict['taux_abattement'] = taux_abattement if contrat.regle_id.applicabilite_abattement else 1
                if selected_tarif_id.type == 'p':
                    if contrat.regle_id.regle_base_id.code == 'SALPL':
                        if contrat.regle_id.regle_base_id.applicabilite_proratat == True:
                            cotisation_line_dict['base'] = declaration_id.p_base_calcul
                        else:
                            cotisation_line_dict['base'] = declaration_id.base_calcul
                    elif contrat.regle_id.regle_base_id.code == 'TA':
                        if contrat.regle_id.regle_base_id.applicabilite_proratat == True:
                            cotisation_line_dict['base'] = declaration_id.p_base_trancheA
                        else:
                            cotisation_line_dict['base'] = declaration_id.base_trancheA
                    elif contrat.regle_id.regle_base_id.code == 'TB':
                        if contrat.regle_id.regle_base_id.applicabilite_proratat == True:
                            cotisation_line_dict['base'] = declaration_id.p_base_trancheB
                        else:
                            cotisation_line_dict['base'] = declaration_id.base_trancheB
                            
                    elif contrat.regle_id.regle_base_id and contrat.regle_id.regle_base_id.id in dict_bases.keys():
                        cotisation_line_dict['base'] = dict_bases[contrat.regle_id.regle_base_id.id]
                    else:
                        cotisation_line_dict['base'] = 0
                        
                mt = self.get_montant_cotisation_line(selected_tarif_id, cotisation_line_dict['base'])
                cotisation_line_dict.update({'montant' : mt,
                                             'montant_abattu' : mt * cotisation_line_dict['taux_abattement']})
                if contrat.regle_id.type=='trsc' :
                    rsc_assure_ids = declaration_id.assure_id.get_rsc(contrat.regle_id, declaration_id)
                    cotisation_line_dict.update({'montant_abattu ' : mt * cotisation_line_dict['taux_abattement'] *  len(rsc_assure_ids),
                                                 'nb_rsc' : len(rsc_assure_ids)})
                if cotisation_line_dict['montant_abattu'] !=0:
                    cotisation_line_list.append((0, 0, cotisation_line_dict))
                    dict_bases.update({
                        contrat.regle_id.id : cotisation_line_dict['montant_abattu'] })
                    
        return cotisation_line_list
    
    @api.multi 
    def calcul_engine(self):
        cotisation_ids = []
        cotiation_to_create = []
        for col in self.collectivite_ids:
            if not self.can_calculate(col.id):
                raise exceptions.Warning(
                    _(u"vous avez validé des cotisations pour une ou plusieurs collectivités. \nImpossible de lancer le calcul pour les mêmes périodes"))
            else:
                cotisation_dict = { 'date_range_id': self.date_range_id.id,
                                    'fiscal_date': self.fiscal_date,
                                    'collectivite_id': col.id,
                                    'cotisation_assure_ids' : [],
                                    'name' : 'Cotisation Brouillon',
                                    }
                cotisation_dict.setdefault('cotisation_assure_ids', [])
                declaration_ids = self.env['cmim.declaration'].search([('collectivite_id.id', '=', col.id),
                                                                       ('date_range_id.id', '=', self.date_range_id.id),
                                                                       ('state', '=', 'valide')])
                dict_tarifs = self.get_tarifs(col)
                for declaration_id in declaration_ids:
                    res = self.calcul_per_collectivite(declaration_id, col.contrat_id.contrat_line_ids, dict_tarifs)
                    cotisation_dict['cotisation_assure_ids'].extend(res)
                cotiation_to_create.append(cotisation_dict)
        for c in cotiation_to_create:
            if c.get('cotisation_assure_ids')!= []:
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
