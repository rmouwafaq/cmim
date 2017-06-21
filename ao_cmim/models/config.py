# -*- coding: utf-8 -*-
import openerp
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, tools, api, _
from openerp.exceptions import UserError
 
class StatutAssure(models.Model):
    _name = "cmim.statut.assure"
    name = fields.Char('Nom', required=True)
    code = fields.Char("code", required=True)
    
class Secteur(models.Model):
    _name = 'cmim.secteur'
    
    name = fields.Char('nom du secteur', reduired=True)
    @api.multi
    def _get_val_trimestrielle(self):
        for obj in self:
            obj.plancher = obj.plancher_mensuel * 3
            obj.plafond = obj.plafond_mensuel * 3
            
    plancher = fields.Float('Plancher Trimestrielle',  compute=_get_val_trimestrielle)
    plafond = fields.Float('Plafond Trimestrielle',  compute=_get_val_trimestrielle)
    plancher_mensuel = fields.Float('Plancher Mensuel', required=True)
    plafond_mensuel = fields.Float('Plafond Mensuel', required=True)

class ConstanteCalcul(models.Model):
    _name = 'cmim.constante'
    @api.multi
    def unlink(self):
        if self.reserved:
            raise UserError(
                _(u"Impossible de supprimer des constantes de calcul réservées au système"))
        else:
            return super(RegleCalcul, self).unlink()
        
    @api.multi
    def _get_val_trimestrielle(self):
        for obj in self:
            obj.valeur = obj.val_mensuelle*3
            
    reserved = fields.Boolean(u'réservé au système', default=False)
    name = fields.Char('Nom ', required=True)
    valeur = fields.Float('Valeur ', compute=_get_val_trimestrielle)
    val_mensuelle = fields.Float('Valeur Mensuelle', required=True)
    
class Tarif(models.Model):
    _name = 'cmim.tarif'
    name = fields.Char('Nom', required=True)
    type = fields.Selection(selection=[('p', 'Taux'),
                                        ('f', 'Forfait')],
                                        required=True,
                                        default="p",
                                        string='Type de tarif')
    montant = fields.Float('Tarif', required=True)    
    
class RegleCalcul(models.Model):
    _name = "cmim.regle.calcul"
    _order = 'reserved desc, type desc, sequence, regle_base_id desc'
    @api.multi
    def unlink(self):
        for obj in self:
            if obj.reserved:
                raise UserError(
                    _(u"Impossible de supprimer les règles de calcul réservées au système"))
            else:
                return super(RegleCalcul, self).unlink()
    @api.onchange('type')
    def onchange_type(self):
        if self.type and self.type == 'taux':
            self.applicabilite_proratat = False
            
    name = fields.Char('Nom', required=True)
    reserved = fields.Boolean('Reserved')
    sequence = fields.Integer('Sequence')
    code = fields.Char('Code')
    notes = fields.Text('Notes')   
    secteur_ids = fields.Many2many('cmim.secteur', 'cmim_regle_calcul_secteur_rel', 'regle_id', 'secteur_id', string="Secteurs")
    statut_ids = fields.Many2many('cmim.statut.assure', 'regle_calcul_statut_rel', 'regle_id', 'statut_id',  string=u"Type de positions")
    default_tarif_id = fields.Many2one('cmim.tarif', string=u'Tarif par défaut',  ondelete = 'restrict')
    debut_applicabilite = fields.Date(u"Date début de validité")
    fin_applicabilite = fields.Date(u"Date fin de validité")
    regle_base_id = fields.Many2one('cmim.regle.calcul', 'Base Calcul', domain=[('type', '!=', 'taux')], ondelete = 'restrict')
    regle_tarif_id = fields.Many2one('cmim.regle.calcul', 'Taux Calcul', domain=[('type', '=', 'taux')], ondelete = 'restrict')
    type = fields.Selection(selection=[('taux', 'Règle Tarif'),
                                        ('base', 'Règle Base')], 
                                        default="base", string='Type de règle',
                                        help=u"Les règles de calcul intermédaires servent à définir les bons tarifs tandis que les règles de calcul contractuelles définissent les bases de calul , le tarif pris en compte lors du calcul est soit le tarif associé à la règle intermédiaire dans le paramétrage de la collectivité, soit le tarif par défaut définit dans la règle de calcul contractuelle.")
    applicabilite_proratat = fields.Boolean(u'Applicabilité prorata', default=True)

