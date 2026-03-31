import calendar
from odoo import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    present_days = fields.Float(string="Present Days", compute="_compute_attendance_summary", store=True)
    el_days = fields.Float(string="EL Used", compute="_compute_attendance_summary", store=True)
    lop_days = fields.Float(string="LOP Taken", compute="_compute_attendance_summary", store=True)
    wo_days = fields.Float(string="W/O Days", compute="_compute_attendance_summary", store=True)
    month_days = fields.Integer(string="Month Days", compute="_compute_attendance_summary", store=True)

    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_attendance_summary(self):
        HrUpload = self.env['hr.upload']
        HrLeave = self.env['hr.leave']

        for slip in self:
            slip.present_days = 0.0
            slip.el_days = 0.0
            slip.lop_days = 0.0
            slip.wo_days = 0.0
            slip.month_days = 0

            if not slip.employee_id or not slip.date_from or not slip.date_to:
                continue

            # ------------------------------------------------
            # Month days
            # ------------------------------------------------
            slip.month_days = calendar.monthrange(
                slip.date_from.year,
                slip.date_from.month
            )[1]

            # ------------------------------------------------
            # Attendance (hr.upload)
            # ------------------------------------------------
            uploads = HrUpload.search([
                ('employee_id', '=', slip.employee_id.id),
                ('attendance_date', '>=', slip.date_from),
                ('attendance_date', '<=', slip.date_to),
            ])

            for att in uploads:
                if att.status in ('present', 'od', 'pm'):
                    slip.present_days += 1.0

                elif att.status == 'wo':
                    slip.wo_days += 1.0

                elif att.status in ('half_lp_pr', 'half_lp_pm'):
                    slip.present_days += 0.5

                elif att.status in ('half_pr_lp', 'half_pm_lp'):
                    slip.present_days += 0.5

            # ------------------------------------------------
            # Leaves (hr.leave)
            # ------------------------------------------------
            leaves = HrLeave.search([
                ('employee_id', '=', slip.employee_id.id),
                # ('state', '=', 'validate'),
                ('request_date_from', '>=', slip.date_from),
                ('request_date_to', '<=', slip.date_to),
            ])

            for leave in leaves:
                code = leave.holiday_status_id.work_entry_type_id.code
                days = leave.number_of_days

                if code == 'LEAVE120':     # EL
                    slip.el_days += days
                elif code == 'LEAVE90':    # LOP
                    slip.lop_days += days
