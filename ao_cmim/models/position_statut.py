# -*- coding: utf-8 -*-
from datetime import datetime
from openerp import models, fields, api

class ProductCMIM(models.Model):
    _name = 'cmim.position.statut'


    statut_id = fields.Many2one('cmim.statut.assure', required=True, string='Statut', domain = lambda self: self._get_statut_domain())
    date_debut_appl = fields.Date(string=u"Début applicabilité", required=True)
    date_fin_appl = fields.Date(string=u"Fin applicabilité", required=True)
    assure_id = fields.Many2one('res.partner', string=u'Assuré')
    
    def _get_statut_domain(self):
        return [('regime', '=', 'rsc')] if self._context.get('default_type_entite', False) == 'rsc' else [('regime', '=', 'n')]