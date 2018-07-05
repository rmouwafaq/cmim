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

class cmimImportDecPay(models.TransientModel):
    _name = 'cmim.import.dec.pay'

    data = fields.Binary("Fichier", required=True)
    delimeter = fields.Char('Delimeter', default=';',
                            help='Default delimeter is ";"')
    type_operation = fields.Selection(selection=[('declaration', u'Déclarations'), ('reglement', 'Encaissements')],
                                      required=True, string=u"Type d'opération", default='declaration')
    model = fields.Selection(selection=[('old', 'Ancien Format'), ('sep', 'Mois séparés')], string=u"Format de fichier",
                             default='sep')
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
    type_id = fields.Many2one('date.range.type', u'Type de péride', default=lambda self: self.env.ref('ao_cmim.data_range_type_trimestriel').id,
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
        list_to_import = []
        list_to_anomalie = []

        ids = []

        dates = []
        if self.date_range_id.child_id and len(self.date_range_id.child_id) == 3:
            for i in range(3):
                dates.append(self.date_range_id.child_id[i])

        self.check_declaration(self.collectivite_id,self.date_range_id)

        for i in range(len(reader_info)):
            values = reader_info[i]
            data = [{'date':dates[0] ,'salaire': values[5], 'nb_jour': values[6]},
                    {'date':dates[1] ,'salaire': values[7], 'nb_jour': values[8]},
                    {'date':dates[2] ,'salaire': values[9], 'nb_jour': values[10]}
                    ]

            # values[0] = int(values[0].replace(" ", ""))
            partner_obj = partner_obj.search([('numero', '=', values[0])])

            if not partner_obj:
                partner_obj = partner_obj.create({'type_entite': 'a',
                                                  'company_type': 'person',
                                                  'customer': True,
                                                  'name': '%s %s' % (values[1], values[2]),
                                                  'id_num_famille': '',
                                                  'numero': values[0],
                                                  'import_flag': True,
                                                  })

            vals = {'collectivite_id': self.collectivite_id.id,
                    'assure_id': partner_obj[0].id,
                    'import_flag': True,
                    'state': 'valide'
                    }

            for item in data:
                values ={}
                salaire = float(item['salaire'].strip() or 0)
                nb_jour = int(item['nb_jour'].strip() or 0)
                nb_jour_prorata = 0
                if nb_jour > 0:
                    nb_jour_prorata = nb_jour_prorata + 30

                values.update({'nb_jour': nb_jour,
                             'salaire': salaire ,
                             'type_id': item['date'].type_id.id,
                             'date_range_id': item['date'].id,
                             'nb_jour_prorata':nb_jour_prorata,
                             })

                list_to_import.append(dict(vals.items() + values.items()))

        #self.statut_id = self.env.ref('ao_cmim.epd').id if self.is_epd else self.env.ref('ao_cmim.act').id
        self.statut_id = self.env.ref('ao_cmim.act').id

        for line in list_to_import:
            declaration = declaration_obj.create(line)
            has_statut = self.env['cmim.position.statut'].search([('assure_id', '=', declaration.assure_id.id),
                                                                  ('statut_id', '=', self.statut_id.id)],
                                                                 limit=1)
            if has_statut:
                has_statut.write({'date_fin_appl': self.date_range_id.date_end})
            else:
                declaration.assure_id.write(
                    {'position_statut_ids': [(0, 0, {'date_debut_appl': self.date_range_id.date_start,
                                                     'date_fin_appl': self.date_range_id.date_end,
                                                     'statut_id': self.statut_id.id,
                                                     })]})
            ids.append(declaration.id)

        if list_to_anomalie:
            logging.info('Assures abscents : %s ', list_to_anomalie)
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

    @api.multi
    def check_declaration(self,collectivite,periode):
        """ Fonction pour supprimer les anciennes declarations sur la meme période"""
        declarations = self.env['cmim.declaration'].search([('collectivite_id.id', '=', collectivite.id),
                                                               ('date_range_id.date_start', '>=',periode.date_start),
                                                               ('date_range_id.date_end', '<=',periode.date_end),
                                                               ('cotisation_id', '=', None),
                                                               ('state', '=', 'valide')])
        if declarations:
            declarations.unlink()
