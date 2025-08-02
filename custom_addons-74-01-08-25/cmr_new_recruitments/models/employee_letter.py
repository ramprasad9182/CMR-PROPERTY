import base64

from odoo import models, fields, api, _
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EmployeeLetter(models.Model):
    _name = 'employee.letter'
    _description = 'Employee Letter'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Reference", compute="_compute_name", store=True)

    @api.depends('employee_id', 'todays_date')
    def _compute_name(self):
        for rec in self:
            if rec.employee_id and rec.todays_date:
                rec.name = f"{rec.employee_id.name} - {rec.todays_date.strftime('%Y-%m-%d')}"
            elif rec.employee_id:
                rec.name = rec.employee_id.name
            else:
                rec.name = "Offer Letter"

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)


    todays_date = fields.Date(string="Date", default=fields.Date.today)
    date_of_joining = fields.Date(string='Date Of Joining')
    ctc_offer = fields.Float(string='CTC', compute="_compute_ctc_offer", store=True)
    designation_id = fields.Many2one('hr.job', string="Designation")

    ctc_type = fields.Selection([
        ('with_bonus', 'With Bonus'),
        ('without_bonus', 'Without Bonus'),
        ('non_ctc', 'Non Ctc'),
    ], string='CTC Type', required='True')

    # Annual Fields
    ctc = fields.Float(string="CTC (Per Annum)")
    basic = fields.Float(string="BASIC (Per Annum)", compute="_compute_basic", store=True)
    hra = fields.Float(string="HRA (Per Annum)", compute="_compute_hra", store=True)
    other_allowance = fields.Float(string="OTHER ALLOWANCE (Per Annum)", compute="_compute_other_allowance", store=True)
    pf = fields.Float(string="PF (Per Annum)", store=True)
    pt = fields.Float(string="PT (Per Annum)", store=True)
    net_take_home = fields.Float(string="NET TAKE HOME (Per Annum)", compute="_compute_net_take_home", store=True)
    family_insurance = fields.Float(string="FAMILY INSURANCE (Per Annum)")
    bonus = fields.Float(string="BONUS (Per Annum)", compute="_compute_bonus", store=True)

    # Monthly Fields
    ctc_m = fields.Float(string="CTC (Per Month)", compute="_compute_monthly_fields", store=True)
    basic_m = fields.Float(string="BASIC (Per Month)", compute="_compute_monthly_fields", store=True)
    hra_m = fields.Float(string="HRA (Per Month)", compute="_compute_monthly_fields", store=True)
    other_allowance_m = fields.Float(string="OTHER ALLOWANCE (Per Month)", compute="_compute_monthly_fields",
                                     store=True)
    pf_m = fields.Float(string="PF (Per Month)", compute="_compute_monthly_fields", store=True)
    pt_m = fields.Float(string="PT (Per Month)", compute="_compute_monthly_fields", store=True)
    net_take_home_m = fields.Float(string="NET TAKE HOME (Per Month)", compute="_compute_monthly_fields", store=True)

    @api.depends('ctc')
    def _compute_ctc_offer(self):
        for record in self:
            record.ctc_offer = record.ctc

    def action_quotation_send(self):
        self.ensure_one()

        try:
            # Generate the offer letter PDF
            report_name = 'cmr_new_recruitments.nhcl_offer_letter_action_direct'
            pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
                report_name,
                [self.id]
            )
            _logger.info("Offer letter PDF generated successfully.")

            # Create an attachment
            attachment = self.env['ir.attachment'].create({
                'name': f'Offer_Letter_{self.name}.pdf',
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'hr.applicant',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            _logger.info("Attachment created: %s", attachment.name)

            # Retrieve the email template
            template_id = self.env['ir.model.data']._xmlid_to_res_id(
                'cmr_new_recruitments.email_template_applicant_job_offer_direct',
                raise_if_not_found=False
            )
            lang = self.env.context.get('lang')
            template = self.env['mail.template'].browse(template_id)
            if template and template.lang:
                lang = template._render_lang(self.ids)[self.id]

            # Build context for compose wizard
            ctx = {
                'default_model': 'employee.letter',
                'default_res_ids': self.ids,
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'mark_so_as_sent': True,
                'custom_layout': "mail.mail_notification_paynow",
                'proforma': self.env.context.get('proforma', False),
                'force_email': True,
                'model_description': self.with_context(lang=lang),
                # 'approval_type': 'job_accepted',
                'default_attachment_ids': [(6, 0, [attachment.id])],
            }

            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                'context': ctx,
            }

        except Exception as e:
            _logger.exception("Failed to prepare quotation email.")
            raise UserError(_("Failed to prepare offer letter email: %s") % str(e))

    def action_appointment_letter_send(self):
        self.ensure_one()
        try:
            _logger.info("🔹 Starting appointment letter generation for: %s", self.name)

            # Step 1: Generate PDF from QWeb report
            pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
                'cmr_new_recruitments.report_appointment_letter_direct', [self.id]
            )
            _logger.info("✅ PDF generated successfully for %s", self.name)

            # Step 2: Create the attachment
            attachment = self.env['ir.attachment'].create({
                'name': f'Appointment_Letter_{self.name}.pdf',
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'employee.letter',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            _logger.info("📎 Attachment created: %s", attachment.name)

            # Step 3: Get the email template ID
            template_id = self.env['ir.model.data']._xmlid_to_res_id(
                'cmr_new_recruitments.email_template_applicant_appointment_letter_direct', raise_if_not_found=False)
            if not template_id:
                raise UserError(_("Appointment email template not found."))

            template = self.env['mail.template'].browse(template_id)

            # Step 4: Determine language
            lang = self.env.context.get('lang')
            if template.lang:
                lang = template._render_lang(self.ids)[self.id]

            # Step 5: Open the email wizard with context
            ctx = {
                'default_model': 'employee.letter',
                'default_res_ids': self.ids,
                'default_use_template': True,
                'default_template_id': template.id,
                'default_composition_mode': 'comment',
                'default_attachment_ids': [(4, attachment.id)],
                'mark_so_as_sent': True,
                'custom_layout': "mail.mail_notification_paynow",
                'force_email': True,
            }

            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'target': 'new',
                'context': ctx,
            }

        except Exception as e:
            _logger.error("❌ Failed to send appointment letter: %s", str(e))
            raise UserError(_("An error occurred while sending the appointment letter:\n%s") % str(e))

    # Compute methods
    @api.depends('ctc')
    def _compute_basic(self):
        for rec in self:
            rec.basic = rec.ctc * 0.60 if rec.ctc else 0.0

    @api.depends('ctc')
    def _compute_hra(self):
        for rec in self:
            rec.hra = rec.ctc * 0.30 if rec.ctc else 0.0

    @api.depends('ctc')
    def _compute_other_allowance(self):
        for rec in self:
            rec.other_allowance = rec.ctc * 0.10 if rec.ctc else 0.0

    @api.depends('ctc', 'pf', 'pt', 'hra', 'other_allowance', 'basic')
    def _compute_net_take_home(self):
        for rec in self:
            rec.net_take_home = rec.basic + rec.hra + rec.other_allowance - rec.pf - rec.pt if rec.ctc else 0.0

    @api.depends('ctc')
    def _compute_bonus(self):
        for rec in self:
            rec.bonus = rec.ctc_m if rec.ctc_m else 0.0

    @api.depends('ctc', 'ctc_type')
    def _compute_monthly_fields(self):
        for rec in self:
            months = 13 if rec.ctc_type == 'with_bonus' else 12
            if rec.ctc:
                rec.ctc_m = rec.ctc / months
                rec.basic_m = rec.basic / months
                rec.hra_m = rec.hra / months
                rec.other_allowance_m = rec.other_allowance / months
                rec.pf_m = rec.pf / months if rec.pf else 0.0
                rec.pt_m = rec.pt / months if rec.pt else 0.0
                rec.net_take_home_m = rec.net_take_home / months
            else:
                rec.ctc_m = rec.basic_m = rec.hra_m = rec.other_allowance_m = rec.pf_m = rec.pt_m = rec.net_take_home_m = 0.0

    # Onchange
    @api.onchange('ctc', 'ctc_type')
    def _onchange_ctc(self):
        for rec in self:
            months = 13 if rec.ctc_type == 'with_bonus' else 12
            rec.ctc_m = rec.ctc / months if rec.ctc else 0.0

    # @api.onchange('ctc', 'availability', 'job_id')
    # def _onchange_offer(self):
    #     self.ctc_offer = self.ctc
    #     self.applicant_name = self.partner_name
    #     self.date_of_joining = self.availability
    #     self.designation_id = self.job_id

    @api.onchange('ctc_m', 'ctc_type')
    def _onchange_ctc_m(self):
        for rec in self:
            months = 13 if rec.ctc_type == 'with_bonus' else 12
            rec.ctc = rec.ctc_m * months if rec.ctc_m else 0.0

    @api.onchange('pf')
    def _onchange_pf(self):
        for rec in self:
            rec.pf_m = rec.pf / 12 if rec.pf else 0.0

    @api.onchange('pf_m')
    def _onchange_pf_m(self):
        for rec in self:
            rec.pf = rec.pf_m * 12 if rec.pf_m else 0.0

    @api.onchange('pt')
    def _onchange_pt(self):
        for rec in self:
            rec.pt_m = rec.pt / 12 if rec.pt else 0.0

    @api.onchange('pt_m')
    def _onchange_pt_m(self):
        for rec in self:
            rec.pt = rec.pt_m * 12 if rec.pt_m else 0.0



    def action_print_offer_letter(self):
        self.ensure_one()
        report = self.env.ref('cmr_new_recruitments.nhcl_offer_letter_action_direct')

        # Dynamically set filename via context — by overriding 'report_file' in self.env.context
        self = self.with_context(report_file=f'Odoo-{self.employee_id.name.replace(" ", "_")}')

        return report.report_action(self)

    def action_print_appointment_letter(self):
        self.ensure_one()
        report = self.env.ref('cmr_new_recruitments.report_appointment_letter_direct')

        self = self.with_context(report_file=f'Odoo-{self.employee_id.name.replace(" ", "_")}')

        return report.report_action(self)
