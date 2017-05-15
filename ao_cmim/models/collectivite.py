# -*- coding: utf-8 -*-
import openerp
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, tools, api

class ResPartner(models.Model):
    _inherit = "res.partner"
    _sql_constraints = [
        ('code_collectivite_uniq', 'unique(code)', 'le code d\'adhérent doit être unique'),
        ('numero_uniq', 'unique(numero, collectivite_id)', 'le matricule doit être unique par collectivité'),
    ]
    @api.model
    def create(self, vals): 
        partner = super(ResPartner, self).create(vals)
        epoux_id = self.search([("id_num_famille", '=', partner.id_num_famille), ("numero", '!=', partner.numero)], limit=1)
        if epoux_id:
            epoux_id.write({'epoux_id':partner.id})
            partner.write({'epoux_id':epoux_id.id})
        return partner
#     @api.multi
#     def get_tarif_of_regle(self, regle_id):
#         for obj in self:
#             if obj.parametrage_ids:
#                 parametrage = self.env['cmim.parametrage.collectivite'].search([('collectivite_id', '=', obj.id), ('regle_id', '=', regle_id)])
#                 if parametrage:
#                     return parametrage.tarif_id
#                 else:
#                     return False
    @api.multi
    def create_lines(self):
        self.ensure_one() 
        list=[]
        for line in self.parametrage_ids:
            line.unlink()
        for cl in self.contrat_id.contrat_line_ids:
            list.append((0,0, {'name': cl.regle_id.name, 
                               'regle_id': cl.regle_id.id,
                               'tarif_id': cl.regle_id.regle_tarif_id.default_tarif_id.id
                               }))
        self.update({"parametrage_ids" : list})
    import_flag = fields.Boolean('Par import', default=False)      
    code = fields.Char(string="Code collectivite")
    prenom = fields.Char(string=u'Prénom')
    date_adhesion = fields.Date(string="date d\'adhesion")
    secteur_id = fields.Many2one('cmim.secteur', "Secteur", ondelete="restrict")
    
#     assures_count = fields.Integer(compute='_assures_count', string="Nb assures")
    siege_id = fields.Many2one('res.partner', string=u'Collectivité mère', domain="[('customer','=',True),('is_company','=',True)]")
    filliale_ids = fields.One2many('res.partner', 'siege_id', 'Filliales', domain=[('customer','=',True),('is_company','=',True)])
    
    contrat_id = fields.Many2one('cmim.contrat', string="Contrat", ondelete = 'restrict')
    parametrage_ids = fields.One2many('cmim.parametrage.collectivite', 'collectivite_id', u'Paramétrage')
    ########################
    @api.multi
    def get_last_collectivite(self):
        for obj in self:
            if obj.is_collectivite:
                obj.collectivite_id = False
            elif obj.declaration_ids:
                obj.collectivite_id = self.env['cmim.declaration'].search([('assure_id', '=', obj.id)], order='date_range_end desc', limit=1).collectivite_id.id
            else:
                obj.collectivite_id = False
    is_collectivite = fields.Boolean(u'Est une collectivité', default=False)
    id_num_famille = fields.Integer(string="Id Numero Famille")
    numero = fields.Integer(string=u"Numero Assuré")

    collectivite_id = fields.Many2one('res.partner', string='Collectivite',compute=get_last_collectivite, domain="[('is_collectivite', '=', True), ('customer','=',True),('is_company','=',True)]", ondelete='cascade')
    statut_id = fields.Many2one('cmim.statut.assure', string='Statut')
    date_naissance = fields.Date(string="Date de naissance")
     
    epoux_id =  fields.Many2one('res.partner', 'Epoux (se)', domain="[('id_num_famille', '=', id_num_famille),('is_collectivite', '=', False), ('company_type','=','person')]")
    declaration_ids = fields.One2many('cmim.declaration', 'assure_id', 'Declarations') 
    ###################
#     assure_ids = fields.One2many('res.partner', 'collectivite_id', string=u"Assurés associés")
    
    @api.multi
    def get_assures(self):
        view_id = self.env.ref('ao_cmim.view_assure_tree').id
        return{ 
                'res_model':'res.partner',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'view_mode':'tree,form',
                'views' : [(view_id, 'tree'),(False, 'form')],
                'view_id': 'ao_cmim.view_assure_tree',
                'target':'self',
                'context' : {'default_company_type' : 'person',
                             'default_is_collectivite' : False, 'default_customer' : True} ,
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
    @api.model
    def fields_view_get(self, view_id=None, view_type=None, toolbar=False, submenu=False):
        def get_view_id(xid, name):
            try:
                return self.env.ref('ao_cmim.' + xid)
            except ValueError:
                view = self.env['ir.ui.view'].search([('name', '=', name)], limit=1)
                if not view:
                    return False
                return view.id

        context = self._context
        if view_type == 'tree':
            if context.get('default_is_collectivite', False) == False and context.get('default_company_type', 'company') == 'person':
                    view_id = get_view_id('view_assure_tree', 'ao.cmim.assure.tree').id or None
                    view_type='tree'
            if context.get('default_is_collectivite', False) == True and context.get('default_company_type', 'company') == 'company' \
                        and context.get('default_is_company', False) == True and context.get('default_customer', False) == True :
                
                view_id = get_view_id('view_collectivite_tree', 'ao.cmim.collectivite.tree').id or None
                view_type='tree'
        return super(ResPartner, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
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
    
    @api.multi
    def get_declarations_for_assure(self):
        if self.collectivite_id:
            view_id = self.env.ref('ao_cmim.declaration_tree_view').id
            return{ 
                    'res_model':'cmim.declaration',
                    'type': 'ir.actions.act_window',
                    'res_id': self.id,
                    'view_mode':'tree',
                    'views' : [(view_id, 'tree'),(False, 'form')],
                    'view_id': 'ao_cmim.declaration_tree_view',
                    'target':'self',
                    'domain':[('assure_id.id', '=', self.id)],
                    'context':{'group_by':'date_range_id'},
                    }
        else:
            return True
#     def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False, lazy=True):
#         if 'numero' in fields:
#             fields.remove('numero')
#         if 'id_num_famille' in fields:
#             fields.remove('id_num_famille')
#         return super(ResPartner, self).read_group(cr, uid, domain, fields, groupby, offset, limit=limit, context=context, orderby=orderby, lazy=True)