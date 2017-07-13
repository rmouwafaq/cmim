# -*- coding: utf-8 -*-

from openerp import api, fields, models
class DateRangeType(models.Model):
    _inherit = "date.range.type"

    nb_days = fields.Integer('Nb jours Moyen', required=True)

