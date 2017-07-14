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

    import_flag = fields.Boolean('Par import', default=False)
    collectivite_id = fields.Many2one('res.partner', u'Collectivité', ondelete='cascade', domain="[('type_entite','=','c')]", required=True)   
    assure_id = fields.Many2one('res.partner', u'Assuré', required=True, domain="[('type_entite','=','a')]", ondelete='cascade')  #  , 
    nb_jour = fields.Integer(u'Nombre de jours déclarés', required=True)
    salaire = fields.Float('salaire', required=True)
    secteur_id = fields.Many2one('cmim.secteur', string='Secteur',
        related='collectivite_id.secteur_id', store=True)
    statut_id = fields.Many2one('cmim.statut.assure', string=u'Statut Assuré',
        related='assure_id.statut_id', store=True)

    state = fields.Selection(selection=[('non_valide', u'Non Validée'), ('valide', u'Validée')],default='non_valide', string="Etat")
    notes = fields.Text('Notes')
    date_range_end = fields.Date('date.range', related='date_range_id.date_end', store=True)
    date_range_id = fields.Many2one('date.range', u'Période',
                                    domain="[('type_id', '=', type_id), ('active', '=', True)]", required=True)
    type_id = fields.Many2one('date.range.type', u'Type de péride',domain="[('active', '=', True)]", required=True)
    # type_id_nb_days = fields.Integer('date.range.type', related='type_id.nb_days', store=True)
    cotisation_id = fields.Many2one('cmim.cotisation', compute=lambda self: self._get_cotisation())

    @api.onchange('nb_jour', 'type_id')
    def onchange_nb_jour(self):
        print 'enteeeeeeeeeeeeeeeeeeeer'
        if self.type_id and self.nb_jour > self.type_id.nb_days:
            raise exceptions.Warning(
                _(u"Valeur incorrecte pour le nombre de jour.\n Le nombre de jour moyen de la période vaut %s. \
                   Vérifiez la configuration des types de périodes !!!." % self.type_id.nb_days))

    def _get_cotisation(self):
        line = self.env['cmim.cotisation.assure.line'].search([('declaration_id', '=', self.id)],limit=1)
        self.cotisation_id = line.cotisation_id.id if line else None
    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        if self.date_range_id:
            self.type_id = self.date_range_id.type_id.id
    # @api.onchange('type_id')
    # def onchange_type_id(self):
    #     if (self.fiscal_date):
    #         periodes = self.env['date.range'].search([])
    #         ids = []
    #         for periode in periodes:
    #             duree = (datetime.strptime(periode.date_end, '%Y-%m-%d') - datetime.strptime(periode.date_start,
    #                                                                                          '%Y-%m-%d')).days
    #             if duree > 88 and duree < 92 and self.fiscal_date == datetime.strptime(periode.date_end,
    #                                                                                    '%Y-%m-%d').year and self.fiscal_date == datetime.strptime(
    #                     periode.date_start, '%Y-%m-%d').year:
    #                 ids.append(periode.id)
    #         return {'domain': {'date_range_id': [('id', 'in', ids)]}}

    @api.multi
    def action_validate(self):
        for obj in self:
            if not self.search([('assure_id.id', '=', obj.assure_id.id),
                                ('collectivite_id.id', '=', obj.collectivite_id.id),
                                ('date_range_id.id', '=', obj.date_range_id.id),
                                ('state', '=', 'valide')]):
                obj.state = 'valide'
            else:
                raise UserError(
                    _(
                        u"Erreur de validation!! Une déclaration a été déjà validée pour le même assuré, la même collectivité durant cette période"))

    # base_calcul = fields.Float(u'Salaire Plafonné par Secteur', compute="get_base_calcul", default=0.0,
    #                help=u"La base de calcul = Salaire si compris entre plancher et plafond du Secteur de la collectivité.\
    #                     , si le Salaire < plancher du secteur la base de calcul prend pour valeur ce dernier.\
    #                     idem, si le salaire dépasse le plafond du secteur de la collectivité le plafond est lui-même la base de calcul qui sera prise")
    # base_trancheA = fields.Float(u'TrancheA', compute="get_base_calcul", default=0.0,
    #                              help="La tranche A = Salaire si salaire < Plafond CNSS, sinon Plafond CNSS.")
    # base_trancheB = fields.Float(u'trancheB', compute="get_base_calcul", default=0.0,
    #                              help=u" trancheB = salaire - Tranche A si salaire > TrancheA, sinon  0.\
    #                                   La tranche B plafonnée= trancheB si trancheB < SRP, sinon  SRP.")
    #
    # p_salaire = fields.Float(u'Salaire Brut', compute="get_base_calcul_proratat", default=0.0)
    #
    # p_base_calcul = fields.Float(u'Salaire Plafonné par Secteur', compute="get_base_calcul_proratat", default=0.0,
    #                help=u"La base de calcul = Salaire si compris entre plancher et plafond du Secteur de la collectivité.\
    #                     , si le Salaire < plancher du secteur la base de calcul prend pour valeur ce dernier.\
    #                     idem, si le salaire dépasse le plafond du secteur de la collectivité le plafond est lui-même la base de calcul qui sera prise")
    # p_base_trancheA = fields.Float(u'TrancheA', compute="get_base_calcul_proratat", default=0.0,
    #                              help="La tranche A = Salaire si salaire < Plafond CNSS, sinon Plafond CNSS.")
    # p_base_trancheB = fields.Float(u'trancheB', compute="get_base_calcul_proratat", default=0.0,
    #                              help=u" trancheB = salaire - Tranche A si salaire > TrancheA, sinon  0.\
    #                                   La tranche B plafonnée= trancheB si trancheB < SRP, sinon  SRP.")
    #
    # @api.multi
    # @api.depends('salaire', 'secteur_id')
    # def get_base_calcul(self ):
    #     cnss = self.env.ref('ao_cmim.cte_calcul_cnss')
    #     srp = self.env.ref('ao_cmim.cte_calcul_srp')
    #     if cnss and srp:
    #         for obj in self:
    #             # if not obj.secteur_id.is_complementary:
    #             # calcul de base_calcul
    #             obj.base_calcul = min(float(obj.secteur_id.plafond), max(float(obj.secteur_id.plancher), float(obj.salaire)))
    #             #calcul de base_trancheA
    #             obj.base_trancheA = min(float(cnss.valeur) ,float(obj.salaire))
    #             #calcul de base_trancheB
    #             res = 0.0
    #             if(obj.salaire > obj.base_trancheA):
    #                 res = obj.salaire - obj.base_trancheA
    #             diff_srp = float(srp.valeur) - obj.p_base_trancheA
    #             obj.base_trancheB = min(float(diff_srp) ,float(res))
    #             # else:
    #             #     obj.base_calcul = obj.salaire
    #             #     obj.base_trancheA = obj.salaire
    #             #     obj.base_trancheB = obj.salaire
    #     else:
    #         raise osv.except_osv(_('Error!'), _(u"Veuillez vérifier la configuration des constantes de calcul" ))
    # @api.multi
    # @api.depends('salaire', 'secteur_id')
    # def get_base_calcul_proratat(self ):
    #
    #     cnss = self.env.ref('ao_cmim.cte_calcul_cnss')
    #     srp = self.env.ref('ao_cmim.cte_calcul_srp')
    #     if cnss and srp:
    #         for obj in self:
    #             # if not obj.secteur_id.is_complementary:
    #             proratat = float(obj.nb_jour / 90.0)
    #             # calcul de base_calcul
    #             obj.p_base_calcul = min(float(obj.secteur_id.plafond * proratat), max(float(obj.secteur_id.plancher) * proratat, float(obj.salaire)))
    #             #calcul de base_trancheA
    #             obj.p_base_trancheA = min(float(cnss.valeur) * proratat ,float(obj.salaire))
    #             #calcul de base_trancheB
    #             res = 0.0
    #             if(obj.salaire > obj.p_base_trancheA):
    #                 res = obj.salaire - obj.p_base_trancheA
    #             diff_srp = float(srp.valeur) - obj.p_base_trancheA
    #             obj.p_base_trancheB = min( diff_srp* proratat ,float(res))
    #             obj.p_salaire = obj.salaire * proratat
    #             # else :
    #             #     obj.p_base_calcul = obj.salaire
    #             #     obj.p_base_trancheA = obj.salaire
    #             #     obj.p_base_trancheB = obj.salaire
    #     else:
    #         raise osv.except_osv(_('Error!'), _(u"Veuillez vérifier la configuration des constantes de calcul" ))
    #
