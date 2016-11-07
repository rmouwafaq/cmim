
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields,exceptions, api, _
from openerp.exceptions import UserError

class constante_calcul(models.Model):
    _name = 'cmim.constante'
    name = fields.Char('Nom ', required=True)
    valeur = fields.Char('Valeur ', required=True)



class reglement(models.Model):
    _inherit = 'account.payment'
    _default = { 'payment_type' : 'inbound',
                'partner_type': 'customer',
                }
    import_flag = fields.Boolean('Par import', default=False)
    secteur_id = fields.Many2one('cmim.secteur',
        string='Secteur',
        related='partner_id.secteur_id', store=True
    )
    payroll_year_id =  fields.Many2one('py.year', 'Calendrier')
    payroll_period_id = fields.Many2one('py.period', 'Periode', domain="[('payroll_year_id','=',payroll_year_id)]")
    
    
class declaration(models.Model):
    _name = 'cmim.declaration'
    
    def _getsalaire_mensuel(self):
        for dec in self:
            dec.sal_men  = (dec.salaire/dec.nb_jour)*30

    import_flag = fields.Boolean('Par import', default=False)      
    assure_id =  fields.Many2one('cmim.assure', 'Assure', ondelete='cascade')#domain=[('collectivite_id.id','=',collectivite_id.id)] , 
    collectivite_id = fields.Many2one('res.partner', 'Collectivite', ondelete='cascade')
    nb_jour = fields.Integer('Nombre de jours declares')
    salaire = fields.Float('salaire')
    payroll_year_id =  fields.Many2one('py.year', 'Calendrier')
    payroll_period_id = fields.Many2one('py.period', 'Periode', domain="[('payroll_year_id','=',payroll_year_id)]")
    sal_men = fields.Float(compute="_getsalaire_mensuel", string='Returned', default= 0.0, digits=0, store=True)
    
class cotisation(models.Model):
    _name = 'cmim.cotisation'
    _description = "Cotisation"

    def _getmontant_total(self):
        for cotisation in self:
            cotisation.montant = 0.0
            for line in cotisation.cotisation_line_ids:
                cotisation.montant = cotisation.montant + line.montant

    
    payroll_year_id = fields.Many2one('py.year', 'Calendrier')
    payroll_period_id = fields.Many2one('py.period', 'Periode de calcul', domain="[('payroll_year_id','=',payroll_year_id)]")
    collectivite_id = fields.Many2one('res.partner', 'Collectivite')
    assure_id = fields.Many2one('cmim.assure', 'Assure')
    name =  fields.Char('Libelle')
    cotisation_line_ids = fields.One2many('cmim.cotisation.line', 'cotisation_id', 'Ligne de calcul')   
    state = fields.Selection(selection=[('draft', 'Brouillon'),
                                        ('valide', 'Validee')],
                                        required=True,
                                        string='Etat', 
                                        default = 'draft')

    montant = fields.Float(compute="_getmontant_total", string='Returned', default= 0.0, digits=0, store=True)

