# -*- coding:utf-8 -*-
from openerp.osv import osv, fields
from datetime import datetime
from dateutil.relativedelta import relativedelta




class payroll_year(osv.osv):
    
    _name = "py.year"
    _description = "Payroll Year"
    _columns = {
        'name': fields.char('Year',),
        'code': fields.char('Code', size=6),
        'company_id': fields.many2one('res.company', 'Company'),
        'date_start': fields.date('Start Date'),
        'date_stop': fields.date('End Date'),
        'period_ids': fields.one2many('py.period', 'payroll_year_id', 'Periods'),
        'state': fields.selection([('draft', 'Open'), ('done', 'Closed')], 'State', readonly=True)
    }
    _defaults = {
        'state': 'draft',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }
    _order = "date_start, id"


    def _check_duration(self, cr, uid, ids, context=None):
        obj_fy = self.browse(cr, uid, ids[0], context=context)
        if obj_fy.date_stop < obj_fy.date_start:
            return False
        return True

    _constraints = [
        (_check_duration, 'Error! The start date of the fiscal year must be before his end date.', ['date_start', 'date_stop'])
    ]

    def create_period_2_weeks(self, cr, uid, ids, context=None):
        return self.create_period_week(cr, uid, ids, context, 2)

    def create_period_1_week(self, cr, uid, ids, context=None):
        return self.create_period_week(cr, uid, ids, context, 1)
        
    def create_period3(self, cr, uid, ids, context=None):
        return self.create_period(cr, uid, ids, context, 3)

    def create_period_week(self, cr, uid, ids, context=None, interval=1):
        
        period_obj = self.pool.get('py.period')
        for fy in self.browse(cr, uid, ids, context=context):
            ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
            period_obj.create(cr, uid, {
                    'name':  "%s %s" % (('Opening Period'), ds.strftime('%Y')),
                    'code': ds.strftime('00/%Y'),
                    'date_start': ds,
                    'date_stop': ds,
                    'special': True,
                    'payroll_year_id': fy.id,
                })
            while ds.strftime('%Y-%m-%d') < fy.date_stop:
                de = ds + relativedelta(weeks=interval, days=-1)

                if de.strftime('%Y-%m-%d') > fy.date_stop:
                    de = datetime.strptime(fy.date_stop, '%Y-%m-%d')

                period_obj.create(cr, uid, {
                    'name': ds.strftime('%d/%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'payroll_year_id': fy.id,
                })
                ds = ds + relativedelta(weeks=interval)
        return True

    def create_period(self, cr, uid, ids, context=None, interval=1):
        period_obj = self.pool.get('py.period')
        for fy in self.browse(cr, uid, ids, context=context):
            ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
            period_obj.create(cr, uid, {
                    'name':  "%s %s" % (('Opening Period'), ds.strftime('%Y')),
                    'code': ds.strftime('00/%Y'),
                    'date_start': ds,
                    'date_stop': ds,
                    'special': True,
                    'payroll_year_id': fy.id,
                })
            while ds.strftime('%Y-%m-%d') < fy.date_stop:
                de = ds + relativedelta(months=interval, days=-1)

                if de.strftime('%Y-%m-%d') > fy.date_stop:
                    de = datetime.strptime(fy.date_stop, '%Y-%m-%d')

                period_obj.create(cr, uid, {
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'payroll_year_id': fy.id,
                })
                ds = ds + relativedelta(months=interval)
        return True

    def find(self, cr, uid, dt=None, exception=True, context=None):
        res = self.finds(cr, uid, dt, exception, context=context)
        return res and res[0] or False

    def finds(self, cr, uid, dt=None, exception=True, context=None):
        if context is None: context = {}
        if not dt:
            dt = fields.date.context_today(self, cr, uid, context=context)
        args = [('date_start', '<=' , dt), ('date_stop', '>=', dt)]
        if context.get('company_id', False):
            company_id = context['company_id']
        else:
            company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        args.append(('company_id', '=', company_id))
        ids = self.search(cr, uid, args, context=context)
        if not ids:
            if exception:
                raise osv.except_osv(_('Error !'), _('No fiscal year defined for this date !\nPlease create one from the configuration of the accounting menu.'))
            else:
                return []
        return ids

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=80):
        if args is None:
            args = []
        if context is None:
            context = {}
        ids = []
        if name:
            ids = self.search(cr, user, [('code', 'ilike', name)] + args, limit=limit)
        if not ids:
            ids = self.search(cr, user, [('name', operator, name)] + args, limit=limit)
        return self.name_get(cr, user, ids, context=context)

payroll_year()


