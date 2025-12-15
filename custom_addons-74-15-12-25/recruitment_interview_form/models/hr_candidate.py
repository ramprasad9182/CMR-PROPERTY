from odoo import models, fields, api


class HRCandidate(models.Model):
    _inherit = 'hr.candidate'

    multi_company_ids = fields.Many2many('res.company', string='Preferred Companies')