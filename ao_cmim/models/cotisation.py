
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields,exceptions, api, _
from openerp.exceptions import UserError

class constante_calcul(models.Model):
    _name = 'cmim.constante'
    name = fields.Char('Nom ', required=True)
    valeur = fields.Char('Valeur ', required=True)
  
    
class declaration(models.Model):
    _name = 'cmim.declaration'
    
    import_flag = fields.Boolean('Par import', default=False)      
    assure_id =  fields.Many2one('cmim.assure', 'Assure', ondelete='cascade')#domain=[('collectivite_id.id','=',collectivite_id.id)] , 
    collectivite_id = fields.Many2one('res.partner', 'Collectivite', ondelete='cascade')
    nb_jour = fields.Integer('Nombre de jours declares')
    salaire = fields.Float('salaire')
    payroll_year_id =  fields.Many2one('py.year', 'Calendrier')
    payroll_period_id = fields.Many2one('py.period', 'Periode', domain="[('payroll_year_id','=',payroll_year_id)]")
    

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
     
class calcul_cotisation (models.TransientModel):
    _name = 'cmim.calcul.cotisation'
    
    payroll_year_id =  fields.Many2one('py.year', 'Calendrier')
    payroll_period_id = fields.Many2one('py.period', 'Periode', domain="[('payroll_year_id','=',payroll_year_id)]")
    collectivite_ids = fields.Many2many('res.partner','calcul_cotisation_collectivite', 'calcul_id', 'partner_id', "Collectivites", domain = "[('customer','=',True),('is_company','=',True)]")
    
    
    @api.multi
    def create_cotisation_product_lines(self, cotisation_obj):
        cotisation_assure_lines = self.env['cmim.cotisation.assure.line'].search([('cotisation_id.id','=', cotisation_obj.id)])
        cotisation_product_obj = self.env['cmim.cotisation.product']
        print len(cotisation_assure_lines)
        for line in cotisation_assure_lines:
            cotisation_product_obj = cotisation_product_obj.search([('cotisation_id.id', '=', cotisation_obj.id), ('product_id.id', '=', line.product_id.id)])
            
            if(cotisation_product_obj):
                cotisation_product_obj.write({'montant': cotisation_product_obj.montant + line.montant})
            else:
                cotisation_product_obj = cotisation_product_obj.create({'cotisation_id': cotisation_obj.id,
                                                                        'product_id': line.product_id.id,
                                                                        'montant' : line.montant
                                                                        })
                cotisation_obj.write({'cotisation_product_ids': [(4,cotisation_product_obj.id)]})
        return True
    
    
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
        elif (self.env['cmim.cotisation'].search([('collectivite_id.id','in',collectivities), 
                                               ('state','=','draft'),
                                               ('payroll_year_id.id','=',self.payroll_year_id.id),
                                               ('payroll_period_id.id','=',self.payroll_period_id.id)])) :
            for col in collectivities:        
                self._cr.execute(" DELETE FROM cmim_cotisation c where c.collectivite_id = %s and c.state = 'draft' and c.payroll_year_id = %s and c.payroll_period_id = %s", (col,self.payroll_year_id.id, self.payroll_period_id.id))
            return True
        else:
            return True
        
    
    @api.multi
    def calcul_per_assure(self, declaration_id, contrat_ids, cotisation_assure_obj):

        cte_cnss = self.env['cmim.constante'].search([('name', '=', 'CNSS')])
        cte_sfp = self.env['cmim.constante'].search([('name', '=', 'SRP')])
        sal_men = (declaration_id.salaire/declaration_id.nb_jour)*30
          
        for contrat in contrat_ids:
            cotisation_line_dict = {'product_id': contrat.product_id.id,
                                    'cotisation_assure_id' : cotisation_assure_obj.id}
            
            if contrat.product_id.base_calcul == 'salaire':
                if(contrat.tarif_id.type == 'p'):
                    cotisation_line_dict['rate1'] = contrat.tarif_id.montant
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
                else: 
                    cotisation_line_dict['montant']  = 0.0
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
                cotisation_line_dict['rate1'] = contrat.tarif_inc_deces_id.montant
                cotisation_line_dict['rate2'] = contrat.tarif_inv_id.montant
                cotisation_line_dict['montant'] = (trancheA * contrat.tarif_inc_deces_id.montant + trancheB * contrat.tarif_inv_id.montant) / 100
            cotisation_assure_obj.write({'cotisation_assure_line_ids':   [(0, 0, cotisation_line_dict)],
                                         'montant': cotisation_assure_obj.montant + cotisation_line_dict['montant']})
        return True
    
    
    @api.multi 
    def calcul_engine(self):
        if(not self.can_calculate()):
            raise exceptions.Warning(
                _("vous avez valide des cotisations pour une ou plusieurs collectivites. \nImpossible de lancer le calcul pour les meme periodes"))
        else: 
            cotisation_ids = []
            for col in self.collectivite_ids:
                cotisation_obj = self.env['cmim.cotisation'].create({  'payroll_year_id': self.payroll_year_id.id,
                                                                       'payroll_period_id': self.payroll_period_id.id,
                                                                       'collectivite_id': col.id
                                                                       })
                declaration_ids = self.env['cmim.declaration'].search([('collectivite_id.id','=',col.id),('payroll_year_id.id','=',self.payroll_year_id.id),('payroll_period_id.id','=',self.payroll_period_id.id)])
                for declaration_id in declaration_ids:
                    
                    cotisation_assure_obj = self.env['cmim.cotisation.assure'].create({    'cotisation_id': cotisation_obj.id,
                                                                                           'collectivite_id': col.id,
                                                                                           'assure_id': declaration_id.assure_id.id})
                    cotisation_obj.write({'cotisation_assure_ids':   [(4, cotisation_assure_obj.id)]})
                    if(not declaration_id.assure_id.is_normal):
                        contrat_ids = self.env['cmim.contrat'].search([('assure_id.id','=',declaration_id.assure_id.id)])
                    else:
                        contrat_ids = self.env['cmim.contrat'].search([('collectivite_id.id','=',declaration_id.collectivite_id.id)])
                    self.calcul_per_assure(declaration_id, contrat_ids, cotisation_assure_obj)
                    cotisation_obj.write({'montant': cotisation_obj.montant + cotisation_assure_obj.montant})
                self.create_cotisation_product_lines(cotisation_obj)
                cotisation_ids.append(cotisation_obj.id)
                print 'pppppppppppppppppppppppppppppppppppppppppp',cotisation_ids
            return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'cmim.cotisation',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_id': self.id,
                    'view_id': 'ao_cmim.cotisation_tree_view',
                    'views': [(False, 'tree')],
                    'domain':[('id', 'in', cotisation_ids)],
                    'target':'self',
                }
    
        
   





