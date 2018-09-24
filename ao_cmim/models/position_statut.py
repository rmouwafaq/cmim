# -*- coding: utf-8 -*-
from openerp import models, fields, api

class ProductCMIM(models.Model):
    _name = 'cmim.position.statut'

    statut_id = fields.Many2one('cmim.statut.assure', required=True, string='Statut', domain = lambda self: self._get_statut_domain())
    statut_regime = fields.Selection(related='statut_id.regime', store=False)
    date_debut_appl = fields.Date(string=u"Début applicabilité", required=True)
    date_fin_appl = fields.Date(string=u"Fin applicabilité", required=True)
    nbr_cjt = fields.Integer(string=u'Nbr Conjt.',default=1)
    assure_id = fields.Many2one('res.partner', string=u'Assuré')
    
    def _get_statut_domain(self):
        return [('regime', '=', 'rsc')] if self._context.get('default_type_entite', False) == 'rsc' else [('regime', '=', 'n')]

    @api.model
    def create(self, vals):
        if vals.get('statut_id') == self.env.ref('ao_cmim.epd').id:
            act_statut = self.search([('assure_id', '=', vals.get('assure_id')),
                             ('statut_id', '=', self.env.ref('ao_cmim.act').id)
                            ])
            if act_statut and act_statut.date_fin_appl < vals.get('date_fin_appl'):
                act_statut.write({'date_fin_appl' : vals.get('date_fin_appl')})
            elif not act_statut:
                value = vals.copy()
                value.update({'statut_id' : self.env.ref('ao_cmim.act').id})
                super(ProductCMIM, self).create(value)
        return super(ProductCMIM, self).create(vals)

