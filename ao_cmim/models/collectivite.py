
import openerp
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, tools, api

class collectivite(models.Model):
    _inherit = "res.partner"
    _sql_constraints = [
        ('code_collectivite_uniq', 'unique(code)', 'le code d\'adherent doit etre unique'),
    ]
    _defaults = {
        'company_type': 'company',
        'is_company': True,
        'customer' : True
        }
    @api.one
    @api.depends('assure_ids')
    def _assures_count(self):
        
        for obj in self:
            if self.assure_ids :
                obj.assures_count = len(self.assure_ids)
            
    import_flag = fields.Boolean('Par import', default=False)      
    code = fields.Char(string="Code collectivite", required=True, copy=False)
    old_code = fields.Char(string="Code collectivite")
    name = fields.Char(string="Raison sociale", required=True)
    date_adhesion = fields.Date(string="date d\'adhesion", required=True)
    secteur_id = fields.Many2one('cmim.secteur', "Secteur", required=True)
    contrat_ids = fields.One2many('cmim.contrat', 'collectivite_id', string="Contrats")
    assure_ids = fields.One2many('cmim.assure', 'collectivite_id', string="Assures associes")
    assures_count = fields.Integer(compute='_assures_count', string="Nb assures")
    parent_id = fields.Many2one('res.partner', domain="[('customer','=',True),('is_company','=',True)]")
    @api.multi
    def get_assures(self):
        view_id = self.env.ref('ao_cmim.view_assure_tree').id
        return{ 
                'res_model':'cmim.assure',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'view_mode':'tree,form',
                'views' : [(view_id, 'tree'),(False, 'form')],
                'view_id': 'ao_cmim.view_assure_tree',
                'target':'self',
                'domain':[('collectivite_id.id', '=', self.id)],
                }
    
    @api.multi
    def get_payments(self):
        view_id = self.env.ref('account.view_account_payment_tree').id
        return{ 
                'res_model':'account.payment',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'view_mode':'tree,form',
                'views' : [(view_id, 'tree'),(False, 'form')],
                'view_id': 'account.view_account_payment_tree',
                'target':'self',
                'domain':[('partner_id.id', '=', self.id)],
                }
    
    @api.multi
    def get_declarations(self):
        view_id = self.env.ref('ao_cmim.declaration_tree_view').id
        return{ 
                'res_model':'cmim.declaration',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'view_mode':'tree',
                'views' : [(view_id, 'tree'),(False, 'form')],
                'view_id': 'ao_cmim.declaration_tree_view',
                'target':'self',
                'domain':[('collectivite_id.id', '=', self.id)],
                'context':{'group_by':'date_range_id'},
                }
    @api.multi
    def get_cotisations(self):
        view_id = self.env.ref('ao_cmim.cotisation_tree_view').id
        return{ 
                'res_model':'cmim.cotisation',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'view_mode':'tree',
                'views' : [(view_id, 'tree'),(False, 'form')],
                'view_id': 'ao_cmim.cotisation_tree_view',
                'target':'self',
                'domain':[('state', '=', 'draft'),('collectivite_id.id', '=', self.id)],
                'context':{'group_by':'date_range_id'},
                }
    
    @api.multi
    def import_declaration(self):
        return True
        