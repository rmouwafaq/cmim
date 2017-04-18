
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import osv, fields
from openerp import models, fields, exceptions, api, _
from openerp.exceptions import UserError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
  
    
class declaration(models.Model):
    _name = 'cmim.declaration'
    _sql_constraints = [
        ('fiscal_date', "check(fiscal_date > 1999)", _("Valeur incorrecte pour l'an comptable !"))
    ]
    import_flag = fields.Boolean('Par import', default=False)      
    assure_id = fields.Many2one('cmim.assure', 'Assure', ondelete='cascade')  # domain=[('collectivite_id.id','=',collectivite_id.id)] , 
    collectivite_id = fields.Many2one('res.partner', 'Collectivite', ondelete='cascade')
    nb_jour = fields.Integer('Nombre de jours declares')
    salaire = fields.Float('salaire')
    secteur_id = fields.Many2one('cmim.secteur',
        string='Secteur',
        related='collectivite_id.secteur_id', store=True
    )
    
    base_calcul = fields.Float('Base', compute="get_base_calcul", default=0.0, 
                   help="La base de calcul = Salaire si compris entre plancher et plafond du Secteur de la collectivite.\
                        , si le Salaire < plancher du secteur la base de calcul prend pour valeur ce dernier.\
                        idem, si le salaire depasse le plafond du secteur de la collectivite le plafond est lui-meme la base de calcul qui sera prise")
    base_trancheA = fields.Float('Base', compute="get_base_calcul", default=0.0,
                                 help="La tranche A = Salaire si salaire < Plafond CNSS, sinon Plafond CNSS.") 
    base_trancheB = fields.Float('Base', compute="get_base_calcul", default=0.0,
                                 help=" trancheB = salaire - Tranche A si salaire > TrancheA, sinon  0.\
                                      La tranche B plafonnee= trancheB si trancheB < SRP, sinon  SRP.")  
    
    @api.multi
    @api.depends('salaire', 'secteur_id')
    def get_base_calcul(self ):
        cnss = self.env.ref('ao_cmim.cte_calcul_cnss') or self.env.search([('name', '=', 'CNSS')]) 
        srp = self.env.ref('ao_cmim.cte_calcul_srp') or self.env.search([('name', '=', 'SRP')]) 
        if cnss and srp:
            for obj in self:
                # calcul de base_calcul
                if obj.salaire >= obj.secteur_id.plancher and obj.salaire <= obj.secteur_id.plafond:
                    obj.base_calcul = obj.salaire
                elif obj.salaire <= obj.secteur_id.plancher: 
                    obj.base_calcul = obj.secteur_id.plancher
                else:
                    obj.base_calcul = obj.secteur_id.plafond
                #calcul de base_trancheA
                if cnss.valeur > obj.salaire:
                    obj.base_trancheA = obj.salaire
                else: 
                    obj.base_trancheA = cnss.valeur     
                #calcul de base_trancheB 
                if(obj.salaire > obj.base_trancheA):
                    res = obj.salaire - obj.base_trancheA
                if(res > srp.valeur):
                    obj.base_trancheB = srp.valeur
                else: 
                    obj.base_trancheB = res
        else:
            raise osv.except_osv(_('Error!'), _("Veuillez verifier la configuration des constantes de calcul" ))
    
    @api.onchange('fiscal_date')
    def onchange_fiscal_date(self):
        if(self.fiscal_date):
            periodes = self.env['date.range'].search([])
            ids = []
            for periode in periodes :
                duree = (datetime.strptime(periode.date_end, '%Y-%m-%d') - datetime.strptime(periode.date_start, '%Y-%m-%d')).days
                if duree > 88 and duree < 92 and self.fiscal_date == datetime.strptime(periode.date_end, '%Y-%m-%d').year and self.fiscal_date == datetime.strptime(periode.date_start, '%Y-%m-%d').year:
                    ids.append(periode.id)
            return {'domain':{'date_range_id': [('id', 'in', ids)]}}
        
    fiscal_date = fields.Integer(string="Annee Comptable")
    date_range_id = fields.Many2one('date.range', 'Periode')
