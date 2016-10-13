from datetime import datetime
from datetime import date
from openerp import fields, models, exceptions, api, _
import base64
import csv
import cStringIO
###################################################################################################

class cmim_import(models.TransientModel):
    
    _name = 'cmim.import'
    _description = 'Import des donnees'    

    data = fields.Binary("Fichier de l'objet", required=True)
    data_contrat = fields.Binary("Fichier relation d'adhesion")
    delimeter = fields.Char('Delimeter', default=',',
                            help='Default delimeter is ";"')
    type = fields.Selection(selection=[('collectivite', 'Collectivites'),
                                         ('assure', 'Assures'),
                                         ('produit', 'Produits'),
                                         ('declaration', 'Declarations'),
                                         ('reglement', 'Encaissements')],
                                           required=True,
                                           string="Objet d'import",
                                           default='collectivite')
    categ_id = fields.Many2one('product.category', ' Categorie', change_default=True, domain="[('type','=','normal')]" , help="Select category for the current product")
    payroll_year_id = fields.Many2one('py.year', 'Calendrier')
    payroll_period_id = fields.Many2one('py.period', 'Periode', domain="[('payroll_year_id','=',payroll_year_id)]")
    # state = fields
    
############################################################################

    @api.multi
    def import_produits(self, reader_info, keys):
        # check if keys exist
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

############################################################################

    @api.multi
    def import_collectivites(self, reader_info, keys , reader_info2, keys2):
        # check if keys exist for first file
        if not isinstance(keys, list) or ('CODE COLLECTIVITE' not in keys) or ("DATE ADHESION" not in keys) or ('SECTEUR' not in keys):
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
        for i in range(len(reader_info)):
            field = reader_info[i]
            values = dict(zip(keys, field))  
            codes.append(values['CODE COLLECTIVITE'])
        if(partner_obj.search([('code', 'in', codes)])):
            raise exceptions.Warning(
                _("Codes collectivites existants, verifiez votre fichier"))
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
                    raise exceptions.Warning(
                        _("Aucune relation d'adhesion n'est definie pour la collectivite codes[i], verifiez la coherence de vos fivhiers"))
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
                    secteur = self.env['cmim.secteur'].search([('name', 'like', values['SECTEUR'])])
                    if(secteur):
                        val['secteur_id'] = secteur.id
                    else: 
                        val['secteur_id'] = self.env['cmim.secteur'].search([('name', 'like', 'DIVERS')]).id
                    val['country_id'] = self.env['res.country'].search([('name', 'ilike', values['VILLE'])]).id or False
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
                val['name'] = 'Adhesion %s a %s' % (collectivite.name, product.name)
                val['import_flag'] = True
                if(product.base_calcul == "salaire"): 
                    mt = float('.'.join(str(x) for x in tuple(values['TARIF'].split(','))))
                    val['tarif_id'] = tarif_obj.create({'name': '% s / %s __%s' % (product.name, collectivite.name, mt),
                                                      'type': values['TYPE TARIF'].lower(),
                                                      'import_flag' : True,
                                                      'montant':mt
                                                      }).id
                else:
                    mt = float('.'.join(str(x) for x in tuple(values['TARIF INC DEC'].split(','))))
                    val['tarif_inc_deces_id'] = tarif_obj.create({
                                                      'name': '%s / %s __%s ' % (product.name, collectivite.name, mt),
                                                      'montant': mt
                                                      }).id
                    mt = float('.'.join(str(x) for x in tuple(values['TARIF INV'].split(','))))
                    val['tarif_inv_id'] = tarif_obj.create({
                                                      'name': '%s / %s __%s ' % (product.name, collectivite.name,mt),
                                                      'import_flag' : True,
                                                      'montant':mt
                                                      }).id
                collectivite.write({'contrat_ids':   [(0, 0, val)]})
        return True
############################################################################
    @api.multi
    def import_declarations(self, reader_info, keys):
        # check if keys exist
        """ PERIODE"""
        if not isinstance(keys, list) or ('ID NUM PERSONNE' not in keys) or ('NB JOURS' not in keys) or ('SALAIRE'not in keys):
            raise exceptions.Warning(
                _("Verifiez l entete de votre fichier"))
        declaration_obj = self.env['cmim.declaration']
        for i in range(len(reader_info)):
            #try:
                val = {}
                field = reader_info[i]
                values = dict(zip(keys, field))  
                assure = self.env['cmim.assure'].search([('id_num_famille', '=', values['ID NUM PERSONNE'])])
                val['collectivite_id'] = assure.collectivite_id.id
                val['assure_id'] = assure.id
                val['nb_jour'] = values['NB JOURS']
                val['salaire'] = float('.'.join(str(x) for x in tuple(values['SALAIRE'].split(','))))
                val['payroll_year_id'] = self.payroll_year_id.id
                val['payroll_period_id'] = self.payroll_period_id.id
                val['import_flag'] = True
                print values['ID NUM PERSONNE']
                declaration_obj.create(val)
                """except Exception:
                    raise exceptions.Warning(
                        _("Une erreur s'est produite au niveau de la ligne %s ")%(i+1))"""
        return True
