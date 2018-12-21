# -*- coding: utf-8 -*-
from openerp import api, fields, models
from dateutil.rrule import (rrule,
                            YEARLY,
                            MONTHLY,
                            WEEKLY,
                            DAILY)
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

class DateRange(models.Model):
    _inherit = "date.range"
    _order = "date_end desc"
    parent_id = fields.Many2one('date.range','Parent')
    child_id = fields.One2many('date.range', 'parent_id', 'Child')

class DateRangeType(models.Model):
    _inherit = "date.range.type"

    nb_days = fields.Integer('Nb jours Moyen', required=True)

