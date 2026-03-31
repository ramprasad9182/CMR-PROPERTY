from odoo import models, fields ,api
from odoo.exceptions import UserError
from datetime import date
import calendar


class HrDutyRoster(models.Model):
    _name = 'hr.duty.roster'
    _description = 'Monthly Duty Roster'

    month = fields.Selection(
        [(str(i), calendar.month_name[i]) for i in range(1, 13)],
        required=True
    )
    year = fields.Integer(required=True)
    department_id = fields.Many2one('hr.department', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed')
    ], default='draft')

    line_ids = fields.One2many(
        'hr.duty.roster.line',
        'roster_id',
        string="Roster Lines"
    )

    valid_days = fields.Integer(
        string="Valid Days",
        compute="_compute_valid_days",
        store=True
    )

    @api.depends('month', 'year')
    def _compute_valid_days(self):
        for rec in self:
            if rec.month and rec.year:
                rec.valid_days = calendar.monthrange(rec.year, int(rec.month))[1]
            else:
                rec.valid_days = 31

    def action_generate_roster(self):
        for roster in self:
            roster.line_ids.unlink()

            employees = self.env['hr.employee'].search([
                ('department_id', '=', roster.department_id.id)
            ])

            calendars = self.env['resource.calendar'].search([])
            if not calendars:
                raise UserError("No shifts found in Resource Calendar")

            for emp in employees:
                vals = {
                    'roster_id': roster.id,
                    'employee_id': emp.id,
                }

                for day in range(1, 32):
                    try:
                        date(int(roster.year), int(roster.month), day)
                    except ValueError:
                        continue

                    if emp.job_id and emp.job_id.name and emp.job_id.name.upper() in ('HOD', 'TL'):
                        vals[f'd{day}'] = emp.resource_calendar_id.id
                    else:
                        vals[f'd{day}'] = calendars[(day - 1) % len(calendars)].id

                self.env['hr.duty.roster.line'].create(vals)

    def action_confirm(self):
        self.state = 'confirmed'


class HrDutyRosterLine(models.Model):
    _name = 'hr.duty.roster.line'
    _description = 'Duty Roster Line'

    roster_id = fields.Many2one('hr.duty.roster', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', required=True)
    designation = fields.Char(
        related='employee_id.job_id.name',
        store=True
    )

    d1 = fields.Many2one('resource.calendar', string="1")
    d2 = fields.Many2one('resource.calendar', string="2")
    d3 = fields.Many2one('resource.calendar', string="3")
    d4 = fields.Many2one('resource.calendar', string="4")
    d5 = fields.Many2one('resource.calendar', string="5")
    d6 = fields.Many2one('resource.calendar', string="6")
    d7 = fields.Many2one('resource.calendar', string="7")
    d8 = fields.Many2one('resource.calendar', string="8")
    d9 = fields.Many2one('resource.calendar', string="9")
    d10 = fields.Many2one('resource.calendar', string="10")
    d11 = fields.Many2one('resource.calendar', string="11")
    d12 = fields.Many2one('resource.calendar', string="12")
    d13 = fields.Many2one('resource.calendar', string="13")
    d14 = fields.Many2one('resource.calendar', string="14")
    d15 = fields.Many2one('resource.calendar', string="15")
    d16 = fields.Many2one('resource.calendar', string="16")
    d17 = fields.Many2one('resource.calendar', string="17")
    d18 = fields.Many2one('resource.calendar', string="18")
    d19 = fields.Many2one('resource.calendar', string="19")
    d20 = fields.Many2one('resource.calendar', string="20")
    d21 = fields.Many2one('resource.calendar', string="21")
    d22 = fields.Many2one('resource.calendar', string="22")
    d23 = fields.Many2one('resource.calendar', string="23")
    d24 = fields.Many2one('resource.calendar', string="24")
    d25 = fields.Many2one('resource.calendar', string="25")
    d26 = fields.Many2one('resource.calendar', string="26")
    d27 = fields.Many2one('resource.calendar', string="27")
    d28 = fields.Many2one('resource.calendar', string="28")
    d29 = fields.Many2one('resource.calendar', string="29")
    d30 = fields.Many2one('resource.calendar', string="30")
    d31 = fields.Many2one('resource.calendar', string="31")
