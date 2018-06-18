# -*- coding: utf-8 -*-
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, exceptions, api, _
from openerp.exceptions import UserError
import test
import logging
class calcul_cotisation (models.TransientModel):
    _name = 'cmim.calcul.cotisation'
    # _sql_constraints = [
    #     ('fiscal_date', "check(fiscal_date > 1999)", _("Valeur incorrecte pour l'an comptable !"))
    # ]
    # fiscal_date = fields.Integer(string=u"Année Comptable", required=True, default=datetime.now().year)
    date_range_id = fields.Many2one('date.range', u'Période',
                                    domain="[('type_id', '=', type_id), ('active', '=', True)]", required=True)
    type_id = fields.Many2one('date.range.type', u'Type de péride', domain="[('active', '=', True)]", required=True)
    collectivite_ids = fields.Many2many('res.partner', 'calcul_cotisation_collectivite', 'calcul_id', 'partner_id', "Collectivites", domain="[('type_entite', '=', 'c'), ('contrat_id', '!=', None), ('customer','=',True),('is_company','=',True)]", required=True)

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        if self.date_range_id:
            self.type_id = self.date_range_id.type_id.id
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

    @api.multi
    def can_calculate(self, collectivite_id):
        res = True
        if(self.env['cmim.cotisation'].search([('collectivite_id', '=', collectivite_id),
                                               ('state', '=', 'valide'),
                                               ('date_range_id.date_start', '>=', self.date_range_id.date_start),
                                               ('date_range_id.date_end', '<=', self.date_range_id.date_end)])):
            res = False
        draft_cotisation = self.env['cmim.cotisation'].search([('collectivite_id', '=', collectivite_id),
                                                               ('state', '=', 'draft'),
                                                               ('date_range_id.date_start', '>=', self.date_range_id.date_start),
                                                               ('date_range_id.date_end', '<=', self.date_range_id.date_end)])
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


    def get_statut_obsolete_xxxx(self, regle_id, declaration_id):
        # FIXME : function code to remove
        test_applicabilite_statut = False
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
        if len(statuts) > 0:
            test_applicabilite_statut = True
        return test_applicabilite_statut


    def get_statut_applicabilite(self, regle_id, declaration_id):

        statut_applicable = False
        statuts = declaration_id.assure_id.get_statut_in_periode(regle_id.statut_ids.ids,
                                                                 declaration_id.date_range_id.date_start,
                                                                 declaration_id.date_range_id.date_end)
        if len(statuts) > 0:
            statut_applicable = True

        return statut_applicable

    def get_applicabilite(self, regle_id, declaration_id):

        test_applicabilite_statut = False
        test_applicabilite_garantie = True
        test_applicabilite_secteur = True
        test_applicabilite_secteur_inverse = True
        test_applicabilite_date = True
        if not regle_id.statut_ids:
            test_applicabilite_statut = True
        else:
            test_applicabilite_statut = self.get_statut_applicabilite(regle_id, declaration_id)

        if not regle_id.secteur_ids:
            test_applicabilite_secteur = True
        elif declaration_id.secteur_id.id in regle_id.secteur_ids.ids:
            test_applicabilite_secteur = True
        else:
            test_applicabilite_secteur = False
        #############################################################
        if not regle_id.garantie_ids:
            test_applicabilite_garantie = True
        elif declaration_id.collectivite_id.garantie_id.id in regle_id.garantie_ids.ids:
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
        test_applicabilite_secteur_inverse = not test_applicabilite_secteur if regle_id.secteur_inverse else test_applicabilite_secteur
        return test_applicabilite_statut and test_applicabilite_secteur_inverse and test_applicabilite_date
    
    def get_montant_cotisation_line(self, tarif_id, base):
        res = 0.0
        if tarif_id.type == 'f':
            res = tarif_id.montant
        else:
            res = (base * tarif_id.montant) / 100
        return res

    def get_base_calcul(self, declaration_id ):
        cnss = self.env.ref('ao_cmim.cte_calcul_cnss')
        srp = self.env.ref('ao_cmim.cte_calcul_srp')
        result = {}
        if cnss and srp:
            prorata_plafond = float(declaration_id.nb_jour_prorata/ float(declaration_id.date_range_id.type_id.nb_days))
            #proratat = float(declaration_id.nb_jour / float(declaration_id.date_range_id.type_id.nb_days))
            proratat = 1
            if declaration_id.nb_jour_prorata>0:
                proratat = float(declaration_id.nb_jour / float(declaration_id.nb_jour_prorata))
            p_salaire = declaration_id.salaire * proratat
            plancher, plafond= 0.0, 0.0
            val_cnss, val_srp = 0.0, 0.0
            if declaration_id.date_range_id.type_id.id == self.env.ref('ao_cmim.data_range_type_trimestriel').id:
                plancher, plafond = declaration_id.secteur_id.plancher*prorata_plafond, declaration_id.secteur_id.plafond*prorata_plafond
                val_cnss, val_srp = cnss.valeur*prorata_plafond, srp.valeur*prorata_plafond
            elif declaration_id.date_range_id.type_id.id == self.env.ref('ao_cmim.data_range_type_mensuel').id:
                plancher, plafond = declaration_id.secteur_id.plancher_mensuel, declaration_id.secteur_id.plafond_mensuel
                val_cnss, val_srp = cnss.val_mensuelle, srp.val_mensuelle
            print plafond, plancher
            if not declaration_id.secteur_id.is_complementary:
                base_calcul = min(float(plafond), max(float(plancher), float(declaration_id.salaire)))
                p_base_calcul = min(float(plafond * proratat), max(float(plancher) * proratat, float(declaration_id.salaire)))
                base_trancheA = min(float(val_cnss), float(declaration_id.salaire))
                p_base_trancheA = min(float(val_cnss) * proratat, float(declaration_id.salaire))

                diff = 0.0
                if declaration_id.salaire > base_trancheA:
                    diff = declaration_id.salaire - base_trancheA
                diff_srp = float(val_srp) - base_trancheA
                base_trancheB = min(float(diff_srp), float(diff))

                diff = 0.0
                if(declaration_id.salaire > p_base_trancheA):
                    diff = declaration_id.salaire - p_base_trancheA
                diff_srp = float(val_srp) - p_base_trancheA
                p_base_trancheB = min(diff_srp * proratat, float(diff))
            else:
                base_calcul = declaration_id.salaire
                base_trancheA = declaration_id.salaire
                base_trancheB = declaration_id.salaire
                p_base_calcul = p_salaire
                p_base_trancheA = p_salaire
                p_base_trancheB = p_salaire
        else:
            raise osv.except_osv(_('Error!'), _(u"Veuillez vérifier la configuration des constantes de calcul" ))
        result.update({'base_calcul': base_calcul,
                       'base_trancheA': base_trancheA,
                       'base_trancheB': base_trancheB,
                       'p_base_calcul': p_base_calcul,
                       'p_base_trancheA': p_base_trancheA,
                       'p_base_trancheB': p_base_trancheB,
                       'proratat': proratat,
                       'p_salaire': p_salaire,
                       })
        return result

    @api.multi
    def calcul_per_collectivite(self, declaration_id, contrat_line_ids, dict_tarifs):
        cotisation_line_list = []
        dict_bases = {}
        base_calcul = self.get_base_calcul(declaration_id)
        taux_abattement = self.get_taux_abattement(declaration_id)
        for contrat in contrat_line_ids:

            if self.get_applicabilite(contrat.regle_id, declaration_id):
                selected_tarif_id = dict_tarifs.get(contrat.regle_id.regle_tarif_id.id)
                if not selected_tarif_id:
                    selected_tarif_id = contrat.regle_id.regle_tarif_id.default_tarif_id

                cotisation_line_dict = {'declaration_id': declaration_id.id,
                                        'name': contrat.product_id.short_name,
                                        'contrat_line_id' : contrat.id,
                                        'taux': selected_tarif_id.montant,
                                        'base': 1,
                                        'tarif_id': selected_tarif_id.id,
                                        'taux_abattement': taux_abattement if contrat.regle_id.applicabilite_abattement else 1,
                                        'proratat': base_calcul.get('proratat') if contrat.regle_id.regle_base_id.applicabilite_proratat else 1.0
                                        }
                
                if selected_tarif_id.type == 'p':
                    if contrat.regle_id.regle_base_id.code == 'SALPL':
                        if contrat.regle_id.regle_base_id.applicabilite_proratat:
                            cotisation_line_dict['base'] = base_calcul.get('p_base_calcul')
                        else:
                            cotisation_line_dict['base'] = base_calcul.get('base_calcul')
                    elif contrat.regle_id.regle_base_id.code == 'TA':
                        if contrat.regle_id.regle_base_id.applicabilite_proratat:
                            cotisation_line_dict['base'] = base_calcul.get('p_base_trancheA')
                        else:
                            cotisation_line_dict['base'] = base_calcul.get('base_trancheA')
                    elif contrat.regle_id.regle_base_id.code == 'TB':
                        if contrat.regle_id.regle_base_id.applicabilite_proratat:
                            cotisation_line_dict['base'] = base_calcul.get('p_base_trancheB')
                        else:
                            cotisation_line_dict['base'] = base_calcul.get('base_trancheB')
                    elif contrat.regle_id.regle_base_id.code == 'SALBRUT':
                        if contrat.regle_id.regle_base_id.applicabilite_proratat:
                            cotisation_line_dict['base'] = base_calcul.get('p_salaire')
                        else:
                            cotisation_line_dict['base'] = declaration_id.salaire
                    elif contrat.regle_id.regle_base_id and contrat.regle_id.regle_base_id.id in dict_bases.keys():
                        cotisation_line_dict['base'] = dict_bases[contrat.regle_id.regle_base_id.id]
                    else:
                        cotisation_line_dict['base'] = 0
                        
                mt = self.get_montant_cotisation_line(selected_tarif_id, cotisation_line_dict['base'])
                cotisation_line_dict.update({'montant': mt,
                                             'montant_abattu' : mt * cotisation_line_dict['taux_abattement']})

                if contrat.regle_id.type == 'trsc':
                    logging.info('Contrat regle >>>>>: %s %s ', contrat.regle_id.type, contrat.regle_id.name)
                    rsc_assure_ids = declaration_id.assure_id.get_rsc(contrat.regle_id, declaration_id)
                    cotisation_line_dict.update({'montant_abattu ' : mt * cotisation_line_dict['taux_abattement'] *  len(rsc_assure_ids),
                                                 'nb_rsc' : len(rsc_assure_ids)})
                    logging.info('regle de type trsc : %s %s %s ', contrat.regle_id.name,mt,len(rsc_assure_ids))
                if cotisation_line_dict['montant_abattu'] !=0:
                    cotisation_line_list.append((0, 0, cotisation_line_dict))
                    dict_bases.update({
                        contrat.regle_id.id : cotisation_line_dict['montant_abattu'] })
                    
        return cotisation_line_list
    
    @api.multi 
    def calcul_engine(self):

        # Moteur de calcul des cotisations CMIM
        cotisation_ids = []
        cotiation_to_create = []
        for col in self.collectivite_ids:
            # Verifier si le calcul peut etre lance pour cette collectivite
            if not self.can_calculate(col.id):
                raise exceptions.Warning(
                    _(u"Une ou plusieurs Cotisations sont validées pour cette collectivité %s. \nImpossible de relancer le calcul pour la même période !!!." %col.name))
            else:
                cotisation_dict = {'date_range_id': self.date_range_id.id,
                                   'type_id': self.type_id.id,
                                   'collectivite_id': col.id,
                                   'cotisation_assure_ids' : [],
                                   'name': 'Cotisation Brouillon',
                                    }
                cotisation_dict.setdefault('cotisation_assure_ids', [])
                declaration_ids = self.env['cmim.declaration'].search([('collectivite_id.id', '=', col.id),
                                                                       ('date_range_id.date_start', '>=', self.date_range_id.date_start),
                                                                       ('date_range_id.date_end', '<=', self.date_range_id.date_end),
                                                                       ('cotisation_id', '=', None),
                                                                       ('state', '=', 'valide')])

                # Rechercher les tarifs spécifiques a chaque collectivite
                dict_tarifs = self.get_tarifs(col)

                for declaration_id in declaration_ids:
                    # for i in range(len(declaration_ids)):
                    res = self.calcul_per_collectivite(declaration_id, col.contrat_id.contrat_line_ids, dict_tarifs)
                    cotisation_dict['cotisation_assure_ids'].extend(res)
                    # if i == 2:
                    #     break
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



    #################### Code Obsolete ################################
    # @api.multi
    # def create_cotisation_product_lines(self, cotisation_obj):
    #     cotisation_assure_lines = self.env['cmim.cotisation.assure.line'].search([('cotisation_id.id', '=', cotisation_obj.id)])
    #     cotisation_product_obj = self.env['cmim.cotisation.product']
    #     for line in cotisation_assure_lines:
    #         cotisation_product_obj = cotisation_product_obj.search([('cotisation_id.id', '=', cotisation_obj.id),
    #                                                                 ('product_id.id', '=', line.product_id.id),
    #                                                                 ('code', '=', line.code)])
    #
    #         if(cotisation_product_obj):
    #             cotisation_product_obj.write({'montant': cotisation_product_obj.montant + line.montant})
    #         else:
    #             cotisation_product_obj = cotisation_product_obj.create({'cotisation_id': cotisation_obj.id,
    #                                                                     'product_id': line.product_id.id,
    #                                                                     'code': line.code,
    #                                                                     'montant' : line.montant
    #                                                                     })
    #             cotisation_obj.write({'cotisation_product_ids': [(4, cotisation_product_obj.id)]})
    #     return True
