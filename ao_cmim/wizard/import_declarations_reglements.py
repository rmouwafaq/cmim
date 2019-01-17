# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import date
from openerp import fields, models, exceptions, api, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import base64
import csv
import cStringIO
from openerp.exceptions import UserError
import logging



#############################################################################

class cmimImportDecPay(models.TransientModel):
    _name = 'cmim.import.dec.pay'

    data = fields.Binary("Fichier", required=True)
    delimeter = fields.Char('Séparateur', default=';',
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
                                    domain="[('active', '=', True)]")
    type_id = fields.Many2one('date.range.type', u'Type de péride', default=lambda self: self.env.ref('ao_cmim.data_range_type_mensuel').id,
                              required=True)
    nombre_lignes = fields.Integer('N° Lignes')

    def _get_domain(self):
        return [('active', '=', True),
                ('id', 'in', [self.env.ref('ao_cmim.data_range_type_trimestriel').id,
                              self.env.ref('ao_cmim.data_range_type_mensuel').id])]

    # @api.onchange('type_id', 'type_operation', 'model')
    # def onchange_type_id(self):
    #     if self.type_operation == 'declaration':
    #         if self.model == 'old' and self.type_id:
    #             return {'domain': {'date_range_id': [('active', '=', True),
    #                                                  ('type_id', '=', self.type_id.id)]}}
    #         elif self.model == 'sep':
    #             return {'domain': {'date_range_id': [('active', '=', True),
    #                                                  ('type_id', '=',
    #                                                   self.env.ref('ao_cmim.data_range_type_trimestriel').id)]}}

    @api.onchange('data')
    def onchange_file(self):
        if self.type_operation == 'declaration':
            if self.data:
                reader = self.read_file()
                partner_obj = self.env['res.partner']
                date_range_obj = self.env['date.range']
                if reader:
                    entete = filter(lambda p: p[0] == 'ENTCHGSAL', reader)[0]
                    recap = filter(lambda p: p[0] == 'RECCHGSAL', reader)[0]
                    collectivite = partner_obj.search([('code','=',entete[1])])
                    self.collectivite_id = collectivite.id if collectivite else False
                    self.collectivite_id = collectivite.id if collectivite else partner_obj.create({'code':entete[1],
                                                                                                    'name':entete[1],
                                                                                                    'type_entite':'c',
                                                                                                    'company_type':'company'})
                    reader_date = datetime.strptime(entete[2], '%d/%m/%Y').date()
                    format_date = reader_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    date_range = date_range_obj.search([('type_id','=',self.env.ref('ao_cmim.data_range_type_mensuel').id),
                                                        ('date_start','<=',format_date),
                                                        ('date_end','>=',format_date),
                                                        ])
                    self.date_range_id = date_range.id if date_range else None
                    self.nombre_lignes = recap[1]
            else:
                self.collectivite_id =  None
                self.date_range_id = None



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
            if values[0] == 'LIGCHGSAL':
                if self.type_id.name == 'Trimestriel':
                    data = [{'date':dates[0] ,'salaire': values[5], 'nb_jour': values[6]},
                            {'date':dates[1] ,'salaire': values[7], 'nb_jour': values[8]},
                            {'date':dates[2] ,'salaire': values[9], 'nb_jour': values[10]}
                            ]
                else:
                    data = [{'date': self.date_range_id, 'nb_jour': values[6], 'salaire': values[7]}
                            ]

                # values[0] = int(values[0].replace(" ", ""))
                partner = partner_obj.search([('numero', '=', values[1])],limit=1)

                if not partner:
                    partner = partner_obj.create({'type_entite': 'a',
                                                      'company_type': 'person',
                                                      'customer': True,
                                                      'name': '%s %s' % (values[2], values[3]),
                                                      'id_num_famille': '',
                                                      'numero': values[1],
                                                      'import_flag': True,
                                                      })

                vals = {'collectivite_id': self.collectivite_id.id,
                        'assure_id': partner.id,
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
                                 'salaire': salaire/100 ,
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
        # codes = [int(reader_info[i][0]) for i in range(len(reader_info))]
        list_to_import = []
        ids = []
        account_obj = self.env['account.payment']
        for i in range(len(reader_info)):
            val = {}
            values = reader_info[i]
            collectivite = collectivite_obj.search([('code', '=', values[3])])
            payment_date = date(int(values[2]),int(values[1]),int(values[0]))
            if (collectivite):
                vals = {'partner_id': collectivite.id,
                        'journal_id': self.journal_id.id,
                        'payment_method_id': 1,
                        'payment_type': 'inbound',
                        'partner_type': 'customer',
                        'import_flag': True,
                        'payment_date': payment_date,
                        'communication':values[4],
                        'amount': float('.'.join(str(x).replace(" ", "") for x in tuple(values[5].split(',')))),

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
    def read_file(self):
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

        if (not self.env['res.partner'].search([('type_entite', '=', 'c')])):
            raise exceptions.Warning(_(
                u"L'import des encaissements exige l'existances des collectivités dans le système, veuillez créer les collectivités en premier"))

        return reader_info

    @api.multi
    def import_dec_pay(self):
        reader_info = self.read_file()
        if self.type_operation == 'declaration':
            return self.import_declarations(reader_info)
        elif self.type_operation == 'reglement':
            reader_info.pop(0)
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
