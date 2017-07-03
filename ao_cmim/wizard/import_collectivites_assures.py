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

    data = fields.Binary("Fichier des données", required=True)
    delimeter = fields.Char('Delimeter', default=';',
                            help='Default delimeter is ";"')
    type_entite = fields.Selection(selection=[('collectivite', u'Collectivités'),
                                         ('assure', u'Assurés')],
                                           required=True,
                                           string=u"Type d'entité",
                                           default='collectivite')
       
############################################################################

    @api.multi
    def import_collectivites(self, reader_info):
        account_obj = self.env['account.account']
        partner_obj = self.env['res.partner']
        list_col_dict = []
        ids = []
        for i in range(len(reader_info)):
            values = reader_info[i]
            if not partner_obj.search([('code' , '=', values[1])]):
                list_col_dict.append({
                    'type_entite': 'c',
                    'company_type' : 'company',
                    'customer' : True,
                    'is_company' : True,
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
            partner_obj = partner_obj.create(col)
            ids.append(partner_obj.id)
        return ids
############################################################################

    @api.multi
    def import_assures(self, reader_info):
        list_assure_dict = []
        ids = []
        partner_obj = self.env['res.partner']
        collectivite_obj = self.env['res.partner']
        for i in range(len(reader_info)):
            values = reader_info[i]
            if not partner_obj.search([('numero', '=', values[1])]):
                list_assure_dict.append({
                                        'type_entite': 'a',
                                        'company_type' : 'person',
                                        'customer' : True,
                                        'name' : '%s %s' % (values[2], values[3]),
                                        'prenom' : '%s' % (values[3]),
                                        'numero' : values[1],
                                        'id_num_famille' : values[0],
                                        'import_flag' : True,
                                        'statut_id' : self.env['cmim.statut.assure'].search([('code', '=',values[4] )]).id \
                                                    or self.env['cmim.statut.assure'].search([('code', '=','ACT' )]).id 
                })
        for val in list_assure_dict:
            partner_obj = partner_obj.create(val)
            ids.append(partner_obj.id)
        return ids
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
            view_id = self.env.ref('ao_cmim.view_collectivite_tree').id
            ids = self.import_collectivites(reader_info)
            if len(ids) > 0:
                return{ 'name' : u'Collectivités Importées',
                        'res_model':'res.partner',
                        'type': 'ir.actions.act_window',
                        'res_id': self.id,
                        'view_mode':'tree,form',
                        'views' : [(view_id, 'tree'), (False, 'form')],
                        'view_id': 'ao_cmim.view_collectivite_tree',
                        'domain':[('id', 'in', ids)],
                        'target':'self',
                        }
            else:
                return True
        elif(not self.env['res.partner'].search([('type_entite', '=', 'c')])):
            raise exceptions.Warning(_(u"L'import des assurés exige l'existances des collectivités dans le système, veuillez créer les collectivités en premier"))
        else:
            view_id = self.env.ref('ao_cmim.view_assure_tree').id
            ids = self.import_assures(reader_info)
            if len(ids) > 0:
                return{ 'name' : u'Assurés Importés',
                        'res_model':'res.partner',
                        'type': 'ir.actions.act_window',
                        'res_id': self.id,
                        'view_mode':'tree,form',
                        'views' : [(view_id, 'tree'), (False, 'form')],
                        'view_id': 'ao_cmim.view_assure_tree',
                        'domain':[('id', 'in', ids)],
                        'target':'self',
                        }
            else:
                return True
                
                
                        
