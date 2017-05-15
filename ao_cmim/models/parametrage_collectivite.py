# -*- coding: utf-8 -*-
import openerp
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, tools, api, _
from openerp.exceptions import UserError
 
class ParametrageCollectivite(models.Model):

    _name = "cmim.parametrage.collectivite"
    
    @api.onchange('regle_id')
    def onchange_regle_id(self):
        if self.regle_id:
            self.name= self.regle_id.name
    
    name = fields.Char('Nom', required=True)
    regle_id = fields.Many2one('cmim.regle.calcul', string=u"Règle de Tarif", domain=[('reserved', '=', False),('regle_tarif_id', '=', None), ('regle_base_id', '=', None)], required=True)
    tarif_id = fields.Many2one('cmim.tarif', u'Tarif', required=True)
    collectivite_id = fields.Many2one('res.partner', u'Collectivité')
    _sql_constraints = [
        ('param_uniq', 'unique(regle_id, tarif_id, collectivite_id)', 'Un seul tarif peut être définit par règle par collectivité'),
    ]