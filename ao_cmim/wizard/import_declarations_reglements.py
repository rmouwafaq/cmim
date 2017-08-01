# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import date
from openerp import fields, models, exceptions, api, _
import base64
import csv
import cStringIO
from openerp.exceptions import UserError


#############################################################################

class cmimImportDecPay(models.TransientModel):
    _name = 'cmim.import.dec.pay'

    data = fields.Binary("Fichier", required=True)
    delimeter = fields.Char('Delimeter', default=';',
                            help='Default delimeter is ";"')
    type_operation = fields.Selection(selection=[('declaration', u'Déclarations'), ('reglement', 'Encaissements')],
                                      required=True, string=u"Type d'opération", default='declaration')
    model = fields.Selection(selection=[('old', 'Ancien Format'), ('sep', 'Mois séparés')], string=u"Format de fichier",
                             default='sep')
    is_epd = fields.Boolean('EPAD')
    statut_id = fields.Many2one('cmim.statut.assure', string='Statut', domain="[('code', '=', ['ACT', 'EPD'])]")
    payment_date = fields.Date(string=u"Date de réglement")
    collectivite_id = fields.Many2one('res.partner', domain="[('type_entite', '=', 'c')]")
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get())
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 default=lambda self: self._default_journal(),
                                 domain="[('company_id', '=', company_id),('type', '=', 'bank')]", required=True)
    header = fields.Boolean(u'Entête', default=True)
    date_range_id = fields.Many2one('date.range', u'Période',
                                    domain="[('active', '=', True)]", required=True)
    type_id = fields.Many2one('date.range.type', u'Type de péride', domain=lambda self: self._get_domain(),
                              required=True)

    def _get_domain(self):
        return [('active', '=', True),
                ('id', 'in', [self.env.ref('ao_cmim.data_range_type_trimestriel').id,
                              self.env.ref('ao_cmim.data_range_type_mensuel').id])]

    @api.onchange('type_id', 'type_operation', 'model')
    def onchange_type_id(self):
        if self.type_operation == 'declaration':
            if self.model == 'old' and self.type_id:
                return {'domain': {'date_range_id': [('active', '=', True),
                                                     ('type_id', '=', self.type_id.id)]}}
            elif self.model == 'sep':
                return {'domain': {'date_range_id': [('active', '=', True),
                                                     ('type_id', '=',
                                                      self.env.ref('ao_cmim.data_range_type_trimestriel').id)]}}

    def _default_journal(self):
        domain = [
            ('type', '=', 'bank'),
            ('company_id', '=', self.env.user.company_id.id),
        ]
        return self.env['account.journal'].search(domain, limit=1)

    @api.multi
    def import_declarations(self, reader_info):
        declaration_obj = self.env['cmim.declaration']
        partner_obj = self.env['res.partner']
        collectivite_id = self.env['res.partner']
        list_to_import = []
        list_to_anomalie = []
        ids = []
        if self.model == "old":
            for i in range(len(reader_info)):
                values = reader_info[i]
                salaire = float('.'.join(str(x) for x in tuple(values[6].split(','))))
                if not salaire == 0:
                    collectivite_id = collectivite_id.search([('code', '=', values[0])])
                    state = 'valide'
                    if collectivite_id:
                        partner_obj = partner_obj.search([('numero', '=', values[3]), ('type_entite', '=', 'a')])
                        if partner_obj and len(partner_obj) > 1:
                            state = 'non_valide'
                            partner_obj = partner_obj[0]
                        elif not partner_obj:
                            partner_obj = partner_obj.create({'type_entite': 'a',
                                                              'company_type': 'person',
                                                              'customer': True,
                                                              'name': '%s %s' % (values[4], values[5]),
                                                              'id_num_famille': values[2],
                                                              'numero': values[3],
                                                              'import_flag': True,
                                                              })
                        if not declaration_obj.search([('assure_id', '=', partner_obj.id),
                                                       ('collectivite_id', '=', collectivite_id.id),
                                                       ('date_range_id', '=', self.date_range_id.id)]):
                            list_to_import.append({
                                'collectivite_id': collectivite_id.id,
                                'assure_id': partner_obj.id,
                                'nb_jour': values[7],
                                'salaire': salaire,
                                'import_flag': True,
                                'type_id': self.type_id.id,
                                'date_range_id': self.date_range_id.id,
                                'state': state})

        elif self.model == "sep":
            for i in range(len(reader_info)):
                values = reader_info[i]
                partner_obj = partner_obj.search([('numero', '=', values[0])])
                vals = {'collectivite_id': self.collectivite_id.id,
                        'assure_id': partner_obj.id,
                        'import_flag': True,
                        'state': 'valide'
                        }
                if self.type_id.id == self.env.ref('ao_cmim.data_range_type_trimestriel').id:
                    salaire = float('.'.join(str(x) for x in tuple(values[3].split(',')))) + float(
                        '.'.join(str(x) for x in tuple(values[5].split(',')))) + float(
                        '.'.join(str(x) for x in tuple(values[7].split(','))))
                    if not salaire == 0:
                        vals.update({'nb_jour': values[4] + values[6] + values[8],
                                     'salaire': salaire,
                                     'type_id': self.type_id.id,
                                     'date_range_id': self.date_range_id.id,
                                     })
                        list_to_import.append(vals)
                elif self.type_id.id == self.env.ref('ao_cmim.data_range_type_mensuel').id:
                    sal1 = float('.'.join(str(x) for x in tuple(values[3].split(','))))
                    sal2 = float('.'.join(str(x) for x in tuple(values[5].split(','))))
                    sal3 = float('.'.join(str(x) for x in tuple(values[7].split(','))))
                    date_range_ids = self.env['date.range'].search([('active', '=', True),
                                                                    ('type_id', '=', self.type_id.id),
                                                                    ('date_start', '>=', self.date_range_id.date_start),
                                                                    ('date_end', '<=', self.date_range_id.date_end)
                                                                    ],
                                                                   limit=3)
                    if date_range_ids and len(date_range_ids) == 3:
                        if not sal1 == 0:
                            vals.update({'nb_jour': values[4],
                                         'salaire': sal1,
                                         'type_id': self.type_id.id,
                                         'date_range_id': date_range_ids[0].id,
                                         })
                            list_to_import.append(vals)
                        if not sal2 == 0:
                            vals.update({'nb_jour': values[6],
                                         'salaire': sal2,
                                         'type_id': self.type_id.id,
                                         'date_range_id': date_range_ids[1].id,
                                         })
                            list_to_import.append(vals)
                        if not sal3 == 0:
                            vals.update({'nb_jour': values[8],
                                         'salaire': sal3,
                                         'type_id': self.type_id.id,
                                         'date_range_id': date_range_ids[2].id,
                                         })
                            list_to_import.append(vals)
        self.statut_id = self.env.ref('ao_cmim.epd').id if self.is_epd else self.env.ref('ao_cmim.act').id
        print '-------------------',self.statut_id.name
        print 'list_to_import', list_to_import
        # for line in list_to_import:
        #     declaration_obj = declaration_obj.create(line)
        #     has_statut = self.env['cmim.position.statut'].search([('assure_id', '=', declaration_obj.assure_id.id),
        #                                                           ('statut_id', '=', self.statut_id.id)],
        #                                                          limit=1)
        #     if has_statut:
        #         has_statut.write({'date_fin_appl': self.date_range_id.date_end})
        #     else:
        #         declaration_obj.assure_id.write({'position_statut_ids': [(0, 0, {'date_debut_appl': self.date_range_id.date_start,
        #                                          'date_fin_appl': self.date_range_id.date_end,
        #                                          'statut_id': self.statut_id.id,
        #                                          })]})
        #     ids.append(declaration_obj.id)
        if len(ids) > 0:
            view_id = self.env.ref('ao_cmim.declaration_tree_view').id
            return {
                'name': u'Déclarations importées',
                'res_model': 'cmim.declaration',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'view_mode': 'tree,form',
                'views': [(view_id, 'tree'), (False, 'form')],
                'view_id': 'ao_cmim.declaration_tree_view',
                'target': 'self',
                'domain': [('id', 'in', ids)],
            }
        else:
            return True
            ############################################################################

    @api.multi
    def import_reglements(self, reader_info):
        collectivite_obj = self.env['res.partner']
        codes = [int(reader_info[i][0]) for i in range(len(reader_info))]
        list_to_import = []
        ids = []
        account_obj = self.env['account.payment']
        for i in range(len(reader_info)):
            val = {}
            values = reader_info[i]
            collectivite_obj = collectivite_obj.search([('code', '=', values[0])])
            if (collectivite_obj):
                vals = {'partner_id': collectivite_obj.id,
                        'journal_id': self.journal_id.id,
                        'payment_method_id': 1,
                        'payment_type': 'inbound',
                        'partner_type': 'customer',
                        'import_flag': True,
                        'payment_date': self.payment_date,
                        'amount': float('.'.join(str(x) for x in tuple(values[2].split(',')))),

                        }
                list_to_import.append(vals)
        for line in list_to_import:
            account_obj = account_obj.search(
                [('partner_id', '=', line['partner_id']), ('journal_id', '=', line['journal_id']),
                 ('payment_date', '=', line['payment_date'])])
            if not account_obj:
                account_obj = account_obj.create(line)
                ids.append(account_obj.id)
            else:
                account_obj.write(line)

        if len(ids) > 0:
            view_id = self.env.ref('account.view_account_payment_tree').id
            return {
                'name': 'Encaissements importes',
                'res_model': 'account.payment',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'view_mode': 'tree,form',
                'views': [(view_id, 'tree'), (False, 'form')],
                'view_id': 'account.view_account_payment_tree',
                'target': 'self',
                'domain': [('id', 'in', ids)],
            }
            #                 account_obj = self.env['account.payment'].create(vals)
            #                 account_obj.post()

            ############################################################################

    @api.multi
    def import_dec_pay(self):
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
        except Exception:
            raise exceptions.Warning(_(u"Le fichier sélectionné n'est pas valide!"))
        if self.header:
            del reader_info[0]
        if (not self.env['res.partner'].search([('type_entite', '=', 'c')])):
            raise exceptions.Warning(_(
                u"L'import des encaissements exige l'existances des collectivités dans le système, veuillez créer les collectivités en premier"))
        else:
            if self.type_operation == 'declaration':
                return self.import_declarations(reader_info)
            elif self.type_operation == 'reglement':
                return self.import_reglements(reader_info)
