# -*- coding: utf-8 -*-
from datetime import datetime
from openerp import models, fields, api

class ProductCMIM(models.Model):
    _name = 'cmim.position.statut'


    statut_id = fields.Many2one('cmim.statut.assure', required=True, string='Statut')
    date_debut_appl = fields.Date(string=u"Début applicabilité", required=True)
    date_fin_appl = fields.Date(string=u"Fin applicabilité", required=True)
    assure_id = fields.Many2one('res.partner', string=u'Assuré')