# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import date
from openerp import fields, models, exceptions, api, _
import cStringIO
import datetime
import base64
import StringIO
import csv
to_day  = datetime.datetime.now()
from openerp.exceptions import UserError
###########################################################################

class cmimImportCOlAss(models.TransientModel):
    
    _name = 'cmim.import.col.ass'
    _description = 'Import des donnees'    

    data = fields.Binary("Fichier des données", required=True)
    date_range_id = fields.Many2one('date.range', u'Période')
    delimeter = fields.Char('Delimeter', default=';',
                            help='Default delimeter is ";"')
    filename = fields.Char(string='Filename', size=256, readonly=True)
    csv_data = fields.Binary('csv data')
    type_entite = fields.Selection( selection=[('c', u'Collectivités'),
                                               ('a', u'Assurés'),
                                               ('rsc', u'RSC')],
                                    required=True,
                                    string=u"Type d'entité",
                                    default='c')
    header = fields.Boolean(u'Entête', default=True)
############################################################################

    @api.multi
    def import_collectivites(self, reader_info):
        account_obj = self.env['account.account']
        partner_obj = self.env['res.partner']
        secteur_obj = self.env['cmim.secteur']
        garantie_obj = self.env['cmim.garantie']
        list_col_dict = []
        ids = []
        for i in range(len(reader_info)):
            values = reader_info[i]
            partner_obj = partner_obj.search([('code', '=', values[0])])
            garantie_obj = garantie_obj.search([('code', '=', values[9])])
            if not partner_obj:
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
                    'secteur_id' : secteur_obj.search([('name', '=', values[7])]).id \
                                    or secteur_obj.search([('name', '=', 'DIVERS')]).id,
                    'garantie_id' : garantie_obj.id or None,
                    'siege_id' : self.env['res.partner'].search([('code', '=', values[8])]).id,
                    'date_adhesion' : datetime.datetime.strptime(values[6], "%d/%m/%Y").strftime('%m/%d/%Y') if values[6] else None,
                    'property_account_receivable_id' :account_obj.search([('code', '=', '34222' + values[0] )]).id \
                                                    or  account_obj.create({
                                                                        'name' : values[1] or False,
                                                                        'code' : '34222' + values[0] or False,
                                                                        'user_type_id' : 1,
                                                                        'reconcile' : True,
                                                                        'company_id': self.env['res.users'].search([('id', '=', self._uid)]).company_id.id  
                                                                            }).id,
                    'property_account_payable_id' : account_obj.search([('code', '=', '44111' + values[0])]).id \
                                                    or account_obj.create({
                                                                        'name' : values[1] or False,
                                                                        'code' : '44111' + values[0]  or False,
                                                                        'user_type_id' : 2,
                                                                        'reconcile' : True,
                                                                        'company_id': self.env['res.users'].search([('id', '=', self._uid)]).company_id.id  
                                                                            }).id
                    })
            else:
                partner_obj.write({
                                    'type_entite': 'c',
                                    'garantie_id' : garantie_obj.id or None,
                                    'secteur_id' : secteur_obj.search([('name', '=', values[7])]).id or None,
                                    'siege_id' : self.env['res.partner'].search([('code', '=', values[8])]).id or None,
                                })
        for col in list_col_dict:
            partner_obj = partner_obj.create(col)
            ids.append(partner_obj.id)
        return ids
############################################################################

    @api.multi
    def import_assures(self, reader_info):
        list_assure_dict = []
        list_anomalie = []
        ids = []
        partner_obj = self.env['res.partner']
        for i in range(len(reader_info)):
            values = reader_info[i]
            partner_obj = partner_obj.search([('numero', '=', values[1])], limit=1)
            statut_id = self.env['cmim.statut.assure'].search([('code', '=', values[5])])
            if not partner_obj and statut_id:
                vals = {
                        'type_entite': self.type_entite,
                        'lib_qualite': values[4],
                        'company_type': 'person',
                        'customer': True,
                        'name': '%s %s' % (values[2], values[3]),
                        'prenom': '%s' % (values[3]),
                        'numero': values[1],
                        'sexe': values[6],
                        'id_num_famille' : values[0],
                        'import_flag' : True,
                        'position_statut_ids': [(0,0,{'date_debut_appl' : self.date_range_id.date_start,
                                             'date_fin_appl' : self.date_range_id.date_end,
                                             'statut_id' : statut_id.id,
                                             })]}
                if self.type_entite == 'rsc':
                        sexe = 'F' if vals.get('sexe') == 'M' else 'M'
                        epoux_id = partner_obj.search([("id_num_famille", '=',  values[0]),
                                                       ("type_entite", '=', 'a'),
                                                       ("sexe", '=', sexe)]
                                                      , limit=1)
                        if epoux_id:
                            vals.update({'epoux_id': epoux_id.id})
                            list_assure_dict.append(vals)
                        else:
                            values.append('Epoux(se) inconnu')
                            list_anomalie.append(values)
                else:
                    list_assure_dict.append(vals)
            elif partner_obj:
                vals = {'lib_qualite': values[4], 'sexe': values[6], 'type_entite': self.type_entite}
                has_statut = self.env['cmim.position.statut'].search([('assure_id', '=', partner_obj.id ),
                                                                     ('statut_id', '=', statut_id.id)],
                                                                     limit=1)
                if has_statut:
                    has_statut.write({'date_fin_appl': self.date_range_id.date_end})
                else:
                    vals.update({'position_statut_ids': [(0, 0, {'date_debut_appl': self.date_range_id.date_start,
                                                                 'date_fin_appl': self.date_range_id.date_end,
                                                                 'statut_id': statut_id.id,
                                                                 })]})
            else:
                values.append('Statut inconnu')
                list_anomalie.append(values)
            partner_obj.write(vals)
        for val in list_assure_dict:
            partner_obj = partner_obj.create(val)
            if partner_obj:
                ids.append(partner_obj.id)
        if len(list_anomalie) > 0:
            file = StringIO.StringIO()
            w = csv.writer(file, delimiter=';')
            for row in list_anomalie:
                w.writerow(row)
            content_value = file.getvalue()
            self.write({
                'csv_data': base64.encodestring(content_value),
                'filename': self.date_range_id.date_start + '_' + self.date_range_id.date_end + '.csv'
            })
            file.close()
            action = {
                'name': 'payment',
                'type': 'ir.actions.act_url',
                'url': "web/content/?model=cmim.import.col.ass&id=" + str(self.id)
                       + "&filename_field=filename&field=csv_data&download=true&filename=" + self.filename,
                'target': 'new'
            }
            return action
        elif len(ids) > 0:
            view_id = self.env.ref('ao_cmim.view_assure_tree').id
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
        if self.header:
            del reader_info[0]
        if self.type_entite == 'c':
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
            return self.import_assures(reader_info)
