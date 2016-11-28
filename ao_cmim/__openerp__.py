# -*- coding: utf-8 -*-
{
    'name':'Comptabilité auxilière de la CMIM ',
    'author':'Agilorg',
    'website':'http://www.agilorg.com',
    'category': 'account',
    'description': """Comptabilité auxiliaire cmim""",
    'depends':['base','account','product'],
    'data':[
            'wizard/import_data.xml',
            
            'wizard/generate_rapport_correctif.xml',
            'wizard/calcul_cotisation.xml',
            'wizard/validation_cotisation.xml',
            
            'views/product.xml',
            'views/cotisation.xml',
            'views/collectivite.xml',
            'views/config.xml',
            'views/menu.xml',

    ],
    'installable':True,
    'auto_install':False,
    'application':True,
}
