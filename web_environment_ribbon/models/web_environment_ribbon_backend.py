# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class WebEnvironmentRibbonBackend(models.Model):

    _name = 'web.environment.ribbon.backend'
    _description = 'Web Environment Ribbon Backend'

    @api.model
    def _prepare_ribbon_name(self):
        db_name = self.env.cr.dbname
        name = self.env['ir.config_parameter'].get_param('ribbon.name')
        name = name.format(db_name=db_name)
        return name

    @api.model
    def get_environment_ribbon(self):
        """
        This method returns the ribbon data from ir config parameters
        :return: dictionary
        """
        ir_config_model = self.env['ir.config_parameter']
        name = self._prepare_ribbon_name()
        return {
            'name': name,
            'color': ir_config_model.get_param('ribbon.color'),
            'background_color': ir_config_model.get_param(
                'ribbon.background.color'),
        }

    @api.model
    def check_production_database(self):
        """
        This method checks the production database name from ir config parameters
        :return: dictionary
        """
        ir_config_model = self.env['ir.config_parameter']
        db_uuid = ir_config_model.get_param('database.uuid')
        if ir_config_model.get_param('ribbon.production.database.uuid') != db_uuid:
            self.deactivate_crons()
            return self.get_environment_ribbon()

        return False

    @api.model
    def deactivate_crons(self):
        """
        This method deactivate all crons if it is not the production database
        """
        ir_cron_model = self.env['ir.cron']
        crons = ir_cron_model.search([('active', '=', True)])
        if crons:
            crons.write({'active': False})