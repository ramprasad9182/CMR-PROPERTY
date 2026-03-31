from odoo import models, fields

class HrOvertimeMaster(models.Model):
    _name = 'hr.overtime.master'
    _description = 'Overtime Master'
    _order = 'start_time'

    name = fields.Char(string="Description", required=True)

    shift_id = fields.Many2one(
        'resource.calendar',
        string="Shift",
        required=True,
        domain="['|', ('company_id', '=', False), ('company_id', 'in', allowed_company_ids)]"
    )

    start_time = fields.Char(
        string="Start Time",
        required=True,
        help="Time in hours (10.5 = 10:30)"
    )

    end_time = fields.Char(
        string="End Time",
        required=True,
        help="Time in hours (11.0 = 11:00)"
    )

    amount = fields.Float(
        string="Overtime Amount",
        required=True
    )