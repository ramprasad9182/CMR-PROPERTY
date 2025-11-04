# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class pos_custom_screen(models.Model):
#     _name = 'pos_custom_screen.pos_custom_screen'
#     _description = 'pos_custom_screen.pos_custom_screen'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

