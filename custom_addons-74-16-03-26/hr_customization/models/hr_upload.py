import datetime

from odoo import models, fields, api
import pytz


class AttendanceExcel(models.Model):
    _name = 'attendance.excel'
    _description = 'Attendance Excel Data'

    emp_code = fields.Char("Employee Code")
    emp_name = fields.Char("Employee Name")
    department = fields.Char("Department")
    att_date = fields.Date("Attendance Date")
    check_in = fields.Char("Check In")
    check_out = fields.Char("Check Out")
    total_time = fields.Char("Total Time")

    status = fields.Char("Status")

    first_session = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('pm', 'Punch Miss'),
    ], string="First Session", compute="_compute_sessions", store=True)

    second_session = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('pm', 'Punch Miss'),
    ], string="Second Session", compute="_compute_sessions", store=True)

    schedule_check_in = fields.Datetime(
        string="Schedule Check In",
        compute="_compute_schedule_time",
        store=True
    )

    schedule_check_out = fields.Datetime(
        string="Schedule Check Out",
        compute="_compute_schedule_time",
        store=True
    )

    overtime_hours = fields.Float(
        string="Overtime In Minutes",
        compute="_compute_overtime",
        store=True
    )

    overtime_amount = fields.Float(
        string="Overtime Amount",
        compute="_compute_overtime",
        store=True
    )

    def _time_to_float(self, time_str):
        h, m = time_str.strip().split(':')
        return int(h) + int(m) / 60.0

    @api.depends('att_date', 'first_session', 'second_session', 'emp_code')
    def _compute_schedule_time(self):
        Employee = self.env['hr.employee']
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')

        for rec in self:
            rec.schedule_check_in = False
            rec.schedule_check_out = False

            if not rec.att_date or not rec.emp_code:
                continue

            employee = Employee.search(
                [('barcode', '=', rec.emp_code)],
                limit=1
            )
            if not employee or not employee.resource_calendar_id:
                continue

            calendar = employee.resource_calendar_id
            weekday = str(rec.att_date.weekday())

            lines = calendar.attendance_ids.filtered(
                lambda a: a.dayofweek == weekday
                          and a.day_period in ('morning', 'afternoon')
            )

            morning = lines.filtered(lambda a: a.day_period == 'morning')
            afternoon = lines.filtered(lambda a: a.day_period == 'afternoon')

            def _to_dt(hour_float):
                hour = int(hour_float)
                minute = int(round((hour_float - hour) * 60))

                local_dt = datetime.datetime.combine(
                    rec.att_date,
                    datetime.time(hour, minute)
                )

                return (
                    user_tz.localize(local_dt)
                    .astimezone(pytz.UTC)
                    .replace(tzinfo=None)
                )

            # PM → treat as full present
            first = rec.first_session
            second = rec.second_session
            if first == 'pm' and second == 'pm':
                first = second = 'present'

            # FULL DAY
            if first == 'present' and second == 'present':
                if morning and afternoon:
                    rec.schedule_check_in = _to_dt(morning.hour_from)
                    rec.schedule_check_out = _to_dt(afternoon.hour_to)

            # MORNING ONLY
            elif first == 'present' and second == 'absent':
                if morning:
                    rec.schedule_check_in = _to_dt(morning.hour_from)
                    rec.schedule_check_out = _to_dt(morning.hour_to)

            # AFTERNOON ONLY
            elif first == 'absent' and second == 'present':
                if afternoon:
                    rec.schedule_check_in = _to_dt(afternoon.hour_from)
                    rec.schedule_check_out = _to_dt(afternoon.hour_to)

    # @api.depends('att_date', 'check_in', 'check_out')
    # def _compute_sessions_dt(self):
    #     for rec in self:
    #
    #         # -------- First Session --------
    #         if rec.att_date and rec.check_in:
    #             try:
    #                 h, m = rec.check_in.strip().split(':')
    #                 rec.first_session_dt = datetime.combine(
    #                     rec.att_date,
    #                     datetime.min.time()
    #                 ).replace(hour=int(h), minute=int(m))
    #             except Exception:
    #                 rec.first_session_dt = False
    #         else:
    #             rec.first_session_dt = False
    #
    #         # -------- Second Session --------
    #         if rec.att_date and rec.check_out:
    #             try:
    #                 h, m = rec.check_out.strip().split(':')
    #                 rec.second_session_dt = datetime.combine(
    #                     rec.att_date,
    #                     datetime.min.time()
    #                 ).replace(hour=int(h), minute=int(m))
    #             except Exception:
    #                 rec.second_session_dt = False
    #         else:
    #             rec.second_session_dt = False

    @api.depends('status')
    def _compute_sessions(self):
        for rec in self:
            status = (rec.status or '').strip()

            if status == 'Present':
                rec.first_session = 'present'
                rec.second_session = 'present'

            elif status == 'Absent':
                rec.first_session = 'absent'
                rec.second_session = 'absent'

            elif status == 'PM':
                rec.first_session = 'pm'
                rec.second_session = 'pm'

            elif status == '1/2PR+1/2LP':
                rec.first_session = 'present'
                rec.second_session = 'absent'

            elif status == '1/2LP+1/2PR':
                rec.first_session = 'absent'
                rec.second_session = 'present'

            else:
                rec.first_session = False
                rec.second_session = False

    def open_upload_wizard(self):
        return {
            'name': 'Upload Attendance Excel',
            'type': 'ir.actions.act_window',
            'res_model': 'attendance.excel.import.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    # @api.depends('check_out', 'schedule_check_out', 'emp_code')
    # def _compute_overtime(self):
    #     Employee = self.env['hr.employee']
    #
    #     for rec in self:
    #         rec.overtime_hours = 0.0
    #         rec.overtime_amount = 0.0
    #
    #         if not rec.check_out or not rec.schedule_check_out or not rec.emp_code:
    #             continue
    #
    #         # 🔹 Employee
    #         employee = Employee.search(
    #             [('barcode', '=', rec.emp_code)],
    #             limit=1
    #         )
    #         if not employee or not employee.resource_calendar_id:
    #             continue
    #
    #         calendar = employee.resource_calendar_id
    #
    #         # 🔹 check_out → float (19:05:00 → 19.08)
    #         try:
    #             check_out_float = rec._time_to_float(rec.check_out)
    #         except Exception:
    #             continue
    #
    #         # 🔹 schedule_check_out → float (18:00 → 18.0)
    #         sch_out = rec.schedule_check_out
    #         sch_out_float = sch_out.hour + sch_out.minute / 60.0
    #
    #         # 🔹 No overtime
    #         if check_out_float <= sch_out_float:
    #             continue
    #
    #         # 🔹 OT hours
    #         overtime_hours = check_out_float - sch_out_float
    #
    #         # 🔹 OT slabs
    #         masters = self.env['hr.overtime.master'].search([
    #             ('shift_id', '=', calendar.id)
    #         ])
    #
    #         overtime_amount = 0.0
    #
    #         for master in masters:
    #             slab_start = rec._time_to_float(master.start_time)
    #             slab_end = rec._time_to_float(master.end_time)
    #
    #             # ✅ Check if OT falls inside slab
    #             if slab_start <= check_out_float <= slab_end:
    #                 overtime_amount += master.amount
    #
    #         rec.overtime_hours = round(overtime_hours, 2)
    #         rec.overtime_amount = overtime_amount

    @api.depends('check_out', 'schedule_check_out', 'emp_code')
    def _compute_overtime(self):
        Employee = self.env['hr.employee']
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')

        for rec in self:
            rec.overtime_hours = 0.0
            rec.overtime_amount = 0.0

            if not rec.check_out or not rec.schedule_check_out or not rec.emp_code:
                continue

            employee = Employee.search(
                [('barcode', '=', rec.emp_code)],
                limit=1
            )
            if not employee or not employee.resource_calendar_id:
                continue

            # 🔹 check_out (local string → float)
            try:
                h, m, s = rec.check_out.split(':')
                check_out_float = int(h) + int(m) / 60.0
            except Exception:
                continue

            # 🔹 schedule_check_out (UTC → local → float)
            sch_local = pytz.UTC.localize(
                rec.schedule_check_out
            ).astimezone(user_tz)

            sch_out_float = sch_local.hour + sch_local.minute / 60.0

            # 🔹 no overtime
            if check_out_float <= sch_out_float:
                continue

            overtime_hours = check_out_float - sch_out_float

            masters = self.env['hr.overtime.master'].search([
                ('shift_id', '=', employee.resource_calendar_id.id)
            ])

            overtime_amount = 0.0
            for master in masters:
                slab_start = rec._time_to_float(master.start_time)
                slab_end = rec._time_to_float(master.end_time)

                if slab_start <= check_out_float <= slab_end:
                    overtime_amount += master.amount

            rec.overtime_hours = int(round(overtime_hours * 60))
            rec.overtime_amount = overtime_amount

