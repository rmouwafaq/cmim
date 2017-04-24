# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import date
from openerp import fields, models, exceptions, api, _
import base64
import csv
import cStringIO
import locale
from openerp.exceptions import UserError
###########################################################################

class cmimImportCOlAss(models.TransientModel):
    
    _name = 'cmim.import.col.ass'
    _description = 'Import des donnees'    

    data = fields.Binary("Fichier de l'objet", required=True)
    delimeter = fields.Char('Delimeter', default=';',
                            help='Default delimeter is ";"')
    type_entite = fields.Selection(selection=[('collectivite', 'Collectivites'),
                                         ('assure', 'Assures')],
                                           required=True,
                                           string="Type d'entite",
                                           default='collectivite')
       
############################################################################

    @api.multi
    def import_collectivites(self, reader_info):
        account_obj = self.env['account.account']
        partner_obj = self.env['res.partner']
        list_col_dict = []
        for i in range(len(reader_info)):
            values = reader_info[i]
            if not partner_obj.search([('code' , '=', values[1])]):
#                 account_obj = account_obj.search([('code', '=', '34222' + values[0] )])
#                 if  account_obj:
#                     receivable = account_obj.id
#                 else
                list_col_dict.append({
                    'code' : values[0],
                    'name' : values[1],
                    'street' : values[2] or '',
                    'city' : values[3] or '',
                    'phone' : values[4] or '',
                    'fax' : values[5] or '',
                    'import_flag' : True,
                    'secteur_id' : self.env['cmim.secteur'].search([('name', '=', values[7])]).id \
                                    or self.env['cmim.secteur'].search([('name', '=', 'DIVERS')]).id,
                    'siege_id' : self.env['res.partner'].search([('code', '=', values[8])]).id,
                    'date_adhesion' : datetime.strptime(values[6], "%d/%m/%Y").strftime('%m/%d/%Y') if values[6] else None,
                    'property_account_receivable_id' :account_obj.search([('code', '=', '34222' + values[0] )]).id or  account_obj.create({
                                                                                                                                            'name' : values[1] or False,
                                                                                                                                            'code' : '34222' + values[0] or False,
                                                                                                                                            'user_type_id' : 1,
                                                                                                                                            'reconcile' : True,
                                                                                                                                            'company_id': self.env['res.users'].search([('id', '=', self._uid)]).company_id.id  
                                                                                                                                                }).id,
                    'property_account_payable_id' : account_obj.search([('code', '=', '44111' + values[0])]).id or account_obj.create({
                                                                                                                                            'name' : values[1] or False,
                                                                                                                                            'code' : '44111' + values[0]  or False,
                                                                                                                                            'user_type_id' : 2,
                                                                                                                                            'reconcile' : True,
                                                                                                                                            'company_id': self.env['res.users'].search([('id', '=', self._uid)]).company_id.id  
                                                                                                                                                }).id
                    })
        for col in list_col_dict:
            partner_obj.create(col)
############################################################################

    @api.multi
    def import_assures(self, reader_info):
        list_assure_dict = []
        assure_obj = self.env['cmim.assure']
        collectivite_obj = self.env['res.partner']
        for i in range(len(reader_info)):
            values = reader_info[i]
            if(not assure_obj.search([('numero', '=', values[3]),('collectivite_id.code', '=', values[0])])):
                list_assure_dict.append({
                                        'collectivite_id' : collectivite_obj.search([('code', '=', values[0])]).id,
                                        'name' : '%s %s' % (values[5], values[6]),
                                        'numero' : values[3],
                                        'epoux_id' : assure_obj.search([("id_num_famille", '=', values[2])], limit=1).id or None,
                                        'id_num_famille' : values[2],
                                        'import_flag' : True,
                                        'date_naissance' : datetime.strptime(values[7], "%d/%m/%Y").date() or None,
                                        'statut_id' : self.env['cmim.statut.assure'].search([('code', '=',values[4] )]).id \
                                                    or self.env['cmim.statut.assure'].search([('code', '=','ACT' )]).id 
                })
        for val in list_assure_dict:
            assure_obj = assure_obj.create(val)
            assure_obj.epoux_id.write({'epoux_id':assure_obj.id})
                    
###########################################################################
    @api.multi
    def import_col_assure(self):
        if not self.data:
                raise exceptions.Warning(_("Le fichier est obligatoire!"))
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
            raise exceptions.Warning(_(u"Le fichier selectionné n'est pas valide!"))
        del reader_info [0]
        if self.type_entite == 'collectivite':
            return self.import_collectivites(reader_info)
        elif(not self.env['res.partner'].search([('customer', '=', True), ('is_company', '=', True)])):
            raise exceptions.Warning(_(u"L'import des assurés exige l'existances des collectivités dans le système, veuillez créer les collectivités en premier"))
        else:
            return self.import_assures(reader_info)
            
                
                
                        
