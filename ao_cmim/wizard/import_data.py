from datetime import datetime
from datetime import date
from openerp import fields, models, exceptions, api, _
import base64
import csv
import cStringIO
from openerp.exceptions import UserError
###################################################################################################

class cmim_import(models.TransientModel):
    
    _name = 'cmim.import'
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
    type_operation = fields.Selection(selection=[('declaration', 'Declarations'),
                                         ('reglement', 'Encaissements')],
                                           required=True,
                                           string="Type d'operation",
                                           default='declaration')
    categ_id = fields.Many2one('product.category', ' Categorie', change_default=True, domain="[('type','=','normal')]" , help="Select category for the current product")
    payroll_year_id = fields.Many2one('py.year', 'Calendrier')
    payroll_period_id = fields.Many2one('py.period', 'Periode', domain="[('payroll_year_id','=',payroll_year_id)]")


        
############################################################################

    @api.multi
    def import_collectivites(self, reader_info, keys , reader_info2, keys2):
        # check if keys exist for first file
        if not isinstance(keys, list) or ('CODE COLLECTIVITE' not in keys) or ("DATE ADHESION" not in keys) or ('SECTEUR' not in keys) or ('COLLECTIVITE MERE' not in keys):
            raise exceptions.Warning(
                _("Verifiez l entete de votre fichier d'adherents"))
        
        # check if keys exist
        values = dict(zip(keys, reader_info[0])) 
        if not isinstance(keys2, list) or ('CODE COLLECTIVITE' not in keys2) or('TYPE TARIF' not in keys2) or ('TARIF' not in keys2) or ('TARIF INC DEC' not in keys2) or ('TARIF INV' not in keys2) or ('CODE PRODUIT' not in keys2):
            raise exceptions.Warning(
                _("Verifiez l entete du fichier relations d'adhesion"))
            
        account_obj = self.env['account.account']
        partner_obj = self.env['res.partner']
        codes = []
        anomalies = []
        
        for i in range(len(reader_info)):
            field = reader_info[i]
            values = dict(zip(keys, field))  
            codes.append(values['CODE COLLECTIVITE'])
            
        if(partner_obj.search([('code', '=', values['CODE COLLECTIVITE'])])):
            anomalies.append(values['CODE COLLECTIVITE'])
        else:
            adhesion_codes = []
            for i in range(len(reader_info)):
                field = reader_info[i]
                values = dict(zip(keys, field))  
                if (values['CODE COLLECTIVITE'] not in adhesion_codes):
                    adhesion_codes.append(values['CODE COLLECTIVITE'])
            i = 0
            while i < len(codes) :
                if codes[i] not in adhesion_codes:
                    anomalies.append(values['CODE COLLECTIVITE'])
                else:
                    i = i + 1
            for i in range(len(reader_info)):
                val = {}
                field = reader_info[i]
                values = dict(zip(keys, field)) 
                if(not partner_obj.search([('code' , '=', values['CODE COLLECTIVITE'])])):
                    val['code'] = values['CODE COLLECTIVITE']
                    val['name'] = values['RAISON SOCIALE']
                    val['street'] = values['ADRESSE'] or ''
                    val['phone'] = values['TELEPHONE'] or ''
                    val['fax'] = values['FAX'] or ''
                    val['import_flag'] = True
                    if (not values['COLLECTIVITE MERE'] == ""):
                        partner_obj = self.env['res.partner'].search([('code', '=', values['COLLECTIVITE MERE'])])
                        if partner_obj:
                            val['parent_id'] = partner_obj.id
                    secteur = self.env['cmim.secteur'].search([('name', 'like', values['SECTEUR'])])
                    if(secteur):
                        val['secteur_id'] = secteur.id
                    else: 
                        val['secteur_id'] = self.env['cmim.secteur'].search([('name', 'like', 'DIVERS')]).id
                    val['city'] = values['VILLE']
                    try:
                        val['date_adhesion'] = datetime.strptime(values["DATE ADHESION"], "%d/%m/%Y").strftime('%m/%d/%Y')
                        # datetime.today().strftime('%m/%d/%Y')
                        # datetime.strptime(values["Date d'adhesion"], "%d/%m/%Y").date()
                    except Exception:
                        val['date_adhesion'] = datetime.today().strftime('%m/%d/%Y')
                    code = '34222' + values['CODE COLLECTIVITE']   
                    # account_type_obj = self.env['account.account.type'].search[('name', 'like', 'receivable')]
                    data = {
                                'name' : 'Compte_CLT' + values['RAISON SOCIALE'] or False,
                                'code' : code  or False,
                                'user_type_id' : 1,
                                'reconcile' : True,
                                'company_id': self.env['res.users'].search([('id', '=', self._uid)]).company_id.id  
                                    }
                    account_obj.create(data)
                    val['property_account_receivable_id'] = account_obj.search([('code', '=', code)]).id or False
                    code = '44111' + values['CODE COLLECTIVITE']
                    data = {
                                'name' : 'Compte_FRS' + values['RAISON SOCIALE'] or False,
                                'code' : code  or False,
                                'user_type_id' : 2,
                                'reconcile' : True,
                                'company_id': self.env['res.users'].search([('id', '=', self._uid)]).company_id.id  
                                    }
                    account_obj.create(data)
                    val['property_account_payable_id'] = account_obj.search([('code', '=', code)]).id or False
                    partner_obj.create(val)
                # creation des contrat
            contrat_obj = self.env['cmim.contrat']
            tarif_obj = self.env['cmim.tarif']
            for i in range(len(reader_info2)):
                val = {}
                field = reader_info2[i]
                values = dict(zip(keys2, field))  
                collectivite = self.env['res.partner'].search([('code', 'like', values['CODE COLLECTIVITE'])])
                product = self.env['product.template'].search([('code', '=', values['CODE PRODUIT'])])
                val['collectivite_id'] = collectivite.id
                val['product_id'] = product.id
                val['name'] = 'Adhesion %s / %s' % (collectivite.name, product.name)
                val['import_flag'] = True
                if(product.base_calcul == "salaire"): 
                    mt = float('.'.join(str(x) for x in tuple(values['TARIF'].split(','))))
                    tarif_obj = self.env['cmim.tarif'].search([('type', '=', values['TYPE TARIF'].lower()), ('montant', '=', mt)])
                    if(not tarif_obj):
                        name= "%s" %mt
                        if(values['TYPE TARIF'].lower() == 'p'):
                            name="%s %%" %(mt)
                        val['tarif_id'] = tarif_obj.create({'name': name,
                                                          'type': values['TYPE TARIF'].lower(),
                                                          'import_flag' : True,
                                                          'montant':mt
                                                          }).id
                    else:
                        val['tarif_id'] = tarif_obj.id
                else:
                    mt = float('.'.join(str(x) for x in tuple(values['TARIF INC DEC'].split(','))))
                    tarif_obj = self.env['cmim.tarif'].search([('type', '=', values['TYPE TARIF'].lower()), ('montant', '=', mt)])
                    if(not tarif_obj):
                        val['tarif_inc_deces_id'] = tarif_obj.create({
                                                          'name': "%s %%" %(mt),
                                                          'montant': mt
                                                          }).id
                    else:
                        val['tarif_inc_deces_id'] = tarif_obj.id
                        
                    mt = float('.'.join(str(x) for x in tuple(values['TARIF INV'].split(','))))
                    tarif_obj = self.env['cmim.tarif'].search([('type', '=', values['TYPE TARIF'].lower()), ('montant', '=', mt)])
                    if(not tarif_obj):
                        val['tarif_inv_id'] = tarif_obj.create({
                                                          'name': "%s %%" %(mt),
                                                          'import_flag' : True,
                                                          'montant':mt
                                                          }).id
                    else:
                        val['tarif_inv_id'] = tarif_obj.id
                collectivite.write({'contrat_ids':   [(0, 0, val)]})
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
    def import_declarations(self, reader_info, keys):
        # check if keys exist
        if not isinstance(keys, list) or ('ID NUM PERSONNE' not in keys) or ('NB JOURS' not in keys) or ('SALAIRE'not in keys):
            raise exceptions.Warning(
                _("Verifiez l entete de votre fichier"))
        declaration_obj = self.env['cmim.declaration']
        for i in range(len(reader_info)):
            val = {}
            field = reader_info[i]
            values = dict(zip(keys, field))  
            salaire = float('.'.join(str(x) for x in tuple(values['SALAIRE'].split(','))))
            if(not salaire==0):
                assure = self.env['cmim.assure'].search([('numero', '=', values['ID NUM PERSONNE'])])
                if(assure):
                    if(not declaration_obj.search([('assure_id.id','=',assure.id),('payroll_year_id','=',self.payroll_year_id.id),('payroll_period_id','=',self.payroll_period_id.id)])):
                        val['collectivite_id'] = assure.collectivite_id.id
                        val['assure_id'] = assure.id
                        val['nb_jour'] = values['NB JOURS']
                        val['salaire'] = salaire
                        val['payroll_year_id'] = self.payroll_year_id.id
                        val['payroll_period_id'] = self.payroll_period_id.id
                        val['import_flag'] = True
                        declaration_obj.create(val)
        return True
