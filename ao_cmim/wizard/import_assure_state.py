# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import date
from openerp import fields, models, exceptions, api, _
import base64
import csv
import cStringIO
from openerp.exceptions import UserError
import logging



#############################################################################

class ImportStatus(models.TransientModel):
    _name = 'cmim.import.state'

    data = fields.Binary("Fichier", required=True)
    delimeter = fields.Char('Delimeter', default=';',
                            help='Default delimeter is ";"')

    statut_id = fields.Many2one('cmim.statut.assure', string='Statut')
    collectivite_id = fields.Many2one('res.partner', domain="[('type_entite', '=', 'c')]")
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get())

    header = fields.Boolean(u'Entête', default=True)
    date_range_id = fields.Many2one('date.range', u'Période',
                                    domain="[('active', '=', True)]", required=True)
    type_id = fields.Many2one('date.range.type', u'Type de péride', domain=lambda self: self._get_domain(),
                              required=True)

    def _get_domain(self):
        return [('active', '=', True),
                ('id', 'in', [self.env.ref('ao_cmim.data_range_type_trimestriel').id,
                              self.env.ref('ao_cmim.data_range_type_mensuel').id])]

    @api.multi
    def import_assure_state(self, reader_info):
        partner_obj = self.env['res.partner']
        statut_obj = self.env['cmim.position.statut']

        assure_ids = []
        for i, line in enumerate(reader_info):

            partner_id = partner_obj.search([('numero', '=', line[0])])
            statut_item = {
                        'statut_id': self.statut_id.id,
                        'date_debut_appl': self.date_range_id.date_start,
                        'date_fin_appl': self.date_range_id.date_end
                           }

            if not partner_id:
                assure_item = {'numero': line[0],
                               'name': line[1]+" "+line[2],
                               'type_entite': 'a'}
                partner_id = partner_obj.create(assure_item)

            assure_ids.append(partner_id.id)
            statut_item['assure_id'] = partner_id.id

            # statut_ids = statut_obj.search([("date_debut_appl","=",statut_item['date_debut_appl']),("date_fin_appl","=",statut_item['date_fin_appl']),('assure_id','=',statut_item['assure_id'])])
            statut_ids = statut_obj.search([('assure_id','=',statut_item['assure_id']), ('statut_id', '=', statut_item['statut_id'])])
            logging.warning("statut %s => %s", line[0], statut_ids)
            if statut_ids:
                if statut_ids[0].date_debut_appl < statut_item['date_debut_appl']:
                    del statut_item['date_debut_appl']

                if statut_ids[0].date_fin_appl > statut_item['date_fin_appl']:
                    del statut_item['date_fin_appl']

                statut_ids[0].write(statut_item)
            else:
                statut_obj.create(statut_item)

        return {
            'name': "assurés imported",
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': self.env.ref('ao_cmim.view_assure_tree').id,
            'res_model': 'res.partner',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('id','in', assure_ids)],
            'type': 'ir.actions.act_window',
            'target': 'self',
        }

    @api.multi
    def import_state(self):
        data = base64.b64decode(self.data)
        file_input = cStringIO.StringIO(data)
        file_input.seek(0)
        reader_info = []
        if self.delimeter:
            delimeter = str(self.delimeter)
        else:
            delimeter = ';'
        reader = csv.reader(file_input, delimiter=delimeter,
                            lineterminator='\r\n')
        try:
            reader_info.extend(reader)
        except Exception as e:
            raise exceptions.Warning(_(u"Le fichier sélectionné n'est pas valide!"+str(e)))
        if self.header:
            del reader_info[0]
        if (not self.env['res.partner'].search([('type_entite', '=', 'c')])):
            raise exceptions.Warning(_(
                u"L'import des encaissements exige l'existances des collectivités dans le système, veuillez créer les collectivités en premier"))
        else:
            return self.import_assure_state(reader_info)

