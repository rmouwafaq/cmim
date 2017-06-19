# -*- coding: utf-8 -*-
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import osv, fields
from openerp import models, fields, exceptions, api, _
from openerp.exceptions import UserError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
  
    
class declaration(models.Model):
    _name = 'cmim.declaration'
    _order = "date_range_end desc"
    _sql_constraints = [
        ('fiscal_date', "check(fiscal_date > 1999)", _(u"Valeur incorrecte pour l'anné comptable !")),
        ('nb_jour', "check(nb_jour > 0)", _(u"Valeur incorrecte pour le nombre de jour déclarés !"))
    ]

    import_flag = fields.Boolean('Par import', default=False)   
    collectivite_id = fields.Many2one('res.partner', u'Collectivité', ondelete='cascade', domain="[('is_collectivite','=',True)]", required=True)   
    assure_id = fields.Many2one('res.partner', u'Assuré', required=True, domain="[('is_collectivite','=',False)]", ondelete='cascade')  #  , 
    nb_jour = fields.Integer(u'Nombre de jours déclarés', required=True)
    salaire = fields.Float('salaire', required=True)
    secteur_id = fields.Many2one('cmim.secteur',
        string='Secteur',
        related='collectivite_id.secteur_id', store=True
    )
    @api.multi
    def action_validate(self):
        for obj in self:
            if not self.search([   ('assure_id.id', '=', obj.assure_id.id), 
                                   ('collectivite_id.id', '=', obj.collectivite_id.id), 
                                   ('date_range_id.id', '=', obj.date_range_id.id),
                                   ('state', '=', 'valide')]):
                obj.state = 'valide'
            else:
                raise UserError(
                _(u"Erreur de validation!! Une déclaration a été déjà validée pour le même assuré, la même collectivité durant cette période"))
            
    state = fields.Selection(selection=[('non_valide', u'Non Validée'), ('valide', u'Validée')],default='non_valide', string="Etat")
    notes = fields.Text('Notes')
    @api.multi
    @api.depends('id_used', 'collectivite_id.code', 'assure_id.id_num_famille', 'assure_id.numero')
    def get_code(self):
        for obj in self:
            if (obj.id_used == 'old'):
                obj.code = '%s%s' %(obj.collectivite_id.code, obj.assure_id.id_num_famille)
            else:
                obj.code = '%s%s' %(obj.collectivite_id.code, obj.assure_id.numero)
            
    code = fields.Char('Code', compute="get_code", store=True) 
    id_used = fields.Selection(string="id used", selection=[('old', 'id Num Famille'), ('new', 'Id Num Personne')], default='old')
    base_calcul = fields.Float(u'Salaire Plafonné par Secteur', compute="get_base_calcul", default=0.0, 
                   help=u"La base de calcul = Salaire si compris entre plancher et plafond du Secteur de la collectivité.\
                        , si le Salaire < plancher du secteur la base de calcul prend pour valeur ce dernier.\
                        idem, si le salaire dépasse le plafond du secteur de la collectivité le plafond est lui-même la base de calcul qui sera prise")
    base_trancheA = fields.Float(u'TrancheA', compute="get_base_calcul", default=0.0,
                                 help="La tranche A = Salaire si salaire < Plafond CNSS, sinon Plafond CNSS.") 
    base_trancheB = fields.Float(u'trancheB', compute="get_base_calcul", default=0.0,
                                 help=u" trancheB = salaire - Tranche A si salaire > TrancheA, sinon  0.\
                                      La tranche B plafonnée= trancheB si trancheB < SRP, sinon  SRP.")
    
    p_base_calcul = fields.Float(u'Salaire Plafonné par Secteur', compute="get_base_calcul_proratat", default=0.0, 
                   help=u"La base de calcul = Salaire si compris entre plancher et plafond du Secteur de la collectivité.\
                        , si le Salaire < plancher du secteur la base de calcul prend pour valeur ce dernier.\
                        idem, si le salaire dépasse le plafond du secteur de la collectivité le plafond est lui-même la base de calcul qui sera prise")
    p_base_trancheA = fields.Float(u'TrancheA', compute="get_base_calcul_proratat", default=0.0,
                                 help="La tranche A = Salaire si salaire < Plafond CNSS, sinon Plafond CNSS.") 
    p_base_trancheB = fields.Float(u'trancheB', compute="get_base_calcul_proratat", default=0.0,
                                 help=u" trancheB = salaire - Tranche A si salaire > TrancheA, sinon  0.\
                                      La tranche B plafonnée= trancheB si trancheB < SRP, sinon  SRP.")  
    
    @api.multi
    @api.depends('salaire', 'secteur_id')
    def get_base_calcul(self ):
        cnss = self.env.ref('ao_cmim.cte_calcul_cnss') 
        srp = self.env.ref('ao_cmim.cte_calcul_srp') 
        if cnss and srp:
            for obj in self:
                # calcul de base_calcul
                obj.base_calcul = min(float(obj.secteur_id.plafond), max(float(obj.secteur_id.plancher), float(obj.salaire)))
                #calcul de base_trancheA
                obj.base_trancheA = min(float(cnss.valeur) ,float(obj.salaire))
                #calcul de base_trancheB 
                res = 0.0
                if(obj.salaire > obj.base_trancheA):
                    res = obj.salaire - obj.base_trancheA
                diff_srp = float(srp.valeur) - obj.p_base_trancheA
                obj.base_trancheB = min(float(diff_srp) ,float(res))
        else:
            raise osv.except_osv(_('Error!'), _(u"Veuillez vérifier la configuration des constantes de calcul" ))
    @api.multi
    @api.depends('salaire', 'secteur_id')
    def get_base_calcul_proratat(self ):
        
        cnss = self.env.ref('ao_cmim.cte_calcul_cnss') 
        srp = self.env.ref('ao_cmim.cte_calcul_srp') 
        if cnss and srp:
            for obj in self:
                proratat = float(obj.nb_jour / 90.0) 
                # calcul de base_calcul
                obj.p_base_calcul = min(float(obj.secteur_id.plafond * proratat), max(float(obj.secteur_id.plancher) * proratat, float(obj.salaire)))
                #calcul de base_trancheA
                obj.p_base_trancheA = min(float(cnss.valeur) * proratat ,float(obj.salaire))
                #calcul de base_trancheB 
                res = 0.0
                if(obj.salaire > obj.p_base_trancheA):
                    res = obj.salaire - obj.p_base_trancheA
                diff_srp = float(srp.valeur) - obj.p_base_trancheA
                obj.p_base_trancheB = min( diff_srp* proratat ,float(res))
        else:
            raise osv.except_osv(_('Error!'), _(u"Veuillez vérifier la configuration des constantes de calcul" ))
    
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
        
    fiscal_date = fields.Integer(string=u"Année Comptable", required=True, default= datetime.now().year )
    date_range_id = fields.Many2one('date.range', u'Période', required=True)
    date_range_end = fields.Date('date.range',
        related='date_range_id.date_end', store=True
    )