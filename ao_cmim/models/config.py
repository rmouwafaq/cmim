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
    regime = fields.Selection(string=u'Régime', selection=[('n', u'Normal'),('rsc', u'RSC') ], default='n', required=True)
 
class Garantie(models.Model):
    _name = "cmim.garantie"
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
    is_complementary = fields.Boolean('Est Complémentaire', default=False)
    plancher = fields.Float('Plancher Trimestriel',  compute=lambda self:self._get_val_trimestrielle())
    plafond = fields.Float('Plafond Trimestriel',  compute=lambda self:self._get_val_trimestrielle())
    plancher_mensuel = fields.Float('Plancher Mensuel')
    plafond_mensuel = fields.Float('Plafond Mensuel')
    garantie_ids = fields.Many2many('cmim.garantie','cmim_secteur_garantie_rel', 'secteur_id', 'garantie_id', 
                                        string="Garanties permises", required=True)
