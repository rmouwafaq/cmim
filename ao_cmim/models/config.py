# -*- coding: utf-8 -*-
import openerp
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, tools, api, _
from openerp.exceptions import UserError
from numpy.fft.info import depends

class TypeProduit(models.Model):
    _name = "cmim.product.type"
    name = fields.Char('Nom du type', required=True)
    short_name = fields.Char("code")
    
class Secteur(models.Model):
    _name = 'cmim.secteur'
    
    name = fields.Char('nom du secteur', reduired=True)
    plancher = fields.Float('Plancher du secteur')
    plafond = fields.Float('Plafond du secteur')

class ConstanteCalcul(models.Model):
    _name = 'cmim.constante'
    name = fields.Char('Nom ', required=True)
    valeur = fields.Char('Valeur ', required=True)
    
class Tarif(models.Model):
    _name = 'cmim.tarif'
    name = fields.Char('Nom', required=True)
    type = fields.Selection(selection=[('p', 'Taux'),
                                        ('f', 'Forfait')],
                                        required=True,
                                        default="p",
                                        string='Type de tarif')
    montant = fields.Float('Tarif')    
    import_flag = fields.Boolean('Par import', default=False)     
    
class RegleCalcul(models.Model):
    _name = "cmim.regle.calcul"
    _order = 'sequence, regle_base_id desc'
#     @api.multi
#     def get_name_type(self):
#         for obj in self:
#             if obj.tarif_id.type == 'f':
#                 obj.name ='%s pr %s' %(obj.tarif_id.montant,obj.type_assure)
#             else:
#                 obj.name="(%s)%s * %s " %(obj.type_assure, obj.base, obj.tarif_id.montant)
    @api.multi
    def unlink(self):
        if self.reserved:
            raise UserError(
                _(u"Impossible de supprimer les règles de calcul réservées au système"))
        else:
            return super(RegleCalcul, self).unlink()
           
    @api.multi
    def write(self, vals):
        if self.reserved:
            raise UserError(
                _(u"Impossible de modifier les règles de calcul réservées au système"))
        else:
            return super(RegleCalcul, self).write(vals)
            
    name = fields.Char('Nom')
    reserved = fields.Boolean('Reserved')
    sequence = fields.Integer('Sequence')
    notes = fields.Text('Notes')   
    secteur_ids = fields.Many2many('cmim.secteur', 'cmim_regle_calcul_secteur_rel', 'regle_id', 'secteur_id', string="Secteurs")
    type_assure = fields.Selection(selection=[  ('all', 'Tous'),
                                                ('active', 'Actifs'),
                                                ('invalide', 'Invalides'),
                                                ('retraite', 'Retraites')],
                                                string='Type Assure',
                                                default='all',
                                                required=True)

    tarif_id = fields.Many2one('cmim.tarif', string='Tarif', required=True)
    debut_applicabilite = fields.Date("Date debut de validite")
    fin_applicabilite = fields.Date("Date fin de validite")
    regle_base_id = fields.Many2one('cmim.regle.calcul', 'Base Calcul')
    
#     base = fields.Selection(selection=[ ('sal', 'Salaire'),
#                                         ('sal_pl', 'Salaire Plafonne par le secteur'),
#                                         ('tB', 'Tranche B'),
#                                         ('tA', 'Tranche A'),
#                                         ('pl_cnss', 'Plafond CNSS'),
#                                         ('srp', 'SRP')],
#                                            string='Base')
 
    
