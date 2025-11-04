from odoo import fields, models, api
from odoo.exceptions import UserError


class PropertyDetails(models.Model):
    _inherit = 'property.details'

    mall_matrix_ids = fields.One2many('mall.demo', 'mall_id')
    mall_mix_total = fields.Integer(string='Total Square feet', compute='_compute_mall_mix_total', store=True)

    @api.depends('mall_matrix_ids')
    def _compute_mall_mix_total(self):
        total = 0
        for rec in self:
            if rec.mall_matrix_ids:
                for data in rec.mall_matrix_ids:
                    total = total + data.mall_carpet_area
                    rec.mall_mix_total = total
            else:
                rec.mall_mix_total = 0


class FloorPlan(models.Model):
    _inherit = 'floor.plan'  # This is incorrect. _inherits must be a dictionary.

    floor_no = fields.Selection(
        [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7')],
        string='Floor Number',
    )
    total_sft = fields.Float(string='Total ft²')
    status = fields.Selection([('active', 'Active'), ('inactive', 'Inactive')], string='Status')
    tenancy = fields.Many2one('tenancy.details', string='Tenancy ID')
    from odoo.exceptions import UserError
    from odoo import api, models

    @api.onchange('total_sft')
    def check_value_total(self):
        v = 0
        rec = self.env['property.commercial.measurement'].search([
            ('commercial_measurement_id.name', '=', self.property_id.name)
        ])

        for r in rec:
            if int(self.floor_no) == r.no_of_unit:
                print(r.carpet_area)
                print(self.total_sft)

                data = self.env['floor.plan'].search([
                    ('floor_no', '=', str(r.no_of_unit))
                ])

                for value in data:
                    if rec.commercial_measurement_id.name == value.property_id.name:
                        v += value.total_sft
                        print(v, "inside")
                v=v+self.total_sft

                # print(self.total_sft, "////", v)

                if (self.total_sft <= r.carpet_area) and (int(self.floor_no) == r.no_of_unit) and(v <= r.carpet_area):
                    pass
                else:
                    raise UserError('Total Square Feet cannot be greater than Area.')

    # @api.model
    # def create(self, vals):
    #     """Overrides the create method to validate total_sft before saving."""
    #     record = super(FloorPlan, self).create(vals)
    #     record.check_value_total()  # Ensure validation is applied on creation
    #     return record
    #
    # def write(self, vals):
    #     """Overrides the write method to validate total_sft when updating records."""
    #     result = super(FloorPlan, self).write(vals)
    #     self.check_value_total()  # Ensure validation is applied on update
    #     return result


"""
    floor_no=fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),('7','7')],string='Floor Number')
    total_sft=fields.Float(string='Total ft²')
    status=fields.Selection([('active','Running'),('inactive','Closed')],string='Status')
    tenancy=fields.Many2one('tenancy.details',string='Tenancy Id')  """
