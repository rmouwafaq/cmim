# -*- coding: utf-8 -*-
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields,exceptions, api, _
from openerp.exceptions import UserError


class Cotisation(models.Model):
    _name ='cmim.cotisation'

    @api.multi
    def unlink(self):
        for cotisation in self:
            if cotisation.state == 'valide' and not cotisation.invoice_id.state == 'draft':
                raise ValidationError("Vous ne pouvez pas supprimer une cotisation d'une Facture validee")
            self.env['account.invoice'].search([('id', '=', cotisation.invoice_id.id)]).unlink()
        super(Cotisation, self).unlink()
        
    @api.multi
    def open_invoice(self):
        view_id = self.env.ref('account.invoice_form').id
        return{ 
                'res_model':'account.invoice',
                'type': 'ir.actions.act_window',
                'res_id': self.invoice_id.id,
                'view_mode':'tree,form',
                'views' : [(view_id, 'form'),(False, 'tree')],
                'view_id': 'account.invoice_form',
                'target':'self',
                }
    @api.multi
    def _getmontant_total(self):
        for obj in self:
            if(obj.cotisation_assure_ids):
                obj.montant = sum(line.montant for line in obj.cotisation_assure_ids)
            elif(obj.cotisation_product_ids):
                obj.montant = sum(line.montant for line in obj.cotisation_product_ids)
                
    name =  fields.Char('Libelle')
    collectivite_id = fields.Many2one('res.partner', 'Collectivite',required=True,  domain = "[('customer','=',True),('is_company','=',True)]")
    invoice_id = fields.Many2one('account.invoice', 'Facture', domain=[('type', '=', 'out_invoice')],  ondelete='cascade')
    cotisation_assure_ids = fields.One2many('cmim.cotisation.assure.line', 'cotisation_id', 'Ligne de calcul par assure')    
    cotisation_product_ids = fields.One2many('cmim.cotisation.product', 'cotisation_id', 'Ligne de calcul par produit')    
    montant = fields.Float(compute="_getmontant_total", string='Montant')
    
    state = fields.Selection(selection=[('draft', 'Brouillon'),
                                        ('valide', 'Validee')],
                                        required=True,
                                        string='Etat', 
                                        default = 'draft')
    secteur_id = fields.Many2one('cmim.secteur',
        string='Secteur',
        related='collectivite_id.secteur_id', store=True
    )
    
    @api.onchange('fiscal_date')
    def onchange_fiscal_date(self):
        if(self.fiscal_date):
            periodes = self.env['date.range'].search([])
            ids = []
            for periode in periodes :
                duree = (datetime.strptime(periode.date_end, '%Y-%m-%d') - datetime.strptime(periode.date_start, '%Y-%m-%d')).days
                if duree > 88 and duree < 92 and self.fiscal_date == datetime.strptime(periode.date_end, '%Y-%m-%d').year and self.fiscal_date == datetime.strptime(periode.date_start, '%Y-%m-%d').year:
                    ids.append(periode.id)
            return {'domain':{'date_range_id': [('id', 'in', ids)]}}
        
    fiscal_date = fields.Integer(string=u"Année Comptable", required=True, default= datetime.now().year )
    date_range_id = fields.Many2one('date.range', u'Période', required=True)
    @api.multi
    def action_validate(self):
        
        inv_obj = self.env['account.invoice']
        for obj in self:
            invoices = {}
            group_key = obj.id 
            for line in obj.cotisation_product_ids:
                if group_key not in invoices:
                    inv_data = obj._prepare_invoice()
                    invoice = inv_obj.create(inv_data)
                    invoices[group_key] = invoice
                line.invoice_line_create(invoices[group_key].id)
                obj.invoice_id = invoice.id
    
            if not invoices:
                raise UserError(_('Pas de lignes facturables.'))
    
            for invoice in invoices.values():
                if not invoice.invoice_line_ids:
                    raise UserError(_('Pas de lignes facturables.'))
            obj.state = 'valide'
            obj.name = self.env['ir.sequence'].next_by_code('cmim.cotisation') 
            obj.invoice_id.origin = obj.name
            return [inv.id for inv in invoices.values()]
        
    def _prepare_invoice(self):
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Veuillez definir un compte journal pour votre Ste.'))
        invoice_vals = {
            'name': self.collectivite_id.name ,
            'origin':self.collectivite_id.name,
            'type': 'out_invoice',
            'account_id': self.collectivite_id.property_account_receivable_id.id,
            'partner_id': self.collectivite_id.id,
            'journal_id': journal_id,
            'date_invoice' : self.date_range_id.date_end,
            'residual_signed' : self.montant
        }
        return invoice_vals

