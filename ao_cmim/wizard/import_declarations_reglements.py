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
    type_operation = fields.Selection(selection=[('declaration', u'Déclarations'),
                                         ('reglement', 'Encaissements')],
                                           required=True,
                                           string=u"Type d'opération",
                                           default='declaration')
    model = fields.Selection(selection=[('trim', 'Trimestrielle'), ('sep', 'Mois séparés')], string=u"Périodicité", default='sep')
    payment_date = fields.Date(string=u"Date de réglement")
    
    def _default_journal(self):
        domain = [
            ('type', '=', 'bank'),
            ('company_id', '=', self.env.user.company_id.id),
        ]
        return self.env['account.journal'].search(domain, limit=1)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get())
    journal_id = fields.Many2one('account.journal', string='Journal',
        default=_default_journal, domain="[('company_id', '=', company_id),('type', '=', 'bank')]", required=True)
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
    
    fiscal_date = fields.Integer(string=u"Année Comptable", default= datetime.now().year )
    date_range_id = fields.Many2one('date.range', u'Période')
    
    @api.multi
    def import_declarations(self, reader_info):
        declaration_obj = self.env['cmim.declaration']
        partner_obj = self.env['res.partner']
        collectivite_id = self.env['res.partner']
        list_to_import = []
        ids = []
        statut = self.env['cmim.statut.assure'].search([('code', '=','INACT' )]).id
        assure_obj = self.env['res.partner']
        if(self.model == "trim"):
            for i in range(len(reader_info)):
                values = reader_info[i]
                salaire = float('.'.join(str(x) for x in tuple(values[6].split(','))))
                if(not salaire == 0):
                    collectivite_id = collectivite_id.search([('code', '=', values[0])])
                    state= 'valide'
                    if collectivite_id:
                        partner_obj = partner_obj.search([('id_num_famille', '=', values[2]), ('name', 'like', values[3] )])
                        if partner_obj and len(partner_obj) > 1:
                            state = 'non_valide'
                            partner_obj = partner_obj[0]
                        
                        elif not partner_obj:
                            partner_obj = partner_obj.create({  'is_collectivite': False,
                                                                'company_type' : 'person',
                                                                'customer' : True,
                                                                'name' : '%s' % values[3],
                                                                'id_num_famille' : values[2],
                                                                'import_flag' : True,
                                                                'statut_id' : statut, 
                                                            })
                        if declaration_obj.search([ ('assure_id', '=', partner_obj.id),
                                                    ('collectivite_id' ,'=', collectivite_id.id), 
                                                    ('date_range_id', '=', self.date_range_id.id)]):
                            state = 'non_valide'
                        list_to_import.append({ 
                                'collectivite_id': collectivite_id.id,
                                'assure_id': partner_obj.id,
                                'nb_jour' : values[5],
                                'salaire': salaire,
                                'import_flag': True,
                                'id_used' : 'old',
                                'fiscal_date': self.fiscal_date,
                                'date_range_id': self.date_range_id.id,
                                'state' : state
                                                 })
            print 'list_to_import', len(list_to_import)
            for line in list_to_import:
                declaration_obj = declaration_obj.create(line)
                ids.append(declaration_obj.id)
        elif(self.model == "sep"):
            for i in range(len(reader_info)):
                values = reader_info[i]
                salaire = float('.'.join(str(x) for x in tuple(values[6].split(',')))) + float('.'.join(str(x) for x in tuple(values[8].split(',')))) + float('.'.join(str(x) for x in tuple(values[10].split(','))))
                if(not salaire == 0):
                    collectivite_obj = collectivite_obj.search([('code', '=', value[0])])
                    assure = self.env['res.partner'].search([('numero', '=', values[3])])
                    state = 'valide'
                    if collectivite_obj :
                        if not assure:
                            assure = assure.create({   'is_collectivite': False,
                                                        'company_type' : 'person',
                                                        'customer' : True,
                                                        'id_num_famille' : values[2],
                                                        'numero' : values[3],
                                                        'name' : '%s %s' % (values[4],values[5]),
                                                        'import_flag' : True,
                                                        'statut_id' : statut, 
                                                            })
                        if declaration_obj.search([('assure_id.id', '=', assure.id), 
                                                   ('collectivite_id.id', '=', collectivite_obj.id), 
                                                   ('date_range_id.id', '=', self.date_range_id.id)]):
                            state="non_valide"
                        list_to_import.append({ 'collectivite_id': collectivite_obj.id,
                                                 'assure_id': assure.id,
                                                 'nb_jour' : values[7] + values[9] + values[11],
                                                 'salaire': salaire,
                                                 'import_flag': True,
                                                 'fiscal_date': self.fiscal_date,
                                                 'date_range_id': self.date_range_id.id,
                                                 'state' : state
                                                })
            print 'list_to_import', len(list_to_import)
            for line in list_to_import:
                declaration_obj = declaration_obj.create(line)
                ids.append(declaration_obj.id)
        if len(ids)>0: 
                view_id = self.env.ref('ao_cmim.declaration_tree_view').id
                return{ 
                    'name': u'Déclarations importées',
                    'res_model':'cmim.declaration',
                    'type': 'ir.actions.act_window',
                    'res_id': self.id,
                    'view_mode':'tree,form',
                    'views' : [(view_id, 'tree'),(False, 'form')],
                    'view_id': 'ao_cmim.declaration_tree_view',
                    'target':'self',
                    'domain':[('id', 'in', ids)],
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
            if(collectivite_obj):
                vals = {        'partner_id' : collectivite_obj.id,
                                'journal_id': self.journal_id.id,
                                'payment_method_id' : 1,
                                'payment_type' : 'inbound',
                                'partner_type' : 'customer',
                                'import_flag': True,
                                'payment_date': self.payment_date,
                                'amount' : float('.'.join(str(x) for x in tuple(values[2].split(',')))),
                                
                                }
                list_to_import.append(vals)
        for line in list_to_import:
            account_obj =  account_obj.search([('partner_id', '=', line['partner_id']), ('journal_id', '=', line['journal_id']), ('payment_date', '=', line['payment_date'])])
            if not account_obj:
                account_obj = account_obj.create(line)
                ids.append(account_obj.id)
            else:
                account_obj.write(line)
            
        if len(ids)>0: 
            view_id = self.env.ref('account.view_account_payment_tree').id
            return{ 
                'name': 'Encaissements importes',
                'res_model':'account.payment',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'view_mode':'tree,form',
                'views' : [(view_id, 'tree'),(False, 'form')],
                'view_id': 'account.view_account_payment_tree',
                'target':'self',
                'domain':[('id', 'in', ids)],
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
        del reader_info[0]
        if(not self.env['res.partner'].search([('is_collectivite', '=', True)])):
                raise exceptions.Warning(_(u"L'import des encaissements exige l'existances des collectivités dans le système, veuillez créer les collectivités en premier"))
        else:
            if self.type_operation == 'declaration':
                    return self.import_declarations(reader_info)
            elif self.type_operation == 'reglement':
                    return self.import_reglements(reader_info)
            
