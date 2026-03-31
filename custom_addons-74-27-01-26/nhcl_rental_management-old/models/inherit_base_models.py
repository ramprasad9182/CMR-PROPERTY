from odoo import fields, api, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    tenant_type = fields.Many2one('tenant.type', string="Tenancy Type")
    adhar_no = fields.Char(string='Adhar No')
    director_name = fields.Char(string='Director Name')
    din_no = fields.Char(string='Din No')
    nhcl_pan_no = fields.Char(string='Pan No')
    nhcl_res_cin_no = fields.Char(string='Cin No')


class Comapny(models.Model):
    _inherit = 'res.company'

    nhcl_com_cin_no = fields.Char(string='Cin No')
    nhcl_com__director_name = fields.Char(string='Director Name')
    nhcl_com_din_no = fields.Char(string='Din No')
    nhcl_com_adhar_no = fields.Char(string='Adhar No')





# class PurchaseRequisitionInherited(models.Model):
#     _inherit = 'purchase.requisition'
#
#     # Define state_blanket_order with appropriate options
#     state_blanket_order = fields.Selection(Selection_add=([
#         ('approval1', 'Approval1'),
#         ('approval2', 'Approval2'),
#         ('ongoing',),
#     ]), string="Blanket Order State")
#
#     # Define state with appropriate options
#     state = fields.Selection(Selection_add=([
#         ('approval1', 'Approval1'),
#         ('approval2', 'Approval2'),
#         ('ongoing',),
#     ]), string="State", default='draft')
#
#     def _onchange_price_unit(self):
#         print(self.state)
#         print(self.state_blanket_order)
#         if self.state not in ['approval1', 'approval2']:
#             self.state = 'approval1'
#             print('after the update ',self.state)
#             # self.state_blanket_order = 'approval1'
#
#         # if self.state == 'approval1' and self.state_blanket_order != 'approval2':
#         #     self.state_blanket_order = 'approval2'
# #
# #     @api.onchange('line_ids')
# #     # def _onchange_line_ids(self):
# #     #     # Call the price unit change handler
# #     #     self._onchange_price_unit()
#
#     def action_approve(self):
#         print(self.state_blanket_order)
#         if self.state == 'approval1':
#             self.state = 'approval2'
#             self.state_blanket_order = 'approval1'
#         elif self.state == 'approval2':
#             self.state = 'ongoing'
#             # self.state_blanket_order = 'ongoing'
#
#     def action_cancel(self):
#         self.state = 'cancel'
#         self.state_blanket_order = 'cancel'