############################################################################

    @api.multi
    def import_assures(self, reader_info, keys):
        # check if keys exist
        if not isinstance(keys, list) or ('ID NUM FAMILLE PER' not in keys)or ('CODE COLLECTIVITE' not in keys)or ('ID NUM PERSONNE' not in keys) or ('NOM' not in keys) or ('PRENOM' not in keys) or ('STATUT' not in keys):
            raise exceptions.Warning(
                _("Verifiez l entete de votre fichier "))
        assure_obj = self.env['cmim.assure']
        for i in range(len(reader_info)):
            val = {}
            field = reader_info[i]
            values = dict(zip(keys, field))  
            if(not assure_obj.search([('numero', '=', values['ID NUM PERSONNE'])])):
                collectivite_obj = self.env['res.partner'].search([('code', '=', values['CODE COLLECTIVITE'])])
                if(collectivite_obj):
                    val['collectivite_id'] = collectivite_obj.id
                    val['name'] = '%s %s' % (values['PRENOM'], values['NOM'])
                    val['numero'] = values['ID NUM PERSONNE']
                    epoux_obj = self.env['cmim.assure'].search([("id_num_famille", '=', values['ID NUM FAMILLE PER'])])
                    if(epoux_obj):
                        val['epoux_id'] = epoux_obj.id
                    val['id_num_famille'] = values['ID NUM FAMILLE PER']
                    val['import_flag'] = True
                    try:
                        val['date_naissance'] = datetime.strptime(values['DATE NAISSANCE'], "%d/%m/%Y").date()
                    except Exception:
                        val['date_naissance'] = None
                        
                    if(values['STATUT'].upper() == 'RETRAITE'):
                        val['statut'] = 'retraite'
                    if(values['STATUT'].upper() == 'INVALIDE'):
                        val['statut'] = 'invalide'
                    assure_obj = assure_obj.create(val)
                    epoux_obj.write({'epoux_id':assure_obj.id})
        return True
