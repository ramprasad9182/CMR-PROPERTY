from dateutil.relativedelta import relativedelta

from odoo import models, fields ,api
from odoo.exceptions import UserError

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
    months = fields.Integer(
        string="No of Months",
        compute="_compute_months",
        store=True
    )
    monthly_installment = fields.Float(
        string="Monthly Deduction",
        compute="_compute_monthly_installment",
        store=True
    )

    remarks = fields.Char(string='Remarks')

    @api.depends('from_date', 'to_date')
    def _compute_months(self):
        for rec in self:
            if rec.from_date and rec.to_date:
                diff = relativedelta(rec.to_date, rec.from_date)
                rec.months = diff.years * 12 + diff.months + 1
            else:
                rec.months = 0

    @api.depends('loan_amount', 'months')
    def _compute_monthly_installment(self):
        for rec in self:
            if rec.loan_amount and rec.months:
                rec.monthly_installment = rec.loan_amount / rec.months
            else:
                rec.monthly_installment = 0

    def write(self, vals):
        if not self.env.user.has_group('cmr_new_recruitments.group_hr_applicant_loan'):
            raise UserError("You are not allowed to edit Employee Loan.")
        return super().write(vals)
