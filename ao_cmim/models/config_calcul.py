# -*- coding: utf-8 -*-
from openerp import models, fields, tools, api, _
from openerp.exceptions import UserError

class ConstanteCalcul(models.Model):
    _name = 'cmim.constante'
    @api.multi
    def unlink(self):
        if self.reserved:
            raise UserError(
                _(u"Impossible de supprimer des constantes de calcul réservées au système"))
        else:
            return super(ConstanteCalcul, self).unlink()
         
    @api.multi
    def _get_val_trimestrielle(self):
        for obj in self:
            obj.valeur = obj.val_mensuelle*3
             
    reserved = fields.Boolean(u'réservé au système', default=False)
    name = fields.Char('Nom ', required=True)
    valeur = fields.Float('Valeur ', compute=_get_val_trimestrielle)
    val_mensuelle = fields.Float('Valeur Mensuelle', required=True)
     
class Tarif(models.Model):
    _name = 'cmim.tarif'
    name = fields.Char('Nom', required=True)
    type = fields.Selection(selection=[('p', 'Taux'),
                                        ('f', 'Forfait')],
                                        required=True,
                                        default="p",
                                        string='Type de tarif')
    montant = fields.Float('Tarif', required=True)    
     
class RegleCalcul(models.Model):
    _name = "cmim.regle.calcul"
    _order = 'reserved desc, type asc, sequence, regle_base_id desc'
    @api.multi
    def unlink(self):
        for obj in self:
            if obj.reserved:
                raise UserError(
                    _(u"Impossible de supprimer les règles de calcul réservées au système"))
            else:
                return super(RegleCalcul, self).unlink()
    @api.onchange('type')
    def onchange_type(self):
        domain_tarif = []
        domain_statut = [('regime', '=', 'n')]
        if self.type and self.type == 'taux':
            self.applicabilite_proratat = False
            domain_tarif = [('type', '=', 'p')]
        elif self.type == 'trsc':
            self.applicabilite_proratat = False
            domain_statut = [('regime', '=', 'rsc')]
        return {'domain':{ 'default_tarif_id': domain_tarif, 
                           'statut_ids': domain_statut, }}
        
             
    name = fields.Char('Nom', required=True)
    reserved = fields.Boolean('Reserved')
    sequence = fields.Integer('Sequence')
    code = fields.Char('Code')
    notes = fields.Text('Notes')
    secteur_inverse = fields.Boolean(u'Applicabilité inverse')
    secteur_ids = fields.Many2many('cmim.secteur', 'cmim_regle_calcul_secteur_rel', 'regle_id', 'secteur_id', string="Secteurs")
    garantie_ids = fields.Many2many('cmim.garantie', 'cmim_regle_calcul_garantie_rel', 'regle_id', 'garantie_id', string="Garanties Applicables")
    default_tarif_id = fields.Many2one('cmim.tarif', string=u'Tarif par défaut',  ondelete = 'restrict')
    debut_applicabilite = fields.Date(u"Date début de validité")
    fin_applicabilite = fields.Date(u"Date fin de validité")
    regle_base_id = fields.Many2one('cmim.regle.calcul', 'Base Calcul', domain=[('type', 'not in', ['taux', 'abat'])], ondelete = 'restrict')
    regle_tarif_id = fields.Many2one('cmim.regle.calcul', 'Taux Calcul', domain=[('type', '=', 'taux')], ondelete = 'restrict')
    type = fields.Selection(selection=[('taux', 'Tarif'),
                                        ('tbase', 'Base'),
                                        ('tabat', 'Abattement'),
                                        ('trsc', 'Spéciale')],
                                        default="tbase", string='Type de règle',
                                        help=u"Les règles de calcul intermédaires servent à définir les bons tarifs tandis que les règles de calcul contractuelles définissent les bases de calul , le tarif pris en compte lors du calcul est soit le tarif associé à la règle intermédiaire dans le paramétrage de la collectivité, soit le tarif par défaut définit dans la règle de calcul contractuelle.")
    applicabilite_proratat = fields.Boolean(u'Applicabilité prorata', default=True)
    applicabilite_abattement = fields.Boolean(u'Applicabilité Abattement', default=False)
    applicabilite_statut = fields.Selection([('all','Tout les statuts'),
                                             ('only','Appliquable Pour'),
                                             ('exclude','Exclure Pour')],string=u"Applicabilité statut",default='all')
    statut_ids = fields.Many2many('cmim.statut.assure', 'regle_calcul_statut_rel', 'regle_id', 'statut_id',
                                  string=u"Type de positions")
