from odoo import models, fields

class AccountAssetAsset(models.Model):

    _inherit = 'account.asset.asset'

    employee_id_nhcl_xpath = fields.Many2one('hr.employee',string='Employee')


