import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FamilyDetails(models.Model):
    _name = 'family.details'
    _description = 'Family Details'
    _order = 'sequence'

    sequence = fields.Integer(string="S.No")
    name = fields.Char(string="Name")
    dob = fields.Date(string="Date of Birth")
    aadhar_no = fields.Char(string="Aadhaar Number")
    relationship = fields.Selection([
        ('mother', 'Mother'),
        ('father', 'Father'),
        ('husband', 'Husband'),
        ('wife', 'Wife'),
        ('son', 'Son'),
        ('daughter', 'Daughter'),
        ('brother', 'Brother'),
        ('sister', 'Sister'),
    ], string="Relationship")

    employee_id = fields.Many2one('hr.employee', string='Employee')
    applicant_employee_id = fields.Many2one('hr.applicant', string='Employee')

    @api.constrains('aadhar_no')
    def _check_aadhar_number(self):
        for rec in self:
            if rec.aadhar_no:
                if not re.match(r'^\d{12}$', rec.aadhar_no):
                    raise ValidationError(
                        "Aadhaar number must contain only numeric digits and must be exactly 12 digits.(Nominee Details)"
                    )