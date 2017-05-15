from datetime import datetime
from openerp import models, fields, api
    
class Contrat(models.Model):
    _name = 'cmim.contrat'
    
    description = fields.Char('Description', required=True)
    collectivite_ids = fields.One2many('res.partner', 'contrat_id', string='Collectivites', domain=[('customer','=',True),('is_collectivite','=',True),('is_company','=',True)])
    contrat_line_ids = fields.Many2many('cmim.contrat.line','cmim_contrat_contrat_ligne_rel', 'contrat_id', 'contrat_ligne_id', string="Lignes de contrat", required=True)
    name = fields.Char('Nom', readonly=True)  
    notes = fields.Text('Notes')   
    
    @api.model
    def create(self, vals): 
        vals['name'] = self.env['ir.sequence'].next_by_code('cmim.contrat') 
        return super(Contrat, self).create(vals)
    
class LigneContrat(models.Model):
    _name = 'cmim.contrat.line'
    _order = 'regle_id_sequence'
    @api.multi
    def get_name(self): 
        for obj in self:
            obj.name = '%s: %s' %(obj.product_id.short_name, obj.regle_id.name) 
    name = fields.Char('Nom', compute="get_name")
    product_id = fields.Many2one('product.template', "Produit", required=True)
    regle_id = fields.Many2one('cmim.regle.calcul', 'Regle de calcul', required=True, domain=[('type', '=', 'base'),('reserved', '=', False), ('regle_tarif_id', '!=', None), ('regle_base_id', '!=', None)])
    regle_id_sequence = fields.Integer(related='regle_id.sequence', store=True)