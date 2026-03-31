from odoo import models, fields, api

class AttendanceExcel(models.Model):
    _name = 'hr.upload'
    _description = 'Attendance Upload'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        required=True
    )

    emp_code = fields.Char(
        string="Employee Code",
        related='employee_id.barcode',
        store=True,
        readonly=True
    )


    department_id = fields.Many2one(
        'hr.department',
        string="Department",
        related='employee_id.department_id',
        store=True,
        readonly=True
    )
    attendance_date = fields.Date(
        string="Date",
        required=True
    )

    check_in = fields.Datetime(string="Check In")
    check_out = fields.Datetime(string="Check Out")

    total_time = fields.Char(string="Total Time")

    status = fields.Selection([
        ('present', 'Present'),
        ('od', 'OD'),
        ('absent', 'Absent'),
        ('half_lp_pr', '1/2LP+1/2PR'),
        ('half_pr_lp', '1/2PR+1/2LP'),
        ('half_pm_lp', '1/2PM+1/2LP'),
        ('half_lp_pm', '1/2LP+1/2PM'),
        ('pm', 'PM'),
        ('wo', 'W/O'),
    ], string="Status")

    morning_session = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
    ], string="Morning Session", compute="_compute_sessions", store=True)

    afternoon_session = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
    ], string="Afternoon Session", compute="_compute_sessions", store=True)

    ns_amount = fields.Float(string="Amount")

    @api.depends('status')
    def _compute_sessions(self):
        for rec in self:

            # Default
            morning = 'present'
            afternoon = 'present'

            if rec.status == 'absent':
                morning = afternoon = 'absent'

            elif rec.status in ('half_lp_pr', 'half_lp_pm'):
                morning = 'absent'
                afternoon = 'present'

            elif rec.status in ('half_pr_lp', 'half_pm_lp'):
                morning = 'present'
                afternoon = 'absent'

            # present / od / wo / pm → both present
            rec.morning_session = morning
            rec.afternoon_session = afternoon
