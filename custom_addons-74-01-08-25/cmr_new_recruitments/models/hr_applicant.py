import base64

from odoo import models,fields,api,_
from odoo.exceptions import UserError, AccessError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    applicant_professional_ids = fields.One2many(
        'professional.details',
        'applicant_id',
        string="Professional Details"
    )
    total_experience = fields.Float(string="Total Years of Experience")
    name = fields.Char(string="name")
    partner_mobile = fields.Char(string="Mobile")
    # ctc_type = fields.Selection([('with_bonus','With Bonus'),('With_out_bonus','Without Bonus')])
    applicant_reference_ids = fields.One2many('employee.reference', 'applicant_employee_id', string="References")
    applicant_education_ids = fields.One2many('employee.education', 'applicant_employee_id', string="Educational Details")
    shortlisted = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Shortlisted')
    check_list_ids = fields.Many2many("check.list")
    checklist_tab_visible = fields.Boolean(string="Checklist Tab Visible", default=False)

    checklist_order_line_ids = fields.One2many('hr.applicant.checklist.orderline', 'check_list_id', string="Checklist Documents")
    stage_remark_ids = fields.One2many('hr.applicant.stage.remark', 'applicant_id', string='Stage Remarks')
    document_type = fields.Selection([
        ('job', 'Job'),
        ('appointment', 'Appointment'),
        ('checklist', 'Checklist'),
        ('accepted', 'Offer Accepted'),
        ('default','Default')
    ], string='Document Type', default='job')
    is_stage_initial = fields.Boolean(
        string="Is Initial Stage",
        compute="_compute_is_stage_initial",
        store=False
    )
    is_stage_signed = fields.Boolean(
        string="Is Initial Signed",
        compute="_compute_is_stage_signed",
        store=False
    )
    on_hold = fields.Boolean(string='On Hold', default=False)
    offer_tag = fields.Selection([
        ('accepted', 'Offer Accepted'),
        ('rejected', 'Offer Rejected'),
    ], string="Offer Status", tracking=True)
    division_id = fields.Many2one(
        'product.category',
        string='Division',
        domain=[('parent_id', '=', False)],
        help="Select division from top-level product categories (no parent)."
    )
    approval_stage = fields.Selection([
        ('draft', 'Draft'),
        ('first_requested', 'Approval Requested'),
        ('first_approved', 'First Approved'),
        ('second_approved', 'Second Approved'),
        ('job_accepted', 'Job Accepted'),  # job offer sent
        ('job_rejected', 'Job Rejected'),
        ('first_approved_offer', 'First Approved'),  # job offer accepted
        ('second_approved_offer', 'Second Approved'),  # approval request
        ('third_approved_offer', 'Third Approved'),  # approved level1
        ('appointment', 'Appointment'),  # approved level2
        ('appointment_accepted', 'Appointment Accepted'),  # sent appointment letter
        ('appointment_rejected', 'Appointment Rejected'),
        ('checklist', 'Checklist'),  # appointment letter accepted
        ('done', 'Done'),  # checklist done
    ], default='draft')

    ctc_type = fields.Selection([
        ('with_bonus', 'With Bonus'),
        ('without_bonus', 'Without Bonus'),
        ('non_ctc', 'Non Ctc'),
    ], string='CTC Type')

    job_offer_sent = fields.Boolean(string="Job Offer Email Sent")
    ctc = fields.Float(string="CTC (Per Annum)")
    basic = fields.Float(string="BASIC (Per Annum)", compute="_compute_basic", store=True)
    hra = fields.Float(string="HRA (Per Annum)", compute="_compute_hra", store=True)
    other_allowance = fields.Float(string="OTHER ALLOWANCE (Per Annum)", compute="_compute_other_allowance", store=True)
    pf = fields.Float(string="PF (Per Annum)", store=True)
    pt = fields.Float(string="PT (Per Annum)", store=True)
    net_take_home = fields.Float(string="NET TAKE HOME (Per Annum)", compute="_compute_net_take_home", store=True)
    family_insurance = fields.Float(string="FAMILY INSURANCE (Per Annum)")
    bonus = fields.Float(string="BONUS (Per Annum)", compute="_compute_bonus", store=True)
    date_today = fields.Date(
        string='Date',
        default=fields.Date.context_today,
    )

    # Monthly Fields
    ctc_m = fields.Float(string="CTC (Per Month)", compute="_compute_monthly_fields", store=True)
    basic_m = fields.Float(string="BASIC (Per Month)", compute="_compute_monthly_fields", store=True)
    hra_m = fields.Float(string="HRA (Per Month)", compute="_compute_monthly_fields", store=True)
    other_allowance_m = fields.Float(string="OTHER ALLOWANCE (Per Month)", compute="_compute_monthly_fields",
                                     store=True)
    pf_m = fields.Float(string="PF (Per Month)", compute="_compute_monthly_fields", store=True)
    pt_m = fields.Float(string="PT (Per Month)", compute="_compute_monthly_fields", store=True)
    net_take_home_m = fields.Float(string="NET TAKE HOME (Per Month)", compute="_compute_monthly_fields", store=True)
    applicant_name = fields.Char(string='Applicant Name')
    todays_date = fields.Date(string="Date", default=fields.Date.today)
    date_of_joining = fields.Date(string='Date Of Joining', default=fields.Date.today)
    ctc_offer = fields.Float(string='CTC')
    designation = fields.Char(string="Designation")

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

    # Computed Methods for Monthly Values
    @api.depends('ctc', 'ctc_type')
    def _compute_monthly_fields(self):
        for rec in self:
            months = 13 if rec.ctc_type == 'with_bonus' else 12
            if rec.ctc:
                rec.ctc_m = rec.ctc / months
                rec.basic_m = rec.basic / months
                rec.hra_m = rec.hra / months
                rec.other_allowance_m = rec.other_allowance / months
                # rec.pf_m = rec.pf / months
                # rec.pt_m = rec.pt / months
                rec.net_take_home_m = rec.net_take_home / months
            else:
                rec.ctc_m = 0.0
                rec.basic_m = 0.0
                rec.hra_m = 0.0
                rec.other_allowance_m = 0.0
                # rec.pf_m = 0.0
                # rec.pt_m = 0.0
                rec.net_take_home_m = 0.0

    # ========== ONCHANGE METHODS ==========

    @api.onchange('ctc', 'ctc_type')
    def _onchange_ctc(self):
        for rec in self:
            months = 13 if rec.ctc_type == 'with_bonus' else 12
            if rec.ctc:
                rec.ctc_m = rec.ctc / months

    @api.onchange('ctc', 'partner_name', 'availability', 'job_id')
    def _onchange_offer(self):

        self.ctc_offer = self.ctc
        self.applicant_name = self.partner_name
        self.date_of_joining = self.availability
        self.designation = self.job_id.name

    @api.onchange('ctc_m', 'ctc_type')
    def _onchange_ctc_m(self):
        for rec in self:
            months = 13 if rec.ctc_type == 'with_bonus' else 12
            if rec.ctc_m:
                rec.ctc = rec.ctc_m * months

    @api.onchange('ctc')
    def _onchange_basic(self):
        for rec in self:
            rec.basic = rec.ctc * 0.60 if rec.ctc else 0.0

    @api.onchange('ctc_m')
    def _onchange_basic_m(self):
        for rec in self:
            rec.basic_m = rec.ctc_m * 0.60 if rec.ctc_m else 0.0

    @api.onchange('ctc')
    def _onchange_hra(self):
        for rec in self:
            rec.hra = rec.ctc * 0.30 if rec.ctc else 0.0

    @api.onchange('ctc_m')
    def _onchange_hra_m(self):
        for rec in self:
            rec.hra_m = rec.ctc_m * 0.30 if rec.ctc_m else 0.0

    @api.onchange('ctc')
    def _onchange_other_allowance(self):
        for rec in self:
            rec.other_allowance = rec.ctc * 0.10 if rec.ctc else 0.0

    @api.onchange('ctc_m')
    def _onchange_other_allowance_m(self):
        for rec in self:
            rec.other_allowance_m = rec.ctc_m * 0.10 if rec.ctc_m else 0.0

    @api.onchange('ctc', 'pf', 'pt', 'basic', 'hra', 'other_allowance')
    def _onchange_net_take_home(self):
        for rec in self:
            if rec.ctc:
                # For Annual Net Take Home: basic + hra + other_allowance - pf - pt
                rec.net_take_home = (rec.basic or 0.0) + (rec.hra or 0.0) + (rec.other_allowance or 0.0) - (
                        rec.pf or 0.0) - (rec.pt or 0.0)
            else:
                rec.net_take_home = 0.0

    @api.onchange('ctc_m', 'pf_m', 'pt_m', 'basic_m', 'hra_m', 'other_allowance_m')
    def _onchange_net_take_home_m(self):
        for rec in self:
            if rec.ctc_m:
                # For Monthly Net Take Home: basic_m + hra_m + other_allowance_m - pf_m - pt_m
                rec.net_take_home_m = (rec.basic_m or 0.0) + (rec.hra_m or 0.0) + (rec.other_allowance_m or 0.0) - (
                        rec.pf_m or 0.0) - (rec.pt_m or 0.0)
            else:
                rec.net_take_home_m = 0.0

    # ========== PF and PT OnChange ==========

    @api.onchange('pf')
    def _onchange_pf(self):
        for rec in self:
            months = 12
            if rec.pf:
                rec.pf_m = rec.pf / months

    @api.onchange('pf_m')
    def _onchange_pf_m(self):
        for rec in self:
            months = 12
            if rec.pf_m:
                rec.pf = rec.pf_m * months

    @api.onchange('pt')
    def _onchange_pt(self):
        for rec in self:
            months = 12
            if rec.pt:
                rec.pt_m = rec.pt / months

    @api.onchange('pt_m')
    def _onchange_pt_m(self):
        for rec in self:
            months = 12
            if rec.pt_m:
                rec.pt = rec.pt_m * months


    def action_request_approval(self):
        self.ensure_one()
        # ✅ Move to stage: "Job Offer Approval Sent"
        job_offer_stage = self.env['hr.recruitment.stage'].search([
            ('name', '=', 'Job Offer Approval Sent')
        ], limit=1)
        if not job_offer_stage:
            raise AccessError("Stage 'Job Offer Approval Sent' not found.")

        self.stage_id = job_offer_stage.id

        self.approval_stage = 'first_requested'
        first_group = self.env.ref('cmr_new_recruitments.group_hr_applicant_first_approval', raise_if_not_found=False)
        if not first_group:
            raise AccessError("Group for first-level approval not found.")

        for user in first_group.users:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user.id,
                summary='Approval Level 1 Needed',
                note='Please review and approve (Level 1).'
            )

    def action_first_approve(self):
        self.ensure_one()
        self.approval_stage = 'first_approved'

        # ✅ Properly find and mark only current user's activity as done
        activity = self.env['mail.activity'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('user_id', '=', self.env.user.id),
            ('summary', '=', 'Approval Level 1 Needed'),
        ], limit=1)
        if activity:
            activity.action_feedback(_('✅ Level 1 Approved by %s') % self.env.user.name)


        second_group = self.env.ref('cmr_new_recruitments.group_hr_applicant_second_approval', raise_if_not_found=False)
        if second_group:
            for user in second_group.users:
                self.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=user.id,
                    summary='Approval Level 2 Needed',
                    note='Please review and approve (Level 2).'
                )

    def action_second_approve(self):
        self.ensure_one()

        # ✅ Move to stage: "Job Offer Approval Sent"
        job_offer_stage = self.env['hr.recruitment.stage'].search([
            ('name', '=', 'Job Offer Approved')
        ], limit=1)
        if not job_offer_stage:
            raise AccessError("Stage 'Job Offer Approved' not found.")

        self.stage_id = job_offer_stage.id

        self.approval_stage = 'second_approved'
        activity = self.env['mail.activity'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('user_id', '=', self.env.user.id),
            ('summary', '=', 'Approval Level 2 Needed'),
        ], limit=1)
        if activity:
            activity.action_feedback(_('✅ Level 2 Approved by %s') % self.env.user.name)

    def action_refuse_approval_one(self):
        self.ensure_one()

        # ✅ Move to 'Refused' stage
        refused_stage = self.env['hr.recruitment.stage'].search([
            ('name', '=', 'Contract Proposal')
        ], limit=1)
        if not refused_stage:
            raise AccessError("Stage 'Contract Proposal' not found. Please configure the stage.")

        self.stage_id = refused_stage.id
        self.approval_stage = 'draft'

        # ✅ Mark all pending activities as done
        activities = self.env['mail.activity'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('user_id', '=', self.env.user.id),

        ])
        if activities:
            activities.action_feedback(_("❌ Approval Refused by %s") % self.env.user.name)

    def action_refuse_approval_two(self):
        self.ensure_one()

        # ✅ Move to 'Refused' stage
        refused_stage = self.env['hr.recruitment.stage'].search([
            ('name', '=', 'Contract Proposal')
        ], limit=1)
        if not refused_stage:
            raise AccessError("Stage 'Contract Proposal' not found. Please configure the stage.")

        self.stage_id = refused_stage.id
        self.approval_stage = 'draft'

        # ✅ Mark all pending activities as done
        activities = self.env['mail.activity'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('user_id', '=', self.env.user.id),

        ])
        if activities:
            activities.action_feedback(_("❌ Approval Refused by %s") % self.env.user.name)

    def action_appointment_request_approval(self):
        self.ensure_one()
        self.approval_stage="second_approved_offer"
        # ✅ Move to stage: "Job Offer Approval Sent"
        job_offer_stage = self.env['hr.recruitment.stage'].search([
            ('name', '=', 'Appointment Approval Sent')
        ], limit=1)
        if not job_offer_stage:
            raise AccessError("Stage 'Appointment Approval Sent' not found.")

        self.stage_id = job_offer_stage.id


        first_group = self.env.ref('cmr_new_recruitments.group_hr_applicant_first_approval', raise_if_not_found=False)
        if not first_group:
            raise AccessError("Group for first-level approval not found.")

        for user in first_group.users:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user.id,
                summary='Approval Level 1 Needed',
                note='Please review and approve (Level 1).'
            )

    def action_appointment_first_approve(self):
        self.ensure_one()
        self.approval_stage="third_approved_offer"


        # ✅ Properly find and mark only current user's activity as done
        activity = self.env['mail.activity'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('user_id', '=', self.env.user.id),
            ('summary', '=', 'Approval Level 1 Needed'),
        ], limit=1)
        if activity:
            activity.action_feedback(_('✅ Level 1 Approved by %s') % self.env.user.name)

        second_group = self.env.ref('cmr_new_recruitments.group_hr_applicant_second_approval', raise_if_not_found=False)
        if second_group:
            for user in second_group.users:
                self.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=user.id,
                    summary='Approval Level 2 Needed',
                    note='Please review and approve (Level 2).'
                )

    def action_appointment_second_approve(self):
        self.ensure_one()
        self.approval_stage = 'appointment'

        # ✅ Move to stage: "Job Offer Approval Sent"
        job_offer_stage = self.env['hr.recruitment.stage'].search([
            ('name', '=', 'Appointment Offer Approved')
        ], limit=1)
        if not job_offer_stage:
            raise AccessError("Stage 'Appointment Offer Approved' not found.")

        self.stage_id = job_offer_stage.id


        activity = self.env['mail.activity'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('user_id', '=', self.env.user.id),
            ('summary', '=', 'Approval Level 2 Needed'),
        ], limit=1)
        if activity:
            activity.action_feedback(_('✅ Level 2 Approved by %s') % self.env.user.name)

    def action_appointment_refuse_approval_one(self):
        self.ensure_one()

        # ✅ Move to 'Refused' stage
        refused_stage = self.env['hr.recruitment.stage'].search([
            ('name', '=', 'Job Offer Approved')
        ], limit=1)
        if not refused_stage:
            raise AccessError("Stage 'Job Offer Approved' not found. Please configure the stage.")

        self.stage_id = refused_stage.id
        self.approval_stage = 'first_approved_offer'

        # ✅ Mark all pending activities as done
        activities = self.env['mail.activity'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('user_id', '=', self.env.user.id),

        ])
        if activities:
            activities.action_feedback(_("❌ Approval Refused by %s") % self.env.user.name)

    def action_appointment_refuse_approval_two(self):
        self.ensure_one()

        # ✅ Move to 'Refused' stage
        refused_stage = self.env['hr.recruitment.stage'].search([
            ('name', '=', 'Job Offer Approved')
        ], limit=1)
        if not refused_stage:
            raise AccessError("Stage 'Job Offer Approved' not found. Please configure the stage.")

        self.stage_id = refused_stage.id
        self.approval_stage = 'first_approved_offer'

        # ✅ Mark all pending activities as done
        activities = self.env['mail.activity'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('user_id', '=', self.env.user.id),

        ])
        if activities:
            activities.action_feedback(_("❌ Approval Refused by %s") % self.env.user.name)


    def action_add_stage_remarks(self):
        """Create missing stage remark lines for this applicant."""
        for applicant in self:
            existing_stage_ids = applicant.stage_remark_ids.mapped('stage_id.id')
            all_stages = self.env['hr.recruitment.stage'].search([], order='sequence')
            for stage in all_stages:
                if stage.id not in existing_stage_ids:
                    self.env['hr.applicant.stage.remark'].create({
                        'applicant_id': applicant.id,
                        'stage_id': stage.id,
                    })


    # def action_offer_accepted(self):
    #     for rec in self:
    #         rec.document_type = 'default'
    #         rec.offer_tag = 'accepted'

    # def action_offer_rejected(self):
    #     for rec in self:
    #         rec.document_type = 'default'
    #         rec.offer_tag = 'rejected'

    def action_quotation_send_accepted(self):
        for rec in self:
            # rec.document_type = 'appointment'
            rec.approval_stage = 'first_approved_offer'


    def action_quotation_send_rejected(self):
        for rec in self:
            # rec.document_type = 'job_rejected'
            rec.approval_stage = 'job_rejected'
            # rec.offer_tag = 'rejected'


    def action_appointment_letter_accepted(self):
        for rec in self:
            # rec.document_type = 'accepted'
            rec.approval_stage = 'checklist'


    def action_appointment_letter_rejected(self):
        for rec in self:
            # rec.document_type = 'appointment_rejected'
            rec.approval_stage = 'appointment_rejected'
            # rec.offer_tag = 'rejected'


    def action_set_on_hold(self):
        for rec in self:
            rec.on_hold = True

    def action_unhold(self):
        for rec in self:
            rec.on_hold = False

    @api.depends('stage_id')
    def _compute_is_stage_second_interview(self):
        for rec in self:
            rec.is_stage_second_interview = rec.stage_id.name == 'Second Interview'

    @api.depends('stage_id')
    def _compute_is_stage_initial(self):
        for rec in self:
            rec.is_stage_initial = rec.stage_id.name == 'Contract Proposal'

    @api.depends('stage_id')
    def _compute_is_stage_signed(self):
        for rec in self:
            rec.is_stage_signed = rec.stage_id.name == 'Contract Signed'

    def action_quotation_send(self):
        self.ensure_one()

        try:
            # Generate the offer letter PDF
            report_name = 'cmr_new_recruitments.nhcl_offer_letter_action'
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
                'cmr_new_recruitments.email_template_applicant_job_offer',
                raise_if_not_found=False
            )
            lang = self.env.context.get('lang')
            template = self.env['mail.template'].browse(template_id)
            if template and template.lang:
                lang = template._render_lang(self.ids)[self.id]

            # Build context for compose wizard
            ctx = {
                'default_model': 'hr.applicant',
                'default_res_ids': self.ids,
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'mark_so_as_sent': True,
                'custom_layout': "mail.mail_notification_paynow",
                'proforma': self.env.context.get('proforma', False),
                'force_email': True,
                'model_description': self.with_context(lang=lang),
                'approval_type': 'job_accepted',
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

            # Step 1: Generate the PDF
            pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
                'cmr_new_recruitments.report_appointment_letter', [self.id]
            )
            _logger.info("✅ PDF generated successfully for %s", self.name)

            # Step 2: Create an attachment
            attachment = self.env['ir.attachment'].create({
                'name': f'Appointment_Letter_{self.name}.pdf',
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'hr.applicant',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            _logger.info("📎 Attachment created: %s", attachment.name)

            # Step 3: Get email template
            template_id = self.env['ir.model.data']._xmlid_to_res_id(
                'cmr_new_recruitments.email_template_applicant_appointment_letter', raise_if_not_found=False)
            if not template_id:
                raise UserError(_("Appointment email template not found."))

            template = self.env['mail.template'].browse(template_id)
            lang = self.env.context.get('lang')
            if template.lang:
                lang = template._render_lang(self.ids)[self.id]

            # Step 4: Prepare context for mail wizard
            ctx = {
                'default_model': 'hr.applicant',
                'default_res_ids': self.ids,
                'default_use_template': True,
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'default_attachment_ids': [(4, attachment.id)],
                'mark_so_as_sent': True,
                'custom_layout': "mail.mail_notification_paynow",
                'force_email': True,
                'model_description': self.with_context(lang=lang),
                'approval_type': 'appointment_accepted',
            }

            _logger.info("✉️ Opening email wizard for manual sending.")
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
            _logger.exception("❌ Error while preparing appointment letter email.")
            raise UserError(_("Failed to process appointment letter: %s") % str(e))


    @api.model
    def _get_next_stage(self, current_stage):
        return self.env['hr.recruitment.stage'].search([
            ('sequence', '>', current_stage.sequence)
        ], order='sequence asc', limit=1)

    def write(self, vals):
        res = super().write(vals)

        # Handle shortlisted logic AFTER write
        if 'shortlisted' in vals and vals['shortlisted'] == 'yes':
            for applicant in self:
                next_stage = self._get_next_stage(applicant.stage_id)
                if next_stage:
                    applicant.stage_id = next_stage.id
                    applicant.shortlisted = False


        return res

    def create_employee_from_applicant(self):

        for applicant in self:
            # Validate at least one checklist item is selected
            if not applicant.check_list_ids:
                raise ValidationError("Please select at least one checklist document before creating an employee.")

            # 2. Validate company
            if not applicant.company_id:
                raise ValidationError("Please assign a Company before creating an employee.")

        # Call the original method to create the employee
        res = super(HrApplicant, self).create_employee_from_applicant()

        for applicant in self:
            applicant._onchange_applicant_lines()
            if applicant.employee_id:
                employee = applicant.employee_id
                applicant.employee_id._compute_grade()
                # 1. Copy Professional Details
                for line in applicant.applicant_professional_ids:
                    line.copy({
                        'employee_id': applicant.employee_id.id,
                        'applicant_id': False
                    })

                # 2. Copy Reference Details
                for ref in applicant.applicant_reference_ids:
                    ref.copy({
                        'employee_id': applicant.employee_id.id,
                        'applicant_employee_id': False
                    })

                # 3. Copy Education Details
                for edu in applicant.applicant_education_ids:
                    edu.copy({
                        'employee_id': applicant.employee_id.id,
                        'applicant_employee_id': False
                    })

                # 4. Copy Checklist (Many2many)
                applicant.employee_id.check_list_ids = [(6, 0, applicant.check_list_ids.ids)]

                # 5. Copy Total Experience
                applicant.employee_id.total_experience = applicant.total_experience

                applicant.employee_id.mobile_phone = applicant.partner_phone
                applicant.employee_id.work_phone = applicant.partner_mobile
                employee.company_id = applicant.company_id
                employee.private_email = applicant.email_from
                employee.private_street = applicant.permanent_street
                employee.private_street2 = applicant.permanent_street2
                employee.private_city = applicant.permanent_city
                employee.private_state_id = applicant.permanent_state_id
                employee.private_zip = applicant.permanent_zip
                employee.private_country_id = applicant.permanent_country_id
                employee.birthday = applicant.dob
                employee.gender = applicant.gender
                employee.marital = applicant.marital_status
                employee.age = applicant.age
                employee.division_id = applicant.division_id.id
                employee.ctc = applicant.ctc
                employee.basic = applicant.basic
                employee.hra = applicant.hra
                employee.other_allowance = applicant.other_allowance
                employee.pf = applicant.pf
                employee.pt = applicant.pt
                employee.bonus = applicant.bonus
                employee.net_take_home = applicant.net_take_home
                employee.family_insurance = applicant.family_insurance
                employee.ctc_m = applicant.ctc_m
                employee.basic_m = applicant.basic_m
                employee.hra_m = applicant.hra_m
                employee.other_allowance_m = applicant.other_allowance_m
                employee.pf_m = applicant.pf_m
                employee.pt_m = applicant.pt_m
                employee.net_take_home_m = applicant.net_take_home_m

                # 7. ✅ Auto-create contract
                self.env['hr.contract'].create({
                    'name': employee.name,
                    'employee_id': employee.id,
                    'department_id': employee.department_id.id,
                    'job_id': employee.job_id.id,
                    'date_start': fields.Date.today(),
                    'wage': applicant.ctc_m,
                    'basic': applicant.basic_m or 0.0,
                    'p_tax': applicant.pf_m or 0.0,
                    'cost_to_company': applicant.ctc or 0.0,
                    'net_salary': applicant.ctc_m or 0.0,
                    'provident_fund': applicant.pt_m or 0.0,
                    # 'l10n_in_house_rent_allowance_metro_nonmetro': applicant.hra_m or 0.0,
                })

        return res

    @api.onchange('applicant_education_ids', 'applicant_professional_ids')
    def _onchange_applicant_lines(self):
        """Auto-assign sequence numbers for both educational and professional lines."""
        for idx, line in enumerate(self.applicant_education_ids, start=1):
            line.sequence = idx
        for idx, line in enumerate(self.applicant_professional_ids, start=1):
            line.sequence = idx

    def action_open_checklist_tab(self):
        self.ensure_one()

        self.approval_stage = 'done'
        self.checklist_tab_visible = True

        # Safe way: shared stages
        next_stage = self.env['hr.recruitment.stage'].search([
            ('sequence', '>', self.stage_id.sequence)
        ], order='sequence asc', limit=1)

        if next_stage:
            self.stage_id = next_stage.id

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.applicant',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def action_send_mail(self):
        # ✅ Keep context key consistent (approval_type)
        self = self.with_context(approval_type=self.env.context.get('approval_type'))
        return super().action_send_mail()

    def _action_send_mail_comment(self, res_ids):
        # ✅ Call the original method
        messages = super()._action_send_mail_comment(res_ids)

        # ✅ Set approval_stage after mail is sent
        approval_type = self.env.context.get('approval_type')
        if self.model == 'hr.applicant' and res_ids and approval_type:
            applicants = self.env['hr.applicant'].browse(res_ids)
            applicants.write({'approval_stage': approval_type})

            # Optional: Flag to track job offer sent
            if approval_type == 'job_accepted':
                applicants.write({'job_offer_sent': True})

        return messages
#
class HrContract(models.Model):
    _inherit = 'hr.contract'

    net_salary = fields.Float(string='Net Salary')
    basic = fields.Float('Basic')
    p_tax = fields.Float('PT')
    cost_to_company = fields.Float(string='Cost to company')
    provident_fund= fields.Float('PF')
    # uan_no = fields.Char('UAN No.')
    # x_studio_overtime = fields.Float('Overtime')
    # x_studio_salary_arrears_june23 = fields.Float('Salary Arrears June23')
    # x_studio_scholarship_1 = fields.Float('Scholarship')
    # x_studio_covid_ded = fields.Float('Covid Ded')
    # x_studio_rent = fields.Float('Rent')






