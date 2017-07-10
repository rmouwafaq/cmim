# -*- coding: utf-8 -*-
from datetime import datetime
from openerp import models, exceptions, fields, api, _
    
class Contrat(models.Model):
    _name = 'cmim.contrat'
    
    description = fields.Char('Description', required=True)
    collectivite_ids = fields.One2many('res.partner', 'contrat_id', string=u'Collectivités', domain=[('customer','=',True),('type_entite','=','c'),('is_company','=',True)])
    contrat_line_ids = fields.Many2many('cmim.contrat.line','cmim_contrat_contrat_ligne_rel', 'contrat_id', 'contrat_ligne_id', 
                                        string="Lignes de contrat", required=True)
    name = fields.Char('Nom', readonly=True)  
    notes = fields.Text('Notes')   
    
    @api.model
    def name_get(self):
        result = []
        for obj in self:
            result.append((obj.id, obj.description))
        return result
    def test_arborescence(self, val_ids):
        line_ids = val_ids[0][2] if len(val_ids) >0 else []
        lines = self.env['cmim.contrat.line'].browse(line_ids)
        base_line_ids = [x.regle_id.id for x in lines]
        res = True
        for line in lines:
            if not line.regle_id.regle_base_id.reserved and line.regle_id.regle_base_id.id not in base_line_ids:
                res=False 
                break
        return res
    @api.model
    def create(self, vals): 
        if not self.test_arborescence(vals.get('contrat_line_ids', [])):
            raise exceptions.Warning(
                _(u"Vérifiez l'arborescence des règles de calcul!"))
        
        vals['name'] = self.env['ir.sequence'].next_by_code('cmim.contrat') 
        return super(Contrat, self).create(vals)
    
    @api.multi
    def write(self, vals):
        val_ids = vals.get('contrat_line_ids', [])
        if not self.test_arborescence(vals.get('contrat_line_ids', [])):
            raise exceptions.Warning(
                _(u"Vérifiez l'arborescence des règles de calcul!"))
        return super(Contrat, self).write(vals)
    

class LigneContrat(models.Model):
    _name = 'cmim.contrat.line'
    _order = 'regle_id_type asc'
    @api.multi
    def get_name(self): 
        for obj in self:
            obj.name = '%s: %s' %(obj.product_id.short_name, obj.regle_id.name) 
    name = fields.Char('Nom', compute="get_name")
    product_id = fields.Many2one('product.template', "Produit", required=True)
    regle_id = fields.Many2one('cmim.regle.calcul', u'Règle de calcul', required=True, domain="[('type', 'in', ['tbase', 'trsc']),('reserved', '=', False), ('regle_tarif_id', '!=', None), ('regle_base_id', '!=', None)]")
    regle_id_type = fields.Selection(related='regle_id.type', store=True)
    regle_id_sequence = fields.Integer(related='regle_id.sequence', store=True)
