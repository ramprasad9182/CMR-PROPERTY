from odoo import models, fields

class HrEmployeeLoan(models.Model):
    _name = 'hr.employee.loan'
    _description = 'Employee Loan / Advance'
    _order = 'from_date desc'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade'
    )

    from_date = fields.Date(
        string='From Date',
    )

    to_date = fields.Date(
        string='To Date',
    )

    loan_amount = fields.Float(
        string='Loan / Advance Amount',
    )

    remarks = fields.Char(string='Remarks')