############################################################################

    @api.multi
    def import_reglements(self, reader_info, keys):
        # check if keys exist
        if not isinstance(keys, list) or ('NUMERO DE COMPTE' not in keys) or ('CREDIT' not in keys) :
            raise exceptions.Warning(
                _("Verifiez l entete de votre fichier"))
        account_obj = self.env['account.payment']
        collectivite_obj = self.env['res.partner']
        codes = []
        for i in range(len(reader_info)):
            field = reader_info[i]
            values = dict(zip(keys, field))  
            codes.append(int(values['NUMERO DE COMPTE']))
        if(not collectivite_obj.search([('code', 'in', codes)])):
            raise exceptions.Warning(
                _("Collectivites inexistantes, verifiez votre fichier"))
        else:
            for i in range(len(reader_info)):
                val = {}
                field = reader_info[i]
                values = dict(zip(keys, field))  
                collectivite_obj = collectivite_obj.search([('code', '=', values['NUMERO DE COMPTE'])])
                if(collectivite_obj):
                    if(not account_obj.search([('partner_id.id','=',collectivite_obj.id),('payroll_year_id','=',self.payroll_year_id.id),('payroll_period_id','=',self.payroll_period_id.id)])):
                        val['partner_id'] = collectivite_obj.id
                        val['journal_id'] = 6
                        val['payment_method_id'] = 1
                        val['payment_type'] = 'inbound'
                        val['partner_type'] = 'customer'
                        val['payroll_year_id'] = self.payroll_year_id.id
                        val['payroll_period_id'] = self.payroll_period_id.id
                        val['import_flag'] = True
                        val['amount'] = float('.'.join(str(x) for x in tuple(values['CREDIT'].split(','))))
                        #val['amount'] = 4
                        account_obj = account_obj.create(val)
                        account_obj.post()
                
        return True
