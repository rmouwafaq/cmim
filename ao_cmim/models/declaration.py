# -*- coding: utf-8 -*-
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
    @api.multi
    def get_salaire_mensuel(self):
        for obj in self:
            obj.sal_mensuel = (obj.salaire/obj.nb_jour) * 30
    import_flag = fields.Boolean('Par import', default=False)      
    assure_id = fields.Many2one('cmim.assure', 'Assure', ondelete='cascade')  # domain=[('collectivite_id.id','=',collectivite_id.id)] , 
    collectivite_id = fields.Many2one('res.partner', 'Collectivite', ondelete='cascade')
    nb_jour = fields.Integer('Nombre de jours declares')
    sal_mensuel = fields.Float('Salaire mensuel', compute="get_salaire_mensuel")
    salaire = fields.Float('salaire')
    secteur_id = fields.Many2one('cmim.secteur',
        string='Secteur',
        related='collectivite_id.secteur_id', store=True
    )
    
    base_calcul = fields.Float(u'Salaire Plafonné par Secteur', compute="get_base_calcul", default=0.0, 
                   help="La base de calcul = Salaire si compris entre plancher et plafond du Secteur de la collectivite.\
                        , si le Salaire < plancher du secteur la base de calcul prend pour valeur ce dernier.\
                        idem, si le salaire depasse le plafond du secteur de la collectivite le plafond est lui-meme la base de calcul qui sera prise")
    base_trancheA = fields.Float(u'TrancheA', compute="get_base_calcul", default=0.0,
                                 help="La tranche A = Salaire si salaire < Plafond CNSS, sinon Plafond CNSS.") 
    base_trancheB = fields.Float(u'trancheB', compute="get_base_calcul", default=0.0,
                                 help=" trancheB = salaire - Tranche A si salaire > TrancheA, sinon  0.\
                                      La tranche B plafonnee= trancheB si trancheB < SRP, sinon  SRP.")  
    
    @api.multi
    @api.depends('salaire', 'secteur_id')
    def get_base_calcul(self ):
        cnss = self.env.ref('ao_cmim.cte_calcul_cnss') 
        srp = self.env.ref('ao_cmim.cte_calcul_srp') 
        if cnss and srp:
            for obj in self:
                # calcul de base_calcul
                obj.base_calcul = min(float(obj.secteur_id.plafond), max(float(obj.secteur_id.plancher), float(obj.sal_mensuel)))
                #calcul de base_trancheA
                obj.base_trancheA = min(float(cnss.valeur) ,float(obj.sal_mensuel))
                #calcul de base_trancheB 
                res = 0.0
                if(obj.sal_mensuel > obj.base_trancheA):
                    res = obj.sal_mensuel - obj.base_trancheA
                obj.base_trancheB = min(float(srp.valeur) ,float(res))
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
        
    fiscal_date = fields.Integer(string="Annee Comptable", required=True)
    date_range_id = fields.Many2one('date.range', 'Periode', required=True)
