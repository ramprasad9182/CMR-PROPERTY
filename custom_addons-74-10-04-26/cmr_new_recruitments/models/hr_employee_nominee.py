import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrEmployeeNominee(models.Model):
    _name = "hr.employee.nominee"
    _description = "Employee Nominee"
    _order = 'sequence'

    employee_id = fields.Many2one('hr.employee', string="Employee", ondelete='cascade')
    sequence = fields.Integer(string="S.No")
    nominee_name = fields.Char(string="Nominee")
    dob = fields.Date(string="Date of Birth")
    aadhar_no = fields.Char(string="Aadhar Number")
    relationship = fields.Selection([
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('husband', 'Husband'),
        ('wife', 'Wife'),
        ('brother', 'Brother'),
        ('sister', 'Sister'),
        ('son', 'Son'),
        ('daughter', 'Daughter'),
    ], string="Relationship")
    percentage = fields.Float(string="Percentage")
    applicant_employee_id = fields.Many2one('hr.applicant', string="Employee", ondelete='cascade')

    @api.constrains('aadhar_no')
    def _check_aadhar_number(self):
        for rec in self:
            if rec.aadhar_no:
                if not re.match(r'^\d{12}$', rec.aadhar_no):
                    raise ValidationError(
                        "Aadhaar number must contain only numeric digits and must be exactly 12 digits.(Nominee Details)"
                    )

    @api.constrains('percentage', 'employee_id')
    def _check_total_percentage(self):
        for record in self:
            if record.employee_id:
                total = sum(self.env['hr.employee.nominee'].search([
                    ('employee_id', '=', record.employee_id.id)
                ]).mapped('percentage'))
                # Exclude the current record when editing (to avoid counting it twice)
                if self.id:
                    total -= record.percentage
                    total += record.percentage

                if total > 100:
                    raise ValidationError("Total nominee percentage cannot exceed 100%.")