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
    data_contrat = fields.Binary("Fichier relation d'adhesion")
    delimeter = fields.Char('Delimeter', default=',',
                            help='Default delimeter is ";"')
    type_entite = fields.Selection(selection=[('collectivite', 'Collectivites'),
                                         ('assure', 'Assures')],
                                           required=True,
                                           string="Type d'entite",
                                           default='collectivite')
       
############################################################################

    @api.multi
    def import_collectivites(self, reader_info , reader_info2):
        account_obj = self.env['account.account']
        partner_obj = self.env['res.partner']
        codes = []
        anomalies = []
        for i in range(len(reader_info)):
            values = reader_info[i]
            codes.append(values[0])            
            if(partner_obj.search([('code', '=', values[0])])):
                anomalies.append(values[0])
        else:
            adhesion_codes = []
            for i in range(len(reader_info)):
                values = reader_info[i]
                if (values[0] not in adhesion_codes):
                    adhesion_codes.append(values[0])
            i = 0
            while i < len(codes) :
                if codes[i] not in adhesion_codes:
                    anomalies.append(values[0])
                else:
                    i = i + 1
            for i in range(len(reader_info)):
                val = {}
                values = reader_info[i]
                if(not partner_obj.search([('code' , '=', values[1])])):
                    val['code'] = values[0]
                    val['name'] = values[1]
                    val['street'] = values[2] or ''
                    val['city'] = values[3] or ''
                    val['phone'] = values[4] or ''
                    val['fax'] = values[5] or ''
                    val['import_flag'] = True
                    #COLLECTIVITE MERE
                    if (not values[8] == ""):
                        partner_obj = self.env['res.partner'].search([('code', '=', values[8])])
                        if partner_obj:
                            val['parent_id'] = partner_obj.id
                    secteur = self.env['cmim.secteur'].search([('name', 'like', values[7])])
                    if(secteur):
                        val['secteur_id'] = secteur.id
                    else: 
                        val['secteur_id'] = self.env['cmim.secteur'].search([('name', 'like', 'DIVERS')]).id
                    try:
                        val['date_adhesion'] = datetime.strptime(values[6], "%d/%m/%Y").strftime('%m/%d/%Y')
                        # datetime.today().strftime('%m/%d/%Y')
                        # datetime.strptime(values["Date d'adhesion"], "%d/%m/%Y").date()
                    except Exception:
                        val['date_adhesion'] = datetime.today().strftime('%m/%d/%Y')
                    code = '34222' + values[0]   
                    account_obj = account_obj.search([('code', '=', code)])
                    if not account_obj:
                        data = {
                                    'name' : values[1] or False,
                                    'code' : code  or False,
                                    'user_type_id' : 1,
                                    'reconcile' : True,
                                    'company_id': self.env['res.users'].search([('id', '=', self._uid)]).company_id.id  
                                        }
                        account_obj = account_obj.create(data)
                    val['property_account_receivable_id'] = account_obj.id or False
                    code = '44111' + values[0]
                    account_obj = account_obj.search([('code', '=', code)])
                    if not account_obj:
                        data = {
                                    'name' : values[1] or False,
                                    'code' : code  or False,
                                    'user_type_id' : 2,
                                    'reconcile' : True,
                                    'company_id': self.env['res.users'].search([('id', '=', self._uid)]).company_id.id  
                                        }
                        account_obj = account_obj.create(data)
                    val['property_account_payable_id'] = account_obj.id or False
                    partner_obj.create(val)
                # creation des contrat
            contrat_obj = self.env['cmim.contrat']
            tarif_obj = self.env['cmim.tarif']
            type_product_id = self.env['cmim.product.type']
            for i in range(len(reader_info2)):
                val = {}
                values = reader_info2[i]
                collectivite = self.env['res.partner'].search([('code', 'like', values[0])])
                product = self.env['product.template'].search([('name', 'ilike', values[4][0:4])])
                val['collectivite_id'] = collectivite.id
                val['product_id'] = product.id
                val['name'] = 'Adhesion %s / %s' % (collectivite.name, product.name)
                val['code'] = values[2]
                val['import_flag'] = True
                mt = float(values[5].replace(',','.',1))
                if mt!=0:
                    tarif_obj = self.env['cmim.tarif'].search([('type', '=', values[3].lower()), ('montant', '=', mt)])
                    if(not tarif_obj):
                        name= "%s" %mt
                        if(values[3].lower() == 'p'):
                            name="%s %%" %(mt)
                        val['tarif_id'] = tarif_obj.create({'name': name,
                                                          'type': values[3].lower(),
                                                          'import_flag' : True,
                                                          'montant':mt
                                                          }).id
                    else:
                        val['tarif_id'] = tarif_obj.id
                    val['type_product_id'] = type_product_id.search([('short_name', '=','MAL')]).id
                else:
                    #mt = float('.'.join(str(x) for x in tuple(values[8].split(','))))
                    mt = float(values[8].replace(',','.',1))
                    tarif_obj = self.env['cmim.tarif'].search([('type', '=', 'p'), ('montant', '=', mt)])
                    if(not tarif_obj):
                        val['tarif_inc_deces_id'] = tarif_obj.create({
                                                          'name': "%s %%" %(mt),
                                                          'montant': mt
                                                          }).id
                    else:
                        val['tarif_inc_deces_id'] = tarif_obj.id
                        
                    #mt = float('.'.join(str(x) for x in tuple(values[9].split(','))))
                    mt = float(values[9].replace(',','.',1))
                    tarif_obj = self.env['cmim.tarif'].search([('type', '=', values[3].lower()), ('montant', '=', mt)])
                    if(not tarif_obj):
                        val['tarif_inv_id'] = tarif_obj.create({
                                                          'name': "%s %%" %(mt),
                                                          'import_flag' : True,
                                                          'montant':mt
                                                          }).id
                    else:
                        val['tarif_inv_id'] = tarif_obj.id
                    val['type_product_id'] = type_product_id.search([('short_name', '=','PRV')]).id
                collectivite.write({'contrat_ids':   [(0, 0, val)]})
                product.write({"type_product_ids": [4,type_product_id.id]})
        if  not anomalies :
            return True
        else:
            warning_msg = _("Les Collectivites suivantes sont existantes ou n'ont pas de relation d'adhesion definie:")
            i = 0
            while i < len(anomalies):
                warning_msg += '\n- %s' % (anomalies[i])
                i = i + 1
            raise UserError(warning_msg)
        # return True