class payroll_period(osv.osv):
    _name = "py.period"
    _description = "Payroll period"
    _columns = {
        'name': fields.char('Period Name', size=64),
        'code': fields.char('Code', size=12),
        'special': fields.boolean('Opening/Closing Period', size=12, help="These periods can overlap."),
        'date_start': fields.date('Start of Period', states={'done':[('readonly', True)]}),
        'date_stop': fields.date('End of Period', states={'done':[('readonly', True)]}),
        'payroll_year_id': fields.many2one('py.year', 'Fiscal Year', states={'done':[('readonly', True)]}, select=True),
        'state': fields.selection([('draft', 'Open'), ('done', 'Closed')], 'State', readonly=True,
                                  help='When monthly periods are created. The state is \'Draft\'. At the end of monthly period it is in \'Done\' state.'),
        'company_id': fields.related('payroll_year_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True)
    }
    _defaults = {
        'state': 'draft',
    }
    
    _order = "date_start, special desc"
    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)', 'The name of the period must be unique per company!'),
    ]


    def name_list(self, cr, uid, ids, context=None):
        result = []
        for period in self.browse(cr, uid, ids, context):
            result.append(period.name)
        return result
    
    def _check_duration(self, cr, uid, ids, context=None):
        obj_period = self.browse(cr, uid, ids[0], context=context)
        if obj_period.date_stop < obj_period.date_start:
            return False
        return True

    def _check_year_limit(self, cr, uid, ids, context=None):
        for obj_period in self.browse(cr, uid, ids, context=context):
            if obj_period.special:
                continue

            if obj_period.payroll_year_id.date_stop < obj_period.date_stop or \
               obj_period.payroll_year_id.date_stop < obj_period.date_start or \
               obj_period.payroll_year_id.date_start > obj_period.date_start or \
               obj_period.payroll_year_id.date_start > obj_period.date_stop:
                return False

            pids = self.search(cr, uid, [('date_stop', '>=', obj_period.date_start), ('date_start', '<=', obj_period.date_stop), ('special', '=', False), ('id', '<>', obj_period.id)])
            for period in self.browse(cr, uid, pids):
                if period.payroll_year_id.company_id.id == obj_period.payroll_year_id.company_id.id:
                    return False
        return True

    _constraints = [
        (_check_duration, 'Error ! The duration of the Period(s) is/are invalid. ', ['date_stop']),
        (_check_year_limit, 'Invalid period ! Some periods overlap or the date period is not in the scope of the fiscal year. ', ['date_stop'])
    ]


    def next(self, cr, uid, period, step, context=None):
        ids = self.search(cr, uid, [('date_start', '>', period.date_start)])
        if len(ids) >= step:
            return ids[step - 1]
        return False

    def find(self, cr, uid, dt=None, context=None):
        if context is None: context = {}
        if not dt:
            dt = fields.date.context_today(self, cr, uid, context=context)
# CHECKME: shouldn't we check the state of the period?
        args = [('date_start', '<=' , dt), ('date_stop', '>=', dt)]
        if context.get('company_id', False):
            args.append(('company_id', '=', context['company_id']))
        else:
            company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
            args.append(('company_id', '=', company_id))
        result = []
        if context.get('account_period_prefer_normal'):
            # look for non-special periods first, and fallback to all if no result is found
            result = self.search(cr, uid, args + [('special', '=', False)], context=context)
        if not result:
            result = self.search(cr, uid, args, context=context)
        if not result:
            raise osv.except_osv(_('Error !'), _('No period defined for this date: %s !\nPlease create one.') % dt)
        return result

    def action_draft(self, cr, uid, ids, *args):
        mode = 'draft'
        cr.execute('update account_journal_period set state=%s where period_id in %s', (mode, tuple(ids),))
        cr.execute('update py_period set state=%s where id in %s', (mode, tuple(ids),))
        return True

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if args is None:
            args = []
        if context is None:
            context = {}
        ids = []
        if name:
            ids = self.search(cr, user, [('code', 'ilike', name)] + args, limit=limit)
        if not ids:
            ids = self.search(cr, user, [('name', operator, name)] + args, limit=limit)
        return self.name_get(cr, user, ids, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if 'company_id' in vals:
            move_lines = self.pool.get('account.move.line').search(cr, uid, [('period_id', 'in', ids)])
            if move_lines:
                raise osv.except_osv(_('Warning !'), _('You can not modify company of this period as some journal items exists.'))
        return super(payroll_period, self).write(cr, uid, ids, vals, context=context)

    def build_ctx_periods(self, cr, uid, period_from_id, period_to_id):
        if period_from_id == period_to_id:
            return [period_from_id]
        period_from = self.browse(cr, uid, period_from_id)
        period_date_start = period_from.date_start
        company1_id = period_from.company_id.id
        period_to = self.browse(cr, uid, period_to_id)
        period_date_stop = period_to.date_stop
        company2_id = period_to.company_id.id
        if company1_id != company2_id:
            raise osv.except_osv(_('Error'), _('You should have chosen periods that belongs to the same company'))
        if period_date_start > period_date_stop:
            raise osv.except_osv(_('Error'), _('Start period should be smaller then End period'))
        # for period from = january, we want to exclude the opening period (but it has same date_from, so we have to check if period_from is special or not to include that clause or not in the search).
        if period_from.special:
            return self.search(cr, uid, [('date_start', '>=', period_date_start), ('date_stop', '<=', period_date_stop), ('company_id', '=', company1_id)])
        return self.search(cr, uid, [('date_start', '>=', period_date_start), ('date_stop', '<=', period_date_stop), ('company_id', '=', company1_id), ('special', '=', False)])

payroll_period()


