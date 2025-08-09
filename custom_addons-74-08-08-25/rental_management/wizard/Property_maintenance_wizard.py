# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class PropertyMaintenance(models.TransientModel):
    _name = 'maintenance.wizard'
    _description = 'Crating Maintenance Request'

    name = fields.Char(string='Request')
    property_id = fields.Many2one('property.details', string='Property')
    maintenance_type_id = fields.Many2one('product.template', string='Type', domain=[('is_maintenance', '=', True)])
    maintenance_team_id = fields.Many2one('maintenance.team', string='Team')

    def maintenance_request(self):
        if self.property_id.is_parent_property:
            data = {
                'name': self.name,
                'maintenance_type_id': self.maintenance_type_id.id,
                'maintenance_team_id': self.maintenance_team_id.id,
                'landlord_id': self.property_id.parent_landlord_id.id,
                'property_id': self.property_id.id,
                'request_date': fields.Date.today()
            }
            maintenance_id = self.env['maintenance.request'].create(data)
        else:
            data = {
                'name': self.name,
                'landlord_id': self.property_id.landlord_id.id,
                'maintenance_type_id': self.maintenance_type_id.id,
                'maintenance_team_id': self.maintenance_team_id.id,
                'property_id': self.property_id.id,
                'request_date': fields.Date.today()
            }
            maintenance_id = self.env['maintenance.request'].create(data)
        return True