############################################################################

    @api.multi
    def import_assures(self, reader_info):

        assure_obj = self.env['cmim.assure']
        for i in range(len(reader_info)):
            val = {}
            values = reader_info[i]
            if(not assure_obj.search([('numero', '=', values[3])])):
                collectivite_obj = self.env['res.partner'].search([('code', '=', values[0])])
                if(collectivite_obj):
                    val['collectivite_id'] = collectivite_obj.id
                    val['name'] = '%s %s' % (values[4], values[5])
                    val['numero'] = values[3]
                    epoux_obj = self.env['cmim.assure'].search([("id_num_famille", '=', values[2])])
                    if(epoux_obj):
                        val['epoux_id'] = epoux_obj.id
                    val['id_num_famille'] = values[2]
                    val['import_flag'] = True
                    try:
                        val['date_naissance'] = datetime.strptime(values[7], "%d/%m/%Y").date()
                    except Exception:
                        val['date_naissance'] = None
                        
                    if(values[4].upper() == 'RETRAITE'):
                        val['statut'] = 'retraite'
                    if(values[4].upper() == 'INVALIDE'):
                        val['statut'] = 'invalide'
                    assure_obj = assure_obj.create(val)
                    epoux_obj.write({'epoux_id':assure_obj.id})
        return True
###########################################################################
    @api.multi
    def import_col_assure(self):
        if not self.data:
                raise exceptions.Warning(_("Le fichier est obligatoire!"))
        # Decode the file data
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
        if self.type_entite == 'collectivite':
            if(not self.env['product.template'].search([])):
                raise exceptions.Warning(_("L'import des collectivites ne peut avoir lieu si aucun produits n'est defini, veuillez creer les produits en premier"))
            else:
                if not self.data_contrat:
                    raise exceptions.Warning(_("Le fichier relation des adhesions est obligatoire!"))
                # Decode the file data_contrat
                data_contrat = base64.b64decode(self.data_contrat)
                file_input = cStringIO.StringIO(data_contrat)
                file_input.seek(0)
                reader_info2 = []
                if self.delimeter:
                    delimeter = str(self.delimeter)
                else:
                    delimeter = ','
                reader = csv.reader(file_input, delimiter=delimeter,
                                    lineterminator='\r\n')
                try:
                    reader_info2.extend(reader)
                except Exception:
                    raise exceptions.Warning(_("Not a valid file!"))
                return self.import_collectivites(reader_info , reader_info2)
        else:
            
            if self.type_entite == 'assure':
                if(not self.env['res.partner'].search([('customer', '=', True), ('is_company', '=', True)])):
                    raise exceptions.Warning(_("L'import des associes exige l'existances des collectivites dans le systemes, veuillez creer les collectivites en premier"))
                else:
                    return self.import_assures(reader_info)
                
                
                
                        