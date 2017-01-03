
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import osv, fields
from openerp import models, fields, exceptions, api, _
from openerp.exceptions import UserError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
  
    
class declaration(models.Model):
    _name = 'cmim.declaration'
    
    import_flag = fields.Boolean('Par import', default=False)      
    assure_id = fields.Many2one('cmim.assure', 'Assure', ondelete='cascade')  # domain=[('collectivite_id.id','=',collectivite_id.id)] , 
    collectivite_id = fields.Many2one('res.partner', 'Collectivite', ondelete='cascade')
    nb_jour = fields.Integer('Nombre de jours declares')
    salaire = fields.Float('salaire')
    secteur_id = fields.Many2one('cmim.secteur',
        string='Secteur',
        related='collectivite_id.secteur_id', store=True
    )
    
    @api.onchange('fiscal_date')
    def onchange_field_id(self):
         if self.fiscal_date:
            periodes = self.env['date.range'].search([])
            ids = []
            dec_year = datetime.strptime(self.fiscal_date, '%Y-%m-%d').year
            for periode in periodes :
                duree =  (datetime.strptime(periode.date_end, '%Y-%m-%d') - datetime.strptime(periode.date_start, '%Y-%m-%d')).days
                if duree>88 and duree <92 and dec_year == datetime.strptime(periode.date_end, '%Y-%m-%d').year and dec_year == datetime.strptime(periode.date_start, '%Y-%m-%d').year:
                    ids.append(periode.id)
            return {'domain':{'date_range_id': [('id', 'in', ids)]}}
    @api.model
    def _get_domain(self):
        periodes = self.env['date.range'].search([])
        ids = []
        for periode in periodes :
            duree =  (datetime.strptime(periode.date_end, '%Y-%m-%d') - datetime.strptime(periode.date_start, '%Y-%m-%d')).days
            if duree>88 and duree <92:
                ids.append(periode.id)
        return [('id', 'in', ids)]
    
    @api.onchange('fiscal_date')
    def onchange_fiscal_date(self):
        if(self.fiscal_date):
            print self.fiscal_date
            date = str(datetime.strptime(self.fiscal_date, '%Y-%m-%d').year) + "-1-1"
            mydate = datetime.strptime(date, '%Y-%m-%d')
            self.fiscal_date = mydate
            
    fiscal_date = fields.Date(string="Annee fiscale")
    date_range_id = fields.Many2one('date.range', 'Periode', domain=lambda self: self._get_domain())
    