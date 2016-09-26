
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, api


###################################################################################################
class collectivite(models.Model):
    _name = 'cmim.collectivite'
    _inherit = "res.partner"
    _sql_constraints = [
        ('code_collectivite_uniq', 'unique(code)', 'le code d\'adherent doit etre unique'),
    ]
    
    code = fields.Char(string="Code collectivite", required=True, copy=False)
    raissoc = fields.Char(string="Raison sociale", required=True)
    customer = fields.Boolean('Is a Customer', help="Check this box if this contact is a customer.", default=True),
    is_company = fields.Boolean(
            'Is a Company',
            help="Check if the contact is a company, otherwise it is a person", default="True"),
    company_type = fields.Selection(
            selection=[('person', 'Individual'),
                       ('company', 'Company')],
            string='Company Type',
            help='Technical field, used only to display a boolean using a radio '
                 'button. As for Odoo v9 RadioButton cannot be used on boolean '
                 'fields, this one serves as interface. Due to the old API '
                 'limitations with interface function field, we implement it '
                 'by hand instead of a true function field. When migrating to '
                 'the new API the code should be simplified. Changing the'
                 'company_type of a company contact into a company will not display'
                 'this contact as a company contact but as a standalone company.', 
                 default='Company'),
    date_adhesion = fields.Date(string="date d\'adhesion", required=True),
    assure_ids = fields.One2many('cmim.assure', 'collectivite_id', string="Assures associes"),
    adherence_id = fields.Many2one('cmim.adherence', "Relation d'adherence")

class assure(models.Model):
    _name = 'cmim.assure'
    _inherit = "res.partner"
    _sql_constraints = [
        ('numero_uniq', 'unique(numero)', 'le code d\'assure doit etre unique'),
    ]
    
    id_num_famille = fields.Integer(string="Id Numero Famille", required=True)
    numero = fields.Integer(string="Numero Assure", required=True)
    code = fields.Char(string="Code collectivite", required=True, copy=False)
    collectivite_id = fields.Many2one('cmim.collectivite', string='Collectivite', required=True)
    statut = fields.Selection(selection= [('active', 'Actif'),
                                          ('invalide', 'Invalide'),
                                          ('retraite', 'Retraite')],
                                           required=True,
                                           string='Statut',
                                           default='active')
    is_normal = fields.Boolean('Est un assure ordinaire', default = True)
    adherence_id = fields.Many2one('cmim.adherence', string = "Relation d'adherence", domain=[('is_normal', 'is', False)])
    
    
    
    
    
    
    