class cotisation_assure_line(models.Model):
    _name = 'cmim.cotisation.assure.line'
    _description = "Lignes ou details du calcul des cotisations_assure"
    _order = 'contrat_line_id'

    @api.multi
    def update_cotisation_product(self):
        cotisation_product_obj = self.env['cmim.cotisation.product']
        cotisation_product_obj = cotisation_product_obj.search([('cotisation_id.id', '=', self.cotisation_id.id),
                                                                ('product_id.id', '=', self.product_id.id),
                                                                ('regle_id', '=', self.regle_id.id)])
        
        if(cotisation_product_obj):
            cotisation_product_obj.write({'montant': cotisation_product_obj.montant + self.montant})
        else:
            cotisation_product_obj = cotisation_product_obj.create({'cotisation_id': self.cotisation_id.id,
                                                                    'product_id': self.product_id.id,
                                                                    'regle_id': self.regle_id.id,
                                                                    'tarif': self.taux,
                                                                    'montant' : self.montant
                                                                    })
        self.cotisation_id.write({'cotisation_product_ids': [(4, cotisation_product_obj.id)]})
    @api.model
    def create(self, vals):
        if vals['base'] == -1:
            vals.update({
                    'montant': vals['taux'],
                    'base' : 1,
                })
        else:
            vals['montant'] = (vals['base'] * vals['taux'])/100
        
        cotisation_line =  super(cotisation_assure_line, self).create(vals)
        cotisation_line.update_cotisation_product()
        return cotisation_line

    @api.multi
    def _get_proratat(self):
        for obj in self:
            obj.proratat = obj.nb_jour / 90.0
            
    cotisation_id = fields.Many2one('cmim.cotisation', string='Cotisation',  ondelete='cascade')
    declaration_id = fields.Many2one('cmim.declaration', string=u'Déclaration')
    assure_id = fields.Many2one('res.partner', string=u'Assuré',related='declaration_id.assure_id', store=True )
    salaire = fields.Float(related='declaration_id.salaire')
    nb_jour = fields.Integer(related='declaration_id.nb_jour', string="NB Jours")
    proratat = fields.Float(string="Proratat" , compute="_get_proratat")
    contrat_line_id = fields.Many2one('cmim.contrat.line', 'Ligne contrat', required=True)
    product_id  = fields.Many2one('product.template', related='contrat_line_id.product_id', store=True)
    product_name  = fields.Char(related='product_id.short_name', string='Produit', store=True)
    regle_id = fields.Many2one('cmim.regle.calcul',  string=u"Règle Calcul", related='contrat_line_id.regle_id')
    name = fields.Char('Description')
    base = fields.Float('Base')
    taux = fields.Float('Tarif')
    montant = fields.Float('Montant') 
    
class cotisation_product(models.Model):
    _name = 'cmim.cotisation.product'
    _description = "Lignes ou details du calcul des cotisations_produit"

    cotisation_id = fields.Many2one('cmim.cotisation', 'Cotisation',  ondelete='cascade')
    product_id = fields.Many2one('product.template', 'Produit') 
    regle_id = fields.Many2one('cmim.regle.calcul',"Règle de calcul" )
    tarif = fields.Float("Tarif")
    montant = fields.Float('Montant', default= 0.0) 
    
    @api.multi
    def _prepare_invoice_line(self):
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % \
                            (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        res = {
            'name': self.product_id.name,
            'origin': self.cotisation_id.collectivite_id.name,
            'account_id': account.id,
            'price_unit': self.montant,
            'quantity': 1,
            'uom_id': 1,
            'product_id': self.product_id.id or False,
        }
        return res
    @api.multi
    def invoice_line_create(self, invoice_id):
        for line in self:
                vals = line._prepare_invoice_line()
                vals.update({'invoice_id': invoice_id, 'invoice_line_ids': [(6, 0, [line.id])]})
                self.env['account.invoice.line'].create(vals)
