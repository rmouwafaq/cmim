
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields,exceptions, api, _
from openerp.exceptions import UserError


class cotisation(models.Model):
    _name ='cmim.cotisation'
    
    def _getmontant_total(self):
    
        if(self.cotisation_line_ids):
            self.montant = sum(line.montant for line in self.cotisation_line_ids)
        elif(self.cotisation_product_ids):
            self.montant = sum(line.montant for line in self.cotisation_product_ids)
                
    name =  fields.Char('Libelle')
    collectivite_id = fields.Many2one('res.partner', 'Collectivite')
    payroll_year_id = fields.Many2one('py.year', 'Calendrier')
    payroll_period_id = fields.Many2one('py.period', 'Periode de calcul', domain="[('payroll_year_id','=',payroll_year_id)]")
    cotisation_assure_ids = fields.One2many('cmim.cotisation.assure', 'cotisation_id', 'Ligne de calcul par assure')    
    cotisation_product_ids = fields.One2many('cmim.cotisation.product', 'cotisation_id', 'Ligne de calcul par produit')    
    montant = fields.Float(compute="_getmontant_total", string='Montant', default= 0.0, digits=0, store=True)
    #montant = fields.Float(string='Montant', default= 0.0)
    
    state = fields.Selection(selection=[('draft', 'Brouillon'),
                                        ('valide', 'Validee')],
                                        required=True,
                                        string='Etat', 
                                        default = 'draft')
    secteur_id = fields.Many2one('cmim.secteur',
        string='Secteur',
        related='collectivite_id.secteur_id', store=True
    )
    
    @api.multi
    def action_validate(self):
        
        inv_obj = self.env['account.invoice']
        invoices = {}
        group_key = self.id 
        for line in self.cotisation_product_ids:
            if group_key not in invoices:
                inv_data = self._prepare_invoice()
                invoice = inv_obj.create(inv_data)
                invoices[group_key] = invoice
            line.invoice_line_create(invoices[group_key].id)

        if not invoices:
            raise UserError(_('There is no invoicable line.'))

        for invoice in invoices.values():
            if not invoice.invoice_line_ids:
                raise UserError(_('There is no invoicable line.'))
        self.state = 'valide'
        return [inv.id for inv in invoices.values()]
    
    @api.multi
    def _prepare_invoice(self):
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))
        invoice_vals = {
            'name': self.collectivite_id.name ,
            'origin':self.collectivite_id.name,
            'cotisation_id.id' : self.id,
            'type': 'out_invoice',
            'account_id': self.collectivite_id.property_account_receivable_id.id,
            'partner_id': self.collectivite_id.id,
            'journal_id': journal_id,
            'residual_signed' : self.montant
        }
        return invoice_vals
  

class cotisation_assure(models.Model):
    _name = 'cmim.cotisation.assure'
    _description = "Cotisation Assure"

    def _getmontant_total(self):
        self.montant = sum(line.montant for line in self.cotisation_assure_line_ids)
        
        
    cotisation_id = fields.Many2one('cmim.cotisation', 'Cotisation',  ondelete='cascade')
    payroll_year_id = fields.Many2one('py.year', string = 'Calendrier', related='cotisation_id.payroll_year_id', store=True)
    payroll_period_id = fields.Many2one('py.period', string = 'Periode de calcul', related='cotisation_id.payroll_period_id', store=True)
    collectivite_id = fields.Many2one('res.partner', 'Collectivite')
    assure_id = fields.Many2one('cmim.assure', 'Assure')
    name =  fields.Char('Libelle')
    cotisation_assure_line_ids = fields.One2many('cmim.cotisation.assure.line', 'cotisation_assure_id', 'Ligne de calcul par assure')  
    montant = fields.Float(compute="_getmontant_total", string='Montant', default= 0.0, digits=0, store=True)
    #montant = fields.Float(string='Montant', default= 0.0)

class cotisation_assure_line(models.Model):
    _name = 'cmim.cotisation.assure.line'
    _description = "Lignes ou details du calcul des cotisations_assure"
    _order = 'cotisation_assure_id,sequence'

    cotisation_assure_id = fields.Many2one('cmim.cotisation.assure', 'Cotisation assure',  ondelete='cascade')
    cotisation_id = fields.Many2one('cmim.cotisation', string='Cotisation',related='cotisation_assure_id.cotisation_id', store=True)
    sequence = fields.Integer('Sequence')
    product_id = fields.Many2one('product.template', 'Produit')
    
    code = fields.Integer(
        string='Code Produit',
        related='product_id.code',
        )
    
    base_calcul = fields.Selection(
        string='Type du produit',
        related='product_id.base_calcul',
    )
    
    name = fields.Char('Libelle')
    base1 = fields.Float('Tranche A', help = 'si le type de produit est salaire, la tranche A est elle-meme la base de salaire', default=0.0)
    base2 = fields.Float('Tranche B', default = 0.0)
    rate1 = fields.Float('Taux 1')
    rate2 = fields.Float('Taux 2')
    montant = fields.Float('Montant', default= 0.0) 
    
class cotisation_product(models.Model):
    _name = 'cmim.cotisation.product'
    _description = "Lignes ou details du calcul des cotisations_produit"

    cotisation_id = fields.Many2one('cmim.cotisation', 'Cotisation',  ondelete='cascade')
    payroll_year_id = fields.Many2one('py.year', string = 'Calendrier', related='cotisation_id.payroll_year_id', store=True)
    payroll_period_id = fields.Many2one('py.period', string = 'Periode de calcul', related='cotisation_id.payroll_period_id', store=True)
    product_id = fields.Many2one('product.template', 'Produit')
    code = fields.Integer(
        string='Code Produit',
        related='product_id.code',
        )
    
    base_calcul = fields.Selection(
        string='Type du produit',
        related='product_id.base_calcul',
    )
    
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
            #'discount': self.discount,
            'uom_id': 1,
            'product_id': self.product_id.id or False,
            #'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            #'account_analytic_id': self.order_id.project_id.id,
        }
        return res
    @api.multi
    def invoice_line_create(self, invoice_id):
        for line in self:
                vals = line._prepare_invoice_line()
                vals.update({'invoice_id': invoice_id, 'invoice_line_ids': [(6, 0, [line.id])]})
                self.env['account.invoice.line'].create(vals)
