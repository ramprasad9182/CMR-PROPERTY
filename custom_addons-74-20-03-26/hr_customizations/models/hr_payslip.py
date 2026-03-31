import calendar
from odoo import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    present_days = fields.Float(string="Present Days", compute="_compute_attendance_summary", store=True)
    el_days = fields.Float(string="EL Used", compute="_compute_attendance_summary", store=True)
    lop_days = fields.Float(string="LOP Taken", compute="_compute_attendance_summary", store=True)
    wo_days = fields.Float(string="W/O Days", compute="_compute_attendance_summary", store=True)
    month_days = fields.Integer(string="Month Days", compute="_compute_attendance_summary", store=True)
    public_holiday_days = fields.Integer(
        string='Public Holidays',
        compute='_compute_public_holiday_days',
        store=True
    )
    el_left = fields.Float(
        string="EL Left (Slab Based)",
        compute="_compute_el_left",
        store=True
    )
    ns_total_amount = fields.Float(
        string="Night Shift Amount",
        compute="_compute_attendance_summary",
        store=True
    )

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_el_left(self):
        HrUpload = self.env['hr.upload']
        HrLeave = self.env['hr.leave']

        el_type = self.env['hr.leave.type'].search(
            [('work_entry_type_id.code', '=', 'LEAVE120')],
            limit=1
        )

        for slip in self:
            emp = slip.employee_id
            start = slip.date_from
            end = slip.date_to

            if not emp or not start or not end or not el_type:
                slip.el_left = 0
                continue

            # ---------------------------------
            # 1. EL EARNED FROM SLABS
            # ---------------------------------
            uploads = HrUpload.search([
                ('employee_id', '=', emp.id),
                ('attendance_date', '>=', start),
                ('attendance_date', '<=', end),
            ])

            rec_map = {r.attendance_date.day: r for r in uploads}
            slabs = [(1, 10), (11, 20), (21, end.day)]

            earned = 0
            for s, e in slabs:
                for d in range(s, e + 1):
                    rec = rec_map.get(d)
                    if rec and not (
                            rec.morning_session == 'absent'
                            and rec.afternoon_session == 'absent'
                    ):
                        earned += 1
                        break

            # ---------------------------------
            # 2. EL TAKEN
            # ---------------------------------
            leaves = HrLeave.search([
                ('employee_id', '=', emp.id),
                ('holiday_status_id', '=', el_type.id),
                ('state', '=', 'validate'),
                ('request_date_from', '<=', end),
                ('request_date_to', '>=', start),
            ])

            taken = 0
            for l in leaves:
                if l.request_unit_half:
                    taken += 0.5
                else:
                    taken += (l.request_date_to - l.request_date_from).days + 1

            # ---------------------------------
            # 3. FINAL LEFT
            # ---------------------------------
            slip.el_left = max(earned - taken, 0)

    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_public_holiday_days(self):
        CalendarLeave = self.env['resource.calendar.leaves']

        for slip in self:
            ph_days = 0  # INTEGER

            if not slip.date_from or not slip.date_to or not slip.employee_id:
                slip.public_holiday_days = 0
                continue

            calendar = slip.employee_id.resource_calendar_id
            if not calendar:
                slip.public_holiday_days = 0
                continue

            holidays = CalendarLeave.search([
                ('calendar_id', '=', calendar.id),
                ('resource_id', '=', False),
                ('date_from', '<=', slip.date_to),
                ('date_to', '>=', slip.date_from),
            ])

            for holiday in holidays:
                start = max(fields.Date.to_date(holiday.date_from), slip.date_from)
                end = min(fields.Date.to_date(holiday.date_to), slip.date_to)
                ph_days += (end - start).days + 1

            slip.public_holiday_days = int(ph_days)

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
            slip.ns_total_amount = 0.0

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
            # Fast NS Total Calculation
            slip.ns_total_amount = sum(uploads.mapped('ns_amount'))

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
