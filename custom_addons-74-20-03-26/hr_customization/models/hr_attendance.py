from odoo import models, fields


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    schedule_check_in = fields.Datetime(
        string="Schedule Check In"
    )

    schedule_check_out = fields.Datetime(
        string="Schedule Check Out"
    )
