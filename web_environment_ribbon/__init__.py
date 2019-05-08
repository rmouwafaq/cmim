# -*- coding: utf-8 -*-
# Copyright 2015 Francesco OpenCode Apruzzese <cescoap@gmail.com>
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2017 Thomas Binsfeld <thomas.binsfeld@acsone.eu>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from . import models
from openerp import api, SUPERUSER_ID

def get_database_uuid(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ir_config_model = env['ir.config_parameter']
    db_uuid = ir_config_model.sudo().get_param('database.uuid')
    ir_config_model.sudo().set_param('ribbon.production.database.uuid',db_uuid)