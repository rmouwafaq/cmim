from datetime import datetime
from openerp import models, fields, api
    
class Contrat(models.Model):
    _name = 'cmim.contrat'
    
    collectivite_ids = fields.One2many('res.partner', 'contrat_id', string='Collectivites',  domain=[('customer','=',True),('is_company','=',True)])
    contrat_line_ids = fields.Many2many('cmim.contrat.line','cmim_contrat_contrat_ligne_rel', 'contrat_id', 'contrat_ligne_id', string="Lignes de contrat", required=True)
    name = fields.Char('Nom', readonly=True)  
    notes = fields.Text('Notes')   
    @api.model
    def create(self, vals): 
        vals['name'] = self.env['ir.sequence'].next_by_code('cmim.contrat') 
        return super(Contrat, self).create(vals)
class LigneContrat(models.Model):
    _name = 'cmim.contrat.line'

    @api.multi
    def get_name(self): 
        for obj in self:
            obj.name = '%s: %s' %(obj.product_id.short_name, obj.regle_id.name) 
    name = fields.Char('Nom', compute="get_name")
    product_id = fields.Many2one('product.template', "Produit", required=True)
    code = fields.Integer("Code Produit")
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