class cotisation_line(models.Model):
    _name = 'cmim.cotisation.line'
    _description = "Lignes ou details du calcul des cotisations"
    _order = 'cotisation_id,sequence'

    cotisation_id = fields.Many2one('cmim.cotisation', 'Cotisation')
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
    
     
class calcul_cotisation (models.TransientModel):
    _name = 'cmim.calcul.cotisation'
    
    @api.one
    def _get_collectivite_ids(self):
        """cr = self.pool.cursor()
        self.env
        return self.pool.get('sale.order.printorder').search("""
        return self.env['res.partner'].search([])
    payroll_year_id =  fields.Many2one('py.year', 'Calendrier')
    payroll_period_id = fields.Many2one('py.period', 'Periode', domain="[('payroll_year_id','=',payroll_year_id)]")
    collectivite_ids = fields.Many2many('res.partner','calcul_cotisation_collectivite', 'calcul_id', 'partner_id', "Collectivites", domain = "[('customer','=',True),('is_company','=',True)]",default=_get_collectivite_ids)
    
    @api.multi
    def can_calculate(self):
        collectivities = []
        for col in self.collectivite_ids:
            collectivities.append(col.id)
        if(self.env['cmim.cotisation'].search([('collectivite_id.id','in',collectivities), 
                                               ('state','=','valide'),
                                               ('payroll_year_id.id','=',self.payroll_year_id.id),
                                               ('payroll_period_id.id','=',self.payroll_period_id.id)])):
            return False
        else:
            return True
    
    @api.multi
    def calcul_per_assure(self, declaration_id, contrat_ids, cotisation_obj):
        """
        base= fields.Float('Base de calcul')
        taux1 = fields.Float('Taux 1')
        taux2 = fields.Float('Taux 2')
        montant = fields.Float('Montant') 
        """
        cte_cnss = self.env['cmim.constante'].search([('name', '=', 'CNSS')])
        cte_sfp = self.env['cmim.constante'].search([('name', '=', 'SRP')])
        sal_men = (declaration_id.salaire/declaration_id.nb_jour)*30  
        for contrat in contrat_ids:
            cotisation_line_dict = {'product_id': contrat.product_id.id}
            
            if contrat.product_id.base_calcul == 'salaire':
                if(contrat.tarif_id.type == 'p'):
                    cotisation_line_dict['taux1'] = contrat.tarif_id.montant
                    if(sal_men < declaration_id.collectivite_id.secteur_id.plancher):
                        b_plancher = declaration_id.collectivite_id.secteur_id.plancher
                    else: 
                        b_plancher = sal_men
                    if( b_plancher < declaration_id.collectivite_id.secteur_id.plafond):
                        b_plafonnee = b_plancher
                    else:
                        b_plafonnee = declaration_id.collectivite_id.secteur_id.plafond
                    cotisation_line_dict['base1'] = b_plafonnee
                    cotisation_line_dict['montant'] = (b_plafonnee * contrat.tarif_id.montant)/ 100
                    print cotisation_line_dict
            else:
                if(cte_cnss.valeur > sal_men):
                    trancheA = sal_men
                else: 
                    trancheA = cte_cnss.valeur                
                if(sal_men > trancheA):
                    res = trancheA
                else : 
                    res = 0.0
                if(res > cte_sfp.valeur):
                    trancheB = cte_sfp.valeur
                else: 
                    trancheB = res
                cotisation_line_dict['base1'] = trancheA
                cotisation_line_dict['base2'] = trancheB  
                cotisation_line_dict['taux1'] = contrat.tarif_inc_deces_id.montant
                cotisation_line_dict['taux2'] = contrat.tarif_inv_id.montant
                cotisation_line_dict['montant'] = (trancheA * contrat.tarif_inc_deces_id.montant + trancheB * contrat.tarif_inv_id.montant) / 100
            cotisation_obj.write({'cotisation_line_ids':   [(0, 0, cotisation_line_dict)]})
        print '\n\n' 
        return True
    
    @api.multi 
    def calcul_engine(self):
        if(not self.can_calculate()):
            raise exceptions.Warning(
                _("vous avez valide des cotisations pour une ou plusieurs collectivites. \nImpossible de lancer le calcul pour les meme periodes"))
        else: 
            for col in self.collectivite_ids:
                declaration_ids = self.env['cmim.declaration'].search([('collectivite_id.id','=',col.id),('payroll_year_id.id','=',self.payroll_year_id.id),('payroll_period_id.id','=',self.payroll_period_id.id)])
                for declaration_id in declaration_ids:
                    cotisation_obj = self.env['cmim.cotisation'].create({  'payroll_year_id': self.payroll_year_id.id,
                                                                           'payroll_period_id': self.payroll_period_id.id,
                                                                           'collectivite_id': col.id,
                                                                           'assure_id': declaration_id.assure_id.id})
                    if(not declaration_id.assure_id.is_normal):
                        contrat_ids = self.env['cmim.contrat'].search([('assure_id.id','=',declaration_id.assure_id.id)])
                    else:
                        contrat_ids = self.env['cmim.contrat'].search([('collectivite_id.id','=',declaration_id.collectivite_id.id)])
                    self.calcul_per_assure(declaration_id, contrat_ids, cotisation_obj) 
        return True
    
        
   





