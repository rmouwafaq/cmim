
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields,exceptions, api, _
from openerp.exceptions import UserError


class cotisation(models.Model):
    _name ='cmim.cotisation'
    
    def _get_cotisation_assure_line_ids(self):
        print "_get_cotisation_assure_line_ids"
        self.cotisation_assure_line_ids = self.env['cmim.cotisation.assure.line'].search([('cotisation_id.id', '=', self.id)], order="product_id")
        print "ooook", self.cotisation_assure_line_ids
    def _getmontant_total(self):
    
        if(self.cotisation_line_ids):
            self.montant = sum(line.montant for line in self.cotisation_line_ids)
        elif(self.cotisation_product_ids):
            self.montant = sum(line.montant for line in self.cotisation_product_ids)
                
    name =  fields.Char('Libelle')
    collectivite_id = fields.Many2one('res.partner', 'Collectivite',  domain = "[('customer','=',True),('is_company','=',True)]")
    
    cotisation_assure_ids = fields.One2many('cmim.cotisation.assure', 'cotisation_id', 'Ligne de calcul par assure')    
    cotisation_product_ids = fields.One2many('cmim.cotisation.product', 'cotisation_id', 'Ligne de calcul par produit')    
    cotisation_assure_line_ids = fields.One2many('cmim.cotisation.assure.line', 'cotisation_id', compute = "_get_cotisation_assure_line_ids") 
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
    @api.onchange('fiscal_date')
    def onchange_field_id(self):
         if self.fiscal_date:
            periodes = self.env['date.range'].search([])
            ids = []
            dec_year = datetime.strptime(self.fiscal_date, '%Y-%m-%d').year
            for periode in periodes :
                duree =  (datetime.strptime(periode.date_end, '%Y-%m-%d') - datetime.strptime(periode.date_start, '%Y-%m-%d')).days
                if duree>88 and duree <92 and dec_year == datetime.strptime(periode.date_end, '%Y-%m-%d').year and dec_year == datetime.strptime(periode.date_start, '%Y-%m-%d').year:
                    ids.append(periode.id)
            return {'domain':{'date_range_id': [('id', 'in', ids)]}}
    @api.model
    def _get_domain(self):
        periodes = self.env['date.range'].search([])
        ids = []
        for periode in periodes :
            duree =  (datetime.strptime(periode.date_end, '%Y-%m-%d') - datetime.strptime(periode.date_start, '%Y-%m-%d')).days
            if duree>88 and duree <92:
                ids.append(periode.id)
        return [('id', 'in', ids)]
    
    @api.onchange('fiscal_date')
    def onchange_fiscal_date(self):
        if(self.fiscal_date):
            print self.fiscal_date
            date = str(datetime.strptime(self.fiscal_date, '%Y-%m-%d').year) + "-1-1"
            mydate = datetime.strptime(date, '%Y-%m-%d')
            self.fiscal_date = mydate    
           
    fiscal_date = fields.Date(string="Annee fiscale")
    date_range_id = fields.Many2one('date.range', 'Periode', domain=lambda self: self._get_domain())
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
            raise UserError(_('Pas de lignes facturables.'))

        for invoice in invoices.values():
            if not invoice.invoice_line_ids:
                raise UserError(_('Pas de lignes facturables.'))
        self.state = 'valide'
        return [inv.id for inv in invoices.values()]
    
    @api.multi
    def _prepare_invoice(self):
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Veuillez definir un compte journal pour votre Ste.'))
        invoice_vals = {
            'name': self.collectivite_id.name ,
            'origin':self.collectivite_id.name,
            'cotisation_id.id' : self.id,
            'type': 'out_invoice',
            'cotisation_id': self.id,
            'account_id': self.collectivite_id.property_account_receivable_id.id,
            'partner_id': self.collectivite_id.id,
            'journal_id': journal_id,
            'date_invoice' : self.date_range_id.date_end,
            'residual_signed' : self.montant
        }
        return invoice_vals
  

class cotisation_assure(models.Model):
    _name = 'cmim.cotisation.assure'
    _description = "Cotisation Assure"

    def _getmontant_total(self):
        self.montant = sum(line.montant for line in self.cotisation_assure_line_ids)
        
        
    cotisation_id = fields.Many2one('cmim.cotisation', 'Cotisation',  ondelete='cascade')
    collectivite_id = fields.Many2one('res.partner',related='cotisation_id.collectivite_id', store=True)
    assure_id = fields.Many2one('cmim.assure', 'Assure', domain="[('collectivite_id', '=','collectivite_id' ]")
    name =  fields.Char('Libelle')
    cotisation_assure_line_ids = fields.One2many('cmim.cotisation.assure.line', 'cotisation_assure_id', 'Ligne de calcul par assure')  
    montant = fields.Float(compute="_getmontant_total", string='Montant', default= 0.0, digits=0, store=True)
    #montant = fields.Float(string='Montant', default= 0.0)

class cotisation_assure_line(models.Model):
    _name = 'cmim.cotisation.assure.line'
    _description = "Lignes ou details du calcul des cotisations_assure"
    _order = 'cotisation_assure_id'

    cotisation_assure_id = fields.Many2one('cmim.cotisation.assure', 'Cotisation assure',  ondelete='cascade')
    cotisation_id = fields.Many2one('cmim.cotisation', string='Cotisation',related='cotisation_assure_id.cotisation_id', store=True)
    assure_id = fields.Many2one('cmim.assure', string='Assure',related='cotisation_assure_id.assure_id', store=True )
    
    product_id = fields.Many2one('product.template', 'Produit')
    code = fields.Char('Code Produit')
    type_product_id = fields.Many2one("cmim.product.type", string='Type de produit' )
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
    product_id = fields.Many2one('product.template', 'Produit') 
    code = fields.Char('Code Produit')
    type_product_id = fields.Many2one("cmim.product.type", string='Type de produit' )
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