############################################################################

    @api.multi
    def import_assures(self, reader_info, keys):
        # check if keys exist
        if not isinstance(keys, list) or ('ID NUM FAMILLE PER' not in keys)or ('CODE COLLECTIVITE' not in keys)or ('ID NUM PERSONNE' not in keys) or ('NOM' not in keys) or ('PRENOM' not in keys) or ('STATUT' not in keys):
            raise exceptions.Warning(
                _("Verifiez l entete de votre fichier "))
        assure_obj = self.env['cmim.assure']
        codes = []
        for i in range(len(reader_info)):
            field = reader_info[i]
            values = dict(zip(keys, field))  
            codes.append(values['ID NUM PERSONNE'])
        if(assure_obj.search([('numero', 'in', codes)])):
            raise exceptions.Warning(
                _("Identifiants assures existants, verifiez votre fichier"))
        else:
            for i in range(len(reader_info)):
                try:
                    val = {}
                    field = reader_info[i]
                    values = dict(zip(keys, field))  
                    val['collectivite_id'] = self.env['res.partner'].search([('code', '=', values['CODE COLLECTIVITE'])]).id
                    val['name'] = '%s %s' % (values['PRENOM'], values['NOM'])
                    val['numero'] = values['ID NUM PERSONNE']
                    val['id_num_famille'] = values['ID NUM FAMILLE PER']
                    val['import_flag'] = True
                    try:
                        val['date_naissance'] = datetime.strptime(values['DATE NAISSANCE'], "%d/%m/%Y").date()
                    except Exception:
                        val['date_naissance'] = None
                        
                    if(values['STATUT'].upper() is 'RETRAITE'):
                        val['statut'] = 'retraite'
                    if(values['STATUT'].upper() is 'INVALIDE'):
                        val['statut'] = 'invalide'
             
                    assure_obj.create(val)
                except Exception:
                    raise exceptions.Warning(
                        _("Une erreur s'est produite au niveau de la ligne %s ")%(i+1))
        return True
############################################################################

    @api.multi
    def import_reglements(self, reader_info, keys):
        # check if keys exist
        """ NUMERO DE COMPTE    LIBELLE    CREDIT"""
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
                #try:
                    val = {}
                    field = reader_info[i]
                    values = dict(zip(keys, field))  
                    val['partner_id'] = collectivite_obj.search([('code','=', int(values['NUMERO DE COMPTE']))]).id
                    val['journal_id'] = 6
                    val['payment_method_id'] = 1
                    val['payment_type'] = 'inbound'
                    val['partner_type'] = 'customer'
                    val['import_flag'] = True
                    #try:
                    #val['amount'] = float('.'.join(str(x) for x in tuple(values['CREDIT'].split(','))))
                    val['amount'] = 4
                    account_obj = account_obj.create(val)
                    print account_obj.partner_id,'----------------------------',i
                    account_obj.post()
                    """except Exception:
                        print 'ligne negligee'
                except Exception:
                    raise exceptions.Warning(
                        _("Une erreur s'est produite au niveau de la ligne %s ")%(i+1))"""
                
        return True
############################################################################

    @api.multi
    def import_action(self):
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
        if self.type == 'collectivite':
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
            
            if self.type == 'assure':
                if(not self.env['res.partner'].search([('customer', '=', True), ('is_company', '=', True)])):
                    raise exceptions.Warning(_("L'import des associes exige l'existances des collectivites dans le systemes, veuillez creer les collectivites en premier"))
                else:
                    return self.import_assures(reader_info, keys)
            if self.type == 'produit':
                return self.import_produits(reader_info, keys)
            if self.type == 'declaration':
                if(not self.env['res.partner'].search([('customer', '=', True), ('is_company', '=', True)])):
                    raise exceptions.Warning(_("L'import des declarations exige l'existance des collectivites dans le systemes, veuillez creer les collectivites en premier"))
                else:
                    return self.import_declarations(reader_info, keys)
            else:
                if(not self.env['res.partner'].search([('customer', '=', True), ('is_company', '=', True)])):
                    raise exceptions.Warning(_("L'import des encaissements exige l'existances des collectivites dans le systemes, veuillez creer les collectivites en premier"))
                else:
                    return self.import_reglements(reader_info, keys)
                
                
                
                        
            
            
            
