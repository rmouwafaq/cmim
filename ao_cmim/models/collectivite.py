import openerp
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields,tools, api


class secteur(models.Model):
    _name='cmim.secteur'
    
    name = fields.Char('nom du secteur', reduired=True)
    plancher = fields.Float('Plancher du secteur')
    plafond = fields.Float('Plafond du secteur')   
    
class collectivite(models.Model):
    _inherit = "res.partner"
    """_sql_constraints = [
        ('code_collectivite_uniq', 'unique(code)', 'le code d\'adherent doit etre unique'),
    ]"""
    _defaults = {
        'company_type': 'company',
        'is_company': True,
        'customer' : True
        }
    import_flag = fields.Boolean('Par import', default=False)      
    code = fields.Char(string="Code collectivite", required=True, copy=False)
    name = fields.Char(string="Raison sociale", required=True)
    date_adhesion = fields.Date(string="date d\'adhesion", required=True)
    assure_ids = fields.One2many('cmim.assure', 'collectivite_id', string="Assures associes" )
    secteur_id = fields.Many2one('cmim.secteur', "Secteur")
    contrat_ids = fields.One2many('cmim.contrat','collectivite_id', string="Contrats")
    declaration_ids = fields.Many2one('cmim.declaration', 'Declarations')
    

class assure(models.Model):
    _name = 'cmim.assure'

    """_sql_constraints = [
        ('numero_uniq', 'unique(numero)', 'le code d\'assure doit etre unique'),
    ]"""
    _defaults = {
        'statut': 'active',
        'is_normal' : True,
        }
    
    def _get_default_image(self):
        img_path = openerp.modules.get_module_resource(
            'base', 'static/src/img', 'avatar.png')
        with open(img_path, 'rb') as f:
            image = f.read()
        return tools.image_resize_image_big(image.encode('base64'))
    
    import_flag = fields.Boolean('Par import', default=False)      
    name = fields.Char('Nom', required=True)
    image = openerp.fields.Binary("Image", attachment=True,
        help="This field holds the image used as avatar for this contact, limited to 1024x1024px",
        default=lambda self: self._get_default_image())
    email =  fields.Char('Email')
    phone = fields.Char('Phone')
    mobile = fields.Char('Mobile')
    street = fields.Char('Street')
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", 'State', ondelete='restrict')
    zip = fields.Char('Zip', size=24, change_default=True)
    country_id = fields.Many2one('res.country', 'Country', ondelete='restrict')
    
    
    id_num_famille = fields.Integer(string="Id Numero Famille")
    numero = fields.Integer(string="Numero Assure", required=True)
    collectivite_id = fields.Many2one('res.partner', string='Collectivite', domain="[('customer','=',True),('is_company','=',True)]", required=True,  ondelete='cascade')
    statut = fields.Selection(selection= [('active', 'Actif'),
                                          ('invalide', 'Invalide'),
                                          ('retraite', 'Retraite')],
                                           required=True,
                                           string='Statut')
    
    date_naissance = fields.Date(string="Date de naissance")
    is_normal = fields.Boolean('Est Normal')
    contrat_ids = fields.One2many('cmim.contrat','assure_id', string="Contrats")
    declaration_ids = fields.Many2one('cmim.declaration', 'Declarations')    
    
    @api.model
    def create(self, vals):
        tools.image_resize_images(vals)
        partner = super(assure, self).create(vals)
        return partner

    