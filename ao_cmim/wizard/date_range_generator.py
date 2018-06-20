# -*- coding: utf-8 -*-
from openerp import api, fields, models
from dateutil.rrule import (rrule,
                            YEARLY,
                            MONTHLY,
                            WEEKLY,
                            DAILY)
from dateutil.relativedelta import relativedelta
import logging


class DateRangeGenerator(models.TransientModel):
    _inherit = 'date.range.generator'

    name_prefix = fields.Char(default="Trimestre" )
    type_id = fields.Many2one('date.range.type', domain="[('active', '=', True)]")
    unit_of_time = fields.Selection(default=MONTHLY)
    duration_count = fields.Integer(default = 3)
    count = fields.Integer(default=4)
    generate_childs = fields.Boolean('Générer les périodes filles')

    @api.multi
    def _generate_date_range_childs(self,parent_period):
        self.ensure_one()
        vals = rrule(freq=1, interval=1,
                     dtstart=fields.Date.from_string(parent_period.date_start),
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
                'name': u'%s - %s' % (dt_start.strftime("%B"), dt_start.strftime("%Y")),
                'date_start': date_start,
                'date_end': date_end,
                'type_id': self.env.ref('ao_cmim.data_range_type_mensuel').id,
                'parent_id':  parent_period.id,
                'company_id': self.company_id.id})

        if date_ranges:
            for dr in date_ranges:
                self.env['date.range'].create(dr)
        return True

    @api.multi
    def action_apply(self):
        date_ranges = self._compute_date_ranges()
        if date_ranges:
            for dr in date_ranges:
                d = self.env['date.range'].create(dr)
                if self.generate_childs:
                    self._generate_date_range_childs(d)
        return self.env['ir.actions.act_window'].for_xml_id(
            module='date_range', xml_id='date_range_action')