############################################################################

    @api.multi
    def import_dec_pay(self):
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
        keys = reader_info[0]
        del reader_info[0]
        if self.type_operation == 'declaration':
            if(not self.env['res.partner'].search([('customer', '=', True), ('is_company', '=', True)])):
                raise exceptions.Warning(_("L'import des declarations exige l'existance des collectivites dans le systemes, veuillez creer les collectivites en premier"))
            else:
                return self.import_declarations(reader_info, keys)
        elif self.type_operation == 'reglement':
            if(not self.env['res.partner'].search([('customer', '=', True), ('is_company', '=', True)])):
                raise exceptions.Warning(_("L'import des encaissements exige l'existances des collectivites dans le systemes, veuillez creer les collectivites en premier"))
            else:
                return self.import_reglements(reader_info, keys)
            
    @api.multi
    def import_pdt(self):
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
        keys = reader_info[0]
        del reader_info[0]
        
        if not isinstance(keys, list) or ('CODE PRODUIT' not in keys):
            raise exceptions.Warning(
                _("Verifiez l entete de votre fichier"))
        product_obj = self.env['product.template']
        codes = []
        for i in range(len(reader_info)):
            field = reader_info[i]
            values = dict(zip(keys, field))  
            codes.append(values['CODE PRODUIT'])
        if(product_obj.search([('code', 'in', codes)])):
            raise exceptions.Warning(
                _("Codes produits existants, verifiez votre fichier"))
        else:
            for i in range(len(reader_info)):
                val = {}
                field = reader_info[i]
                values = dict(zip(keys, field))   
                if not self.env['product.template'].search([('code', '=', values['CODE PRODUIT'])]):
                    val['code'] = values['CODE PRODUIT']
                    val['name'] = values['NOM PRODUIT']
                    val['import_flag'] = True
                    if(values['OBLIGATOIRE'] == 'O'):
                        val['is_mandatory'] = True
                    if(float('.'.join(str(x) for x in tuple(values['TARIF'].split(',')))) == 0):
                        val['plancher'] = int(values['TRANCHEA'])
                        val['plafond'] = int(values['TRANCHEB'])
                        val['base_calcul'] = 'tranche'
                    else: 
                        val['plancher'] = int(values['PLANCHER'])
                        val['plafond'] = int(values['PLAFOND'])
                        val['base_calcul'] = 'salaire'
                    val['categ_id'] = self.categ_id.id
                    product_obj.create(val)
        return True


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
        keys = reader_info[0]
        del reader_info[0]
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
                keys2 = reader_info2[0]
                del reader_info2[0]
                return self.import_collectivites(reader_info, keys , reader_info2, keys2)
        else:
            
            if self.type_entite == 'assure':
                if(not self.env['res.partner'].search([('customer', '=', True), ('is_company', '=', True)])):
                    raise exceptions.Warning(_("L'import des associes exige l'existances des collectivites dans le systemes, veuillez creer les collectivites en premier"))
                else:
                    return self.import_assures(reader_info, keys)
                
                
                
                        
            
            
            
