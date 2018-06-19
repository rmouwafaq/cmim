# -*- coding: utf-8 -*-
from openerp import api, fields, models
from dateutil.rrule import (rrule,
                            YEARLY,
                            MONTHLY,
                            WEEKLY,
                            DAILY)
from dateutil.relativedelta import relativedelta


class DateRangeGenerator(models.TransientModel):
    _inherit = 'date.range.generator'

    name_prefix = fields.Char(default="Trimestre" )
    type_id = fields.Many2one('date.range.type', domain="[('active', '=', True)]")
    unit_of_time = fields.Selection(default=MONTHLY)
    duration_count = fields.Integer(default = 3)
    count = fields.Integer(default=4)
    generate_childs = fields.Boolean('Générer les périodes filles')


    @api.multi
    def action_apply(self):
        date_ranges = self._compute_date_ranges()
        if date_ranges:
            for dr in date_ranges:
                dr = self.env['date.range'].create(dr)
                if self.generate_childs:
                    dr.generate_childs()
        return self.env['ir.actions.act_window'].for_xml_id(
            module='date_range', xml_id='date_range_action')