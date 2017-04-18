from datetime import datetime
from openerp import models, fields, api
    
class Contrat(models.Model):
    _name = 'cmim.contrat'
    
    collectivite_id = fields.One2many('res.partner', 'contrat_id', string='Collectivite')
    contrat_ids = fields.Many2many('cmim.contrat.line','cmim_contrat_contrat_ligne_rel', 'contrat_id', 'contrat_ligne_id', string="Lignes de contrat", required=True)
    name = fields.Char('Nom')  
    notes = fields.Text('Notes')   
    @api.model
    def create(self, vals): 
        if vals.get('name','/')=='/':
            vals['name'] = self.env['ir.sequence'].get(cr, uid, 'cmim.contrat') 
        return super(Contrat, self).create(vals)
class LigneContrat(models.Model):
    _name = 'cmim.contrat.line'
    
    @api.model
    def create(self, vals): 
        if vals.get('name','/')=='/':
            vals['name'] =  '%s: %s' %(obj.product_id.short_name, obj.regle_id.name) 
        return super(Contrat, self).create(vals)
    name = fields.Char('Nom', required=True)
    product_id = fields.Many2one('product.template', "Produit", required=True)
    code = fields.Integer("Code Produit")
    type_produit = fields.Selection(selection=[('prevoyance', 'Prevoyance'),
                                          ('mal_retraite', 'Mal/ Retraire')],
                                           required=True,
                                           string='Type Produit')
    regle_id = fields.Many2one('cmim.regle.calcul', 'Regle de calcul', required=True)
# class contrat(models.Model):
#     _name = 'cmim.contrat'
#     
#     import_flag = fields.Boolean('Par import', default=False)      
#     name = fields.Char('Nom du contrat')
#     collectivite_id = fields.Many2one('res.partner', string='Collectivite', required=True,  ondelete='cascade')
#     product_id = fields.Many2one('product.template', "Produit", required=True)
#     code = fields.Integer("Code Produit")
#     type_product_id = fields.Many2one("cmim.product.type", string='Type de produit', )
#     type_product_name= fields.Char(string="Type de produit" ,related='type_product_id.short_name', store=True)
#     
#     secteur_id = fields.Many2one('cmim.secteur',
#         string='Secteur',
#         related='collectivite_id.secteur_id', store=True
#     )
#     tarif_id = fields.Many2one('cmim.tarif',  string='Tarif')
#     tarif_inc_deces_id = fields.Many2one('cmim.tarif',  string='Tarif Inc_Deces')
#     tarif_inv_id = fields.Many2one('cmim.tarif',  string ='Tarif Inv')
# 
#         
#     def calcul_cotisation(self):
#         return True 

