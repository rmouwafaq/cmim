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
    delimeter = fields.Char('Delimeter', default=',',
                            help='Default delimeter is ","')
    type_operation = fields.Selection(selection=[('declaration', 'Declarations'),
                                         ('reglement', 'Encaissements')],
                                           required=True,
                                           string="Type d'operation",
                                           default='declaration')
    model = fields.Selection(selection=[('1', 'Trimestrielle'), ('2', 'Par mois')])
    payment_date = fields.Date(string="Date de reglement")
    
    @api.model
    def _get_domain(self):
        periodes = self.env['date.range'].search([])
        ids = []
        for periode in periodes :
            duree = (datetime.strptime(periode.date_end, '%Y-%m-%d') - datetime.strptime(periode.date_start, '%Y-%m-%d')).days
            if duree > 88 and duree < 92:
                ids.append(periode.id)
        return [('id', 'in', ids)]
    
    @api.onchange('fiscal_date')
    def onchange_field_id(self):
         if self.fiscal_date:
            periodes = self.env['date.range'].search([])
            ids = []
            dec_year = datetime.strptime(self.fiscal_date, '%Y-%m-%d').year
            for periode in periodes :
                duree = (datetime.strptime(periode.date_end, '%Y-%m-%d') - datetime.strptime(periode.date_start, '%Y-%m-%d')).days
                if duree > 88 and duree < 92 and dec_year == datetime.strptime(periode.date_end, '%Y-%m-%d').year and dec_year == datetime.strptime(periode.date_start, '%Y-%m-%d').year:
                    ids.append(periode.id)
            return {'domain':{'date_range_id': [('id', 'in', ids)]}}
    fiscal_date = fields.Date(string="Annee fiscale")
    date_range_id = fields.Many2one('date.range', 'Periode', domain=lambda self: self._get_domain())
    
#############################################################################
    @api.multi
    def import_declarations(self, reader_info):
        if not self.data:
            raise exceptions.Warning(_("Veuillez selectionner le modele de bordereaux"))
        declaration_obj = self.env['cmim.declaration']
        collectivite_obj = self.env['res.partner']
        if(self.model == "1"):
            for i in range(len(reader_info)):
                values = reader_info[i]
                salaire = float('.'.join(str(x) for x in tuple(values[2].split(','))))
                if(not salaire == 0):
                    collectivite_obj = collectivite_obj.search([('code', '=', values[0])])
                    assure = self.env['cmim.assure'].search([('numero', '=', values[1]), ('collectivite_id.id', '=', collectivite_obj.id)])
                    if(assure):
                        if(not declaration_obj.search([('assure_id.id', '=', assure.id), ('fiscal_date', '=', self.fiscal_date), ('date_range_id.id', '=', self.date_range_id.id)])):
                            declaration_obj.create({ 'collectivite_id': collectivite_obj.id,
                                                     'assure_id': assure.id,
                                                     'nb_jour' : values['3'],
                                                     'salaire': salaire,
                                                     'import_flag': True,
                                                     'fiscal_date': self.fiscal_date,
                                                     'date_range_id': self.date_range_id.id
                                                     })
        elif(self.model == "2"):
            collectivite_obj = collectivite_obj.search([('code', '=', reader_info[i][0])])
            del reader_info[0]
            for i in range(len(reader_info)):
                values = reader_info[i]
                salaire = float('.'.join(str(x) for x in tuple(values[1].split(',')))) + float('.'.join(str(x) for x in tuple(values[3].split(',')))) + float('.'.join(str(x) for x in tuple(values[5].split(','))))
                if(not salaire == 0):
                    assure = self.env['cmim.assure'].search([('numero', '=', values[0]), ('collectivite_id.id', '=', collectivite_obj.id)])
                    if(assure):
                        if(not declaration_obj.search([('assure_id.id', '=', assure.id), ('fiscal_date', '=', self.fiscal_date), ('date_range_id.id', '=', self.date_range_id.id)])):
                            declaration_obj.create({ 'collectivite_id': collectivite_obj.id,
                                                     'assure_id': assure.id,
                                                     'nb_jour' : values['2'] + values['4'] + values['6'],
                                                     'salaire': salaire,
                                                     'import_flag': True,
                                                     'fiscal_date': self.fiscal_date,
                                                     'date_range_id': self.date_range_id.id
                                                     })
############################################################################

    @api.multi
    def import_reglements(self, reader_info):
        collectivite_obj = self.env['res.partner']
        codes = [int(reader_info[i][0]) for i in range(len(reader_info))]
        if(not collectivite_obj.search([('code', 'in', codes)])):
            raise exceptions.Warning(
                _("Collectivites inexistantes, verifiez votre fichier"))
        else:
            for i in range(len(reader_info)):
                val = {}
                values = reader_info[i]
                collectivite_obj = collectivite_obj.search([('code', '=', values[0])])
                if(collectivite_obj):
                    vals = {        'partner_id' : collectivite_obj.id,
                                    'journal_id': 6,
                                    'payment_method_id' : 1,
                                    'payment_type' : 'inbound',
                                    'partner_type' : 'customer',
                                    'import_flag': True,
                                    'payment_date': self.payment_date,
                                    'amount' : float('.'.join(str(x) for x in tuple(values[1].split(',')))),
                                    
                                    }
                    account_obj = self.env['account.payment'].create(vals)
                    account_obj.post()

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
            delimeter = ','
        reader = csv.reader(file_input, delimiter=delimeter,
                            lineterminator='\r\n')
        try:
            reader_info.extend(reader)
        except Exception:
            raise exceptions.Warning(_("Le fichier selectionne n'est pas valide!"))
        if self.type_operation == 'declaration':
            if(not self.env['res.partner'].search([('customer', '=', True), ('is_company', '=', True)])):
                raise exceptions.Warning(_("L'import des declarations exige l'existance des collectivites dans le systemes, veuillez creer les collectivites en premier"))
            else:
                return self.import_declarations(reader_info)
        elif self.type_operation == 'reglement':
            if(not self.env['res.partner'].search([('customer', '=', True), ('is_company', '=', True)])):
                raise exceptions.Warning(_("L'import des encaissements exige l'existances des collectivites dans le systemes, veuillez creer les collectivites en premier"))
            else:
                return self.import_reglements(reader_info)
            
