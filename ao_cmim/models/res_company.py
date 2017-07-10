# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _

class ResCompany(models.Model):
    _inherit = 'res.company'

    statut_update_date = fields.Date(u'Dernière Mise à jour des statuts')
        

    