
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
    type_id = fields.Many2one('date.range.type', domain= "[('allow_overlap','=', True),('active', '=', True)]" )
    unit_of_time = fields.Selection(default=MONTHLY)
    duration_count = fields.Integer(default = 3)
    count = fields.Integer(default=4)