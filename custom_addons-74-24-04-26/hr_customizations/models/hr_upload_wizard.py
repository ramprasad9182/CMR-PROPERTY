import base64
import io
import openpyxl
import calendar
from collections import defaultdict
from datetime import datetime, date, time, timedelta

import pytz
from odoo import models, fields, _
from odoo.exceptions import ValidationError


class HrAttendanceUploadWizard(models.TransientModel):
    _name = 'hr.attendance.upload.wizard'
    _description = 'Attendance Excel Upload Wizard'

    file = fields.Binary(string="Excel File", required=True)
    filename = fields.Char(string="File Name")

    STATUS_MAP = {
        'Present': 'present',
        'OD': 'od',
        'Absent': 'absent',
        '1/2LP+1/2PR': 'half_lp_pr',
        '1/2PR+1/2LP': 'half_pr_lp',
        '1/2PM+1/2LP': 'half_pm_lp',
        '1/2LP+1/2PM': 'half_lp_pm',
        'PM': 'pm',
        'W/O': 'wo',
    }

    # =====================================================
    # MAIN ENTRY
    # =====================================================
    def action_upload(self):

        HrUpload = self.env['hr.upload']
        HrEmployee = self.env['hr.employee']
        HrLeaveType = self.env['hr.leave.type']

        el_type = HrLeaveType.search(
            [('work_entry_type_id.code', '=', 'LEAVE120')], limit=1
        )
        lop_type = HrLeaveType.search(
            [('work_entry_type_id.code', '=', 'LEAVE90')], limit=1
        )

        if not el_type or not lop_type:
            raise ValidationError(_("EL / LOP Leave Types not configured"))

        emp_map = {
            str(e.barcode).strip(): e
            for e in HrEmployee.search([('barcode', '!=', False)])
        }

        wb = openpyxl.load_workbook(
            io.BytesIO(base64.b64decode(self.file)),
            read_only=True,
            data_only=True
        )
        sheet = wb.active

        seen = set()
        created_uploads = self.env['hr.upload']

        # ----------------------------
        # STEP 1: IMPORT ATTENDANCE
        # ----------------------------
        for row_no, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):

            barcode = str(row[1]).strip() if row[1] else False
            att_date = self._validate_date(row[9], row_no)
            status_txt = (row[17] or '').strip()
            shift = (row[10] or '').strip()

            if not barcode:
                continue

            if barcode not in emp_map:
                raise ValidationError(_("Row %s: Employee not found") % row_no)

            if status_txt not in self.STATUS_MAP:
                raise ValidationError(_("Row %s: Invalid status") % row_no)

            key = (barcode, att_date)
            if key in seen:
                raise ValidationError(_("Row %s: Duplicate attendance in Excel") % row_no)
            seen.add(key)

            if HrUpload.search([
                ('employee_id', '=', emp_map[barcode].id),
                ('attendance_date', '=', att_date),
            ], limit=1):
                raise ValidationError(_("Row %s: Attendance already exists") % row_no)

            # ----------------------------
            # NS Amount Logic
            # ----------------------------
            ns_amount = 0.0

            if shift.upper() == 'P/C':
                # If both sessions absent → amount = 0
                if (
                        self.STATUS_MAP[status_txt] == 'absent'
                ):
                    ns_amount = 0.0
                else:
                    ns_amount = 100.0

            created_uploads |= HrUpload.create({
                'employee_id': emp_map[barcode].id,
                'attendance_date': att_date,
                'status': self.STATUS_MAP[status_txt],
                'check_in': self._combine(att_date, row[12]),
                'check_out': self._combine(att_date, row[14]),
                'total_time': self._time_to_hhmm(row[16]),
                'ns_amount': ns_amount,
            })

        # ----------------------------
        # STEP 2: APPLY EL / LOP
        # ----------------------------
        self._apply_el_lop(created_uploads, el_type, lop_type)

        return {'type': 'ir.actions.act_window_close'}

    # =====================================================
    # EL / LOP ENGINE (FINAL)
    # =====================================================
    def _apply_el_lop(self, uploads, el_type, lop_type):

        HrLeave = self.env['hr.leave']
        Allocation = self.env['hr.leave.allocation']

        emp_month_map = defaultdict(list)
        for r in uploads:
            emp_month_map[(r.employee_id.id, r.attendance_date.year, r.attendance_date.month)].append(r)

        alloc_cache = {}

        for (_, year, month), recs in emp_month_map.items():

            emp = recs[0].employee_id
            recs = sorted(recs, key=lambda r: r.attendance_date)

            start = date(year, month, 1)
            end = date(year, month, calendar.monthrange(year, month)[1])

            existing = HrLeave.search([
                ('employee_id', '=', emp.id),
                ('request_date_from', '<=', end),
                ('request_date_to', '>=', start),
                ('state', '!=', 'refuse'),
            ])

            blocked = set()
            for l in existing:
                d = l.request_date_from
                while d <= l.request_date_to:
                    blocked.add(d)
                    d += timedelta(days=1)

            processed = {}  # date -> {'am': bool, 'pm': bool}
            leaves_vals = []

            def _init(d):
                if d not in processed:
                    processed[d] = {'am': False, 'pm': False}

            # =================================================
            # CTC → ONLY LOP
            # =================================================
            if emp.ctc_type != 'non_ctc':
                for r in recs:
                    d = r.attendance_date
                    if d in blocked:
                        continue
                    _init(d)

                    # FULL DAY LOP FIRST
                    if (
                        r.morning_session == 'absent'
                        and r.afternoon_session == 'absent'
                        and not processed[d]['am']
                        and not processed[d]['pm']
                    ):
                        leaves_vals.append(self._full_vals(emp, lop_type, d))
                        processed[d]['am'] = processed[d]['pm'] = True
                        continue

                    # HALF DAY
                    if r.morning_session == 'absent' and not processed[d]['am']:
                        leaves_vals.append(self._half_vals(emp, lop_type, d, 'am'))
                        processed[d]['am'] = True

                    if r.afternoon_session == 'absent' and not processed[d]['pm']:
                        leaves_vals.append(self._half_vals(emp, lop_type, d, 'pm'))
                        processed[d]['pm'] = True

            # =================================================
            # NON-CTC → EL SLABS → EL → LOP
            # =================================================
            else:
                if emp.id not in alloc_cache:
                    alloc = Allocation.search([
                        ('employee_id', '=', emp.id),
                        ('state', '=', 'validate'),
                        ('allocation_type', '=', 'accrual'),
                        ('holiday_status_id.work_entry_type_id.code', '=', 'LEAVE120'),
                    ], limit=1)
                    alloc_cache[emp.id] = alloc.accrual_plan_id.level_ids[:1].added_value if alloc else 0

                monthly_el = alloc_cache[emp.id]

                # ---- SLABS ----
                rec_map = {r.attendance_date.day: r for r in recs}
                slabs = [(1, 10), (11, 20), (21, end.day)]
                earned_el = 0

                for s, e in slabs:
                    for day in range(s, e + 1):
                        rec = rec_map.get(day)
                        if rec and not (rec.morning_session == 'absent' and rec.afternoon_session == 'absent'):
                            earned_el += 1
                            break

                remaining_el = min(earned_el, monthly_el)

                # ---- APPLY EL ----
                for r in recs:
                    d = r.attendance_date
                    if d in blocked or remaining_el <= 0:
                        continue
                    _init(d)

                    if (
                        r.morning_session == 'absent'
                        and r.afternoon_session == 'absent'
                        and remaining_el >= 1
                        and not processed[d]['am']
                        and not processed[d]['pm']
                    ):
                        leaves_vals.append(self._full_vals(emp, el_type, d))
                        processed[d]['am'] = processed[d]['pm'] = True
                        remaining_el -= 1
                        continue

                    if r.morning_session == 'absent' and remaining_el >= 0.5 and not processed[d]['am']:
                        leaves_vals.append(self._half_vals(emp, el_type, d, 'am'))
                        processed[d]['am'] = True
                        remaining_el -= 0.5

                    if r.afternoon_session == 'absent' and remaining_el >= 0.5 and not processed[d]['pm']:
                        leaves_vals.append(self._half_vals(emp, el_type, d, 'pm'))
                        processed[d]['pm'] = True
                        remaining_el -= 0.5

                # ---- REMAINING → LOP ----
                for r in recs:
                    d = r.attendance_date
                    if d in blocked:
                        continue
                    _init(d)

                    if (
                        r.morning_session == 'absent'
                        and r.afternoon_session == 'absent'
                        and not processed[d]['am']
                        and not processed[d]['pm']
                    ):
                        leaves_vals.append(self._full_vals(emp, lop_type, d))
                        processed[d]['am'] = processed[d]['pm'] = True
                        continue

                    if r.morning_session == 'absent' and not processed[d]['am']:
                        leaves_vals.append(self._half_vals(emp, lop_type, d, 'am'))
                        processed[d]['am'] = True

                    if r.afternoon_session == 'absent' and not processed[d]['pm']:
                        leaves_vals.append(self._half_vals(emp, lop_type, d, 'pm'))
                        processed[d]['pm'] = True

            # ---- GROUP FULL-DAY CONTINUOUS ONLY ----
            if leaves_vals:
                leaves_vals = self._group_continuous_leaves(leaves_vals)
                HrLeave.create(leaves_vals)

    # =====================================================
    # GROUP CONTINUOUS FULL-DAY LEAVES
    # =====================================================
    def _group_continuous_leaves(self, vals_list):

        result = []
        vals_list = sorted(
            vals_list,
            key=lambda x: (x['employee_id'], x['holiday_status_id'], x['request_date_from'])
        )

        for v in vals_list:
            if v.get('request_unit_half'):
                result.append(v)
                continue

            if not result:
                result.append(v)
                continue

            last = result[-1]
            if (
                not last.get('request_unit_half')
                and last['employee_id'] == v['employee_id']
                and last['holiday_status_id'] == v['holiday_status_id']
                and last['request_date_to'] + timedelta(days=1) == v['request_date_from']
            ):
                last['request_date_to'] = v['request_date_to']
            else:
                result.append(v)

        return result

    # =====================================================
    # HELPERS
    # =====================================================
    def _full_vals(self, emp, leave_type, d):
        return {
            'employee_id': emp.id,
            'holiday_status_id': leave_type.id,
            'request_date_from': d,
            'request_date_to': d,
            'name': 'Auto from attendance import',
        }

    def _half_vals(self, emp, leave_type, d, period):
        return {
            'employee_id': emp.id,
            'holiday_status_id': leave_type.id,
            'request_date_from': d,
            'request_date_to': d,
            'request_unit_half': True,
            'request_date_from_period': period,
            'name': 'Auto from attendance import',
        }

    def _combine(self, d, t):
        if not d or not t:
            return False
        if isinstance(t, datetime):
            t = t.time()
        local_dt = datetime.combine(d, time(t.hour, t.minute))
        tz = pytz.timezone(self.env.user.tz or 'UTC')
        return tz.localize(local_dt).astimezone(pytz.UTC).replace(tzinfo=None)

    def _time_to_hhmm(self, v):
        if isinstance(v, (datetime, time)):
            return f"{v.hour:02d}:{v.minute:02d}"
        return ''

    def _validate_date(self, d, row_no):
        if isinstance(d, datetime):
            d = d.date()
        if not d:
            raise ValidationError(_("Row %s: Date missing") % row_no)
        if d > fields.Date.context_today(self):
            raise ValidationError(_("Row %s: Future date not allowed") % row_no)
        return d
# ##################################################################################################