
import openerp
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, tools, api
from numpy.fft.info import depends

class TypeProduit(models.Model):
    _name="cmim.product.type"
    name = fields.Char('Nom du type', required=True )
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
    _name='cmim.tarif'
    name = fields.Char('Nom', required = True)
    type = fields.Selection(selection= [('p', 'Taux'),
                                        ('f', 'Forfait')],
                                        required=True,
                                        default = "p",
                                        string='Type de tarif')
    montant = fields.Float('Tarif')    
    import_flag = fields.Boolean('Par import', default=False )     
    
class RegleCalcul(models.Model):
    _name="cmim.regle.calcul"
    @api.multi
    def get_name_type(self):
        for obj in self:
            if obj.tarif_id.type == 'f':
                obj.name ='%s pr %s' %(obj.tarif_id.montant,obj.type_assure)
            else:
                obj.name="%s * %s " %(obj.base, obj.tarif_id.montant)
            obj.type_regle = "mal_retraite"
            if obj.base_2 and obj.tarif_inc_inv_id:
                obj.name = obj.name + ' + %s * %s' %(obj.base2, obj.tarif_inc_inv_id.montant)
                obj.type_regle = "prevoyance"
    name = fields.Char('Regle de calcul', compute="get_name_type")
    type_regle = fields.Selection(selection=[('prevoyance', 'Prevoyance'),
                                          ('mal_retraite', 'Mal/ Retraire')],
                                           default='mal_retraite',
                                           string='Type Produit')
    secteur_id = fields.Many2one('cmim.secteur', string="Secteur") 
    date_range_id = fields.Many2one('date.range', 'Periode')
    type_assure = fields.Selection(selection=[('active', 'Actif'),
                                          ('invalide', 'Invalide'),
                                          ('retraite', 'Retraite')],
                                           string='Type Assure')
    base = fields.Selection(selection=[('salaire', 'Salaire Plafonne par le secteur'),
                                          ('trancheA', 'Tranche A'),
                                          ('trancheAB', 'Tranche B')],
                                           string='Base')
    tarif_id = fields.Many2one('cmim.tarif',  string='Tarif', required=True)
    tarif1_type = fields.Selection(selection= [('p', 'Taux'),
                                        ('f', 'Forfait')],
                                        related='tarif_id.type')
    base_2 = fields.Selection(selection=[('salaire', 'Salaire Plafonne par le secteur'),
                                          ('trancheA', 'Tranche A'),
                                          ('trancheAB', 'Tranche B')],
                                           string='Base 2')
    tarif_inc_inv_id = fields.Many2one('cmim.tarif',  string='Tarif inv_inc', domain=[('type', '=', 'p')])
    
    