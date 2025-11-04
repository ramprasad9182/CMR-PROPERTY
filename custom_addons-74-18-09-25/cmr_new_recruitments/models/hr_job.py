from odoo import models, fields, api

class HrJob(models.Model):
    _inherit = 'hr.job'

    hired_count = fields.Integer(string="Hired", compute="_compute_hired_count")
    vacant_count = fields.Integer(string="Vacant", compute="_compute_vacant_count")
    application_count = fields.Integer(string="Applications", compute="_compute_application_count")
    # vacancy = fields.Integer(string="Vacant", compute = "_compute_vacant")



    @api.depends('no_of_recruitment', 'hired_count')
    def _compute_vacant_count(self):
        for record in self:
            record.vacant_count = record.no_of_recruitment - record.hired_count


    def _compute_hired_count(self):
        Applicant = self.env['hr.applicant']
        for record in self:
            record.hired_count = Applicant.search_count([
                ('job_id', '=', record.id),
                ('stage_id.name', '=', 'Contract Signed'),
            ])

    def _compute_application_count(self):
        Applicant = self.env['hr.applicant']
        for record in self:
            record.application_count = Applicant.search_count([
                ('job_id', '=', record.id)
            ])