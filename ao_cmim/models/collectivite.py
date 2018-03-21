# -*- coding: utf-8 -*-
from openerp import models, fields, tools, api

class ResPartner(models.Model):
    _inherit = "res.partner"
    _sql_constraints = [
        ('code_collectivite_uniq', 'unique(code)', 'le code d\'adhérent doit être unique'),
        ('numero_uniq', 'unique(numero)', 'le matricule doit être unique.'),
    ]

    import_flag = fields.Boolean('Par import', default=False)      
    code = fields.Char(string="Code collectivite")
    prenom = fields.Char(string=u'Prénom')
    date_adhesion = fields.Date(string="date d\'adhesion")
    secteur_id = fields.Many2one('cmim.secteur', "Secteur", ondelete="restrict")
    
    siege_id = fields.Many2one('res.partner', string=u'Collectivité mère', domain="[('customer','=',True),('is_company','=',True)]")
    filliale_ids = fields.One2many('res.partner', 'siege_id', 'Filliales', domain=[('customer','=',True),('is_company','=',True)])
    
    contrat_id = fields.Many2one('cmim.contrat', string="Contrat")
    parametrage_ids = fields.One2many('cmim.parametrage.collectivite', 'collectivite_id', u'Paramétrage')
    garantie_id = fields.Many2one('cmim.garantie', string="Garantie")
    ########################
    is_collectivite = fields.Boolean(u'Est une collectivité', default=False, store=True)
    type_entite = fields.Selection(selection=[('c', u'Collectivité'), 
                                              ('a', u'Assuré'),
                                              ('rsc', u'RSC') ])
    lib_qualite = fields.Selection(selection=[('ASS', u'Assuré'),
                                              ('EP', u'Epoux (se)')],
                                   string=u"Lib Qualité")
    sexe = fields.Selection(selection=[('M', 'Homme'), ('F', 'Femme')], 
                            default='M',
                            string="Sexe")
    id_num_famille = fields.Integer(string="Id Numero Famille")
    numero = fields.Integer(string=u"Numero Assuré")

    collectivite_id = fields.Many2one('res.partner', string='Collectivite', store=True, compute='get_last_collectivite')
    collectivite_name = fields.Char(string=u'Collectivité', related="collectivite_id.name")
    statut_id = fields.Many2one('cmim.statut.assure', string='Statut')
    statut_ids = fields.Many2many('cmim.statut.assure', 'res_partner_statut_rel', 'partner_id', 'statut_id',  string='Position/Statut')
    position_statut_ids = fields.One2many('cmim.position.statut', 'assure_id',  string='Position/Statut')
    date_naissance = fields.Date(string="Date de naissance")
    epoux_id =  fields.Many2one('res.partner', 'Epoux (se)', domain="[('id_num_famille', '=', id_num_famille),('type_entite', '=', 'a'), ('company_type','=','person')]")
    declaration_ids = fields.One2many('cmim.declaration', 'assure_id', 'Declarations') 

#     @api.model
#     def create(self, vals): 
#         if vals.get('type_entite', False) == 'rsc':
#             sexe = 'F'  if vals.get('sexe', 'M') == 'M' else 'M' 
#             epoux_id = self.search([("id_num_famille", '=',  vals.get('id_num_famille')), ("type_entite", '=', 'a'), ("sexe", '=', sexe)])
#             if epoux_id:
#                 vals.update({'epoux_id': epoux_id.id})
#             else : 
#                 return False
#         else:
#             return super(ResPartner, self).create(vals)
    @api.onchange('secteur_id', 'type_entite')
    def onchange_secteur_id(self):
        if self.secteur_id and self.type_entite == 'c':
            return {'domain':{ 'garantie_id': [('id', 'in', self.secteur_id.garantie_ids.ids)] }}
        
    def get_statut_in_periode(self, statut_ids, date_start, date_end): 
        res = []
        for pos in self.position_statut_ids:
            if pos.statut_id.id in statut_ids and pos.date_debut_appl <= date_start and pos.date_fin_appl >= date_end:
                res.append(pos.id)
        return res
    
    def get_rsc(self, regle_id, declaration_id):
        res = []
        rsc_ids = self.search([('epoux_id', '=', self.id), ('type_entite', '=', 'rsc')])
        for rsc in rsc_ids :
            if len(rsc.get_statut_in_periode(regle_id.statut_ids.ids, 
                                            declaration_id.date_range_id.date_start, 
                                            declaration_id.date_range_id.date_end)) > 0:
                res.append(rsc)
        return rsc_ids
                
    @api.multi
    def create_lines(self):
        self.ensure_one() 
        list=[]
        self.parametrage_ids = [(5,)]
        for cl in self.contrat_id.contrat_line_ids:
            if not cl.regle_id.garantie_ids or (cl.regle_id.garantie_ids and self.garantie_id.id in cl.regle_id.garantie_ids.ids)\
                    and (not cl.regle_id.secteur_ids or (cl.regle_id.secteur_ids and self.secteur_id.id in cl.regle_id.secteur_ids.ids)):
                list.append((0,0, {'name': cl.regle_id.name,
                                   'regle_id': cl.regle_id.id,
                                   'tarif_id': cl.regle_id.regle_tarif_id.default_tarif_id.id
                                   }))
        for r in self.env['cmim.regle.calcul'].search([('type', '=', 'tabat')]):
            if self.secteur_id.id in r.secteur_ids.ids or r.secteur_ids.ids == [] :
                list.append((0,0, {'name': r.name, 
                                   'regle_id': r.id,
                                   'tarif_id': r.default_tarif_id.id
                                   }))
        self.update({"parametrage_ids" : list})

    @api.multi
    @api.depends('declaration_ids')
    def get_last_collectivite(self):
        print 'get_last_collectivite'
        for obj in self:
            if obj.type_entite == 'c':
                obj.collectivite_id = False
            elif obj.type_entite == 'rsc':
                dec = self.env['cmim.declaration'].search([('assure_id', '=', obj.epoux_id.id)],
                                                          order='date_range_end desc', limit=1)
                if dec:
                    obj.collectivite_id = dec.collectivite_id.id
            elif obj.declaration_ids:
                obj.collectivite_id = self.env['cmim.declaration'].search([('assure_id', '=', obj.id)],
                                                                          order='date_range_end desc', limit=1).collectivite_id.id
            else:
                obj.collectivite_id = False

    ###################
    @api.model
    def update_assure(self):
        print 'CRON CRON'
        for ass in self.search([('type_entite', '=', 'a'), ('statut_id', '!=', False), ('numero', '!=', 0)]):
            ass.write({
                       'statut_ids' : [(4,ass.statut_id.id)],
                       })
    
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
                'domain':[ 
                          ('statut_id.code' , '!=', 'INACT'),
                          ('company_type' , '=', 'person'),
                          ('customer' , '=', True),
                          ('type_entite' , '=', 'a'),
                          ('collectivite_id' , '=', self.id),
                          ],
#                ('collectivite_id', '=', None),
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
            if context.get('default_type_entite', 'a') == 'a' and context.get('default_company_type', 'company') == 'person':
                    view_id = get_view_id('view_assure_tree', 'ao.cmim.assure.tree').id or None
                    view_type='tree'
            if context.get('default_type_entite', 'a') == 'c' and context.get('default_company_type', 'company') == 'company' \
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
#         return super(ResPartner, self).read_group(cr, uid, domain, fields, groupby, offset, limit=limit, context=context, orderby=orderby, lazy=True)1111