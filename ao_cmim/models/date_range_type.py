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
    parent_id = fields.Many2one('date.range','Parent')
    child_id = fields.One2many('date.range', 'parent_id', 'Child')

    @api.multi
    def generate_childs(self):
        self.ensure_one()
        vals = rrule(freq=1, interval=1,
                     dtstart=fields.Date.from_string(self.date_start),
                     count=4)
        vals = list(vals)
        date_ranges = []
        for idx, dt_start in enumerate(vals[:-1]):
            dt_start = dt_start.date()
            date_start = fields.Date.to_string(dt_start)
            # always remove 1 day for the date_end since range limits are
            # inclusive
            dt_end = vals[idx + 1].date() - relativedelta(days=1)
            date_end = fields.Date.to_string(dt_end)
            date_ranges.append({
                'name': '%s - %s' % (dt_start.strftime("%B"), dt_start.strftime("%Y")),
                'date_start': date_start,
                'date_end': date_end,
                'type_id': self.type_id.id,
                'parent_id':  self.id,
                'company_id': self.company_id.id})

        if date_ranges:
            _logger.info('#### date_ranges : %s' % date_ranges)
            for dr in date_ranges:
                self.create(dr)
        return True


class DateRangeType(models.Model):
    _inherit = "date.range.type"

    nb_days = fields.Integer('Nb jours Moyen', required=True)

