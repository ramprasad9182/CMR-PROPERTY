import typing
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError
from odoo import fields, api, models
import base64


class AccountMove(models.Model):
    _inherit = 'account.move'

    # state = fields.Selection(selection_add=[
    #     ('approve', 'Approve') ,('posted') # Adding a new option
    # ])
    state = fields.Selection(
        [('draft', 'Draft'), ('approve', 'Approve'), ('posted', 'Posted'), ('cancel', 'Cancelled')], default='draft')
    # state = fields.Selection(selection_add=[ ('approve', 'Approve'), ('posted',)])
    needs_approval = fields.Boolean(string="Needs Approval", default=False)
    nhcl_invoice_type = fields.Selection(
        [('rent', 'Rent'), ('cam', 'Cam'), ('regular', 'Regular'), ('advanced', 'Advance'), ('marketing', 'Marketing'),
         ('electric', 'Electric'), ('gas', 'Gas')], string="Invoice Type", copy=False, default='rent')
    invoice_month_range = fields.Char(string="Invoice Month Range", compute="_compute_invoice_month_range",
                                      store=True, )
    cam_fields = fields.Boolean(string="Check", compute='get_fields')
    amount_in_words = fields.Char(string='Amount in Words', compute='_compute_amount_in_words', store=True)
    for_ammount = fields.Integer(string='Amount change', compute='_get_amount', default=1)
    check_post = fields.Integer(string='Check post', default=0)

    # this is for the amount convert to words
    def convert_to_indian_words(self, amount):
        # Ensure amount is a float
        amount = float(amount)
        integer_part = int(amount)  # Get the integer part
        decimal_part = round((amount - integer_part) * 100)  # Get the decimal part as paise (always two digits)

        # Define components for conversion
        units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen",
                 "Nineteen"]
        thousands = ["", "Thousand", "Lakh", "Crore"]

        def convert_chunk(num):
            """Convert a three-digit chunk into words."""
            if num == 0:
                return ""
            elif num < 10:
                return units[num]
            elif num < 20:
                return teens[num - 10]
            elif num < 100:
                return tens[num // 10] + (" " + units[num % 10] if num % 10 != 0 else "")
            else:
                return units[num // 100] + " Hundred" + (" " + convert_chunk(num % 100) if num % 100 != 0 else "")

        # Convert the integer part
        words = []
        chunk_idx = 0

        while integer_part > 0:
            chunk = integer_part % 1000
            if chunk > 0:
                chunk_in_words = convert_chunk(chunk) + " " + thousands[chunk_idx]
                words.insert(0, chunk_in_words.strip())
            integer_part //= 1000
            chunk_idx += 1

        # Handle the case where the amount is exactly zero
        if not words:
            words.append("Zero")

        rupee_words = " ".join(words).strip() + " Rupees"

        # Add the decimal part (paise) if it exists
        if decimal_part > 0:
            paise_words = convert_chunk(decimal_part) + " Paise"
            return f"{rupee_words} and {paise_words}"

        return rupee_words

    @api.depends('amount_total')
    def _compute_amount_in_words(self):
        for record in self:
            # Retrieve the total amount from the invoice (absolute value in case of negative amounts)
            amount_total = abs(record.amount_total)
            # Use the custom method to convert the amount to words
            record.amount_in_words = self.convert_to_indian_words(amount_total)

    @api.onchange('nhcl_invoice_type')
    def get_fields(self):
        invoice = self.env.context.get('default_move_type') == 'out_invoice'
        credit_note = self.env.context.get('default_move_type') == 'out_refund' and self.env.context.get(
            'display_account_trust', False)
        for rec in self:
            if (invoice and rec.nhcl_invoice_type == 'cam') or (credit_note and rec.nhcl_invoice_type == 'cam'):
                rec.cam_fields = True
            else:
                rec.cam_fields = False

    # this is for the invoice date for report
    @api.depends('invoice_date')
    def _compute_invoice_month_range(self):
        for record in self:
            if record.invoice_date:
                # Parse the invoice_date into a date object
                invoice_date2 = fields.Date.from_string(record.invoice_date)
                # Get the first day of the month from the invoice date
                first_day = invoice_date2.replace(day=1)
                # Format both the first day of the month and the invoice date
                formatted_range = f"{first_day.strftime('%d/%b/%Y')} to {invoice_date2.strftime('%d/%b/%Y')}"
                record.invoice_month_range = formatted_range
            else:
                record.invoice_month_range = "No Invoice Date"

    # this is for the tenancy 2 days before alert message
    @api.model
    def send_message_invoice(self):
        # Get the email template
        template = self.env.ref('nhcl_rental_management.maintenance_invoice_message')
        channel = self.env['discuss.channel'].search([('name', '=', 'Invoice Alert')])
        # Create the channel if it does not exist
        if not channel:
            user_ids = self.env['res.users'].search([]).ids
            channel = self.env['discuss.channel'].create({
                'name': 'Invoice Alert',
                'channel_type': 'group',
                'channel_partner_ids': [(4, user.partner_id.id) for user in self.env['res.users'].browse(user_ids)],
            })
        for record in self.env['account.move'].search(
                [('move_type', '=', 'out_invoice'), ('invoice_date', '!=', False), ('state', '=', 'draft')]):
            notification_date = record.invoice_date + timedelta(days=-2)
            if fields.Date.today() == notification_date:
                template.send_mail(record.id, force_send=True)
                channel.message_post(
                    body=f"email sent to tenant: {record.partner_id.name} for aleart",
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )

    # it's for the invoice mail based on the post
    # def send_invoice_email_post(self):
    #     template = self.env.ref('nhcl_rental_management.invoice_message_post')
    #     account_post = self.env['account.move'].search(
    #         [('state', '=', 'posted'), ('move_type', '=', 'out_invoice'), ('invoice_date', '!=', False)])
    #
    #     for post in account_post:
    #         if post.invoice_date == fields.Date.today():
    #             # Get the report object for the report template
    #             report = self.env.ref('nhcl_rental_management.tenancy_account_invoice_customise12')
    #             # Use the report's `render_qweb_pdf` method to generate the PDF content
    #             pdf_content, pdf_filename = report._render_qweb_pdf(post.id)
    #             print('successful calling')
    #             # Create the attachment for the generated PDF
    #             attachment = self.env['ir.attachment'].create({
    #                 'name': pdf_filename,
    #                 'type': 'binary',
    #                 'datas': pdf_content.encode('base64'),
    #                 'mimetype': 'application/pdf',
    #                 'res_model': 'account.move',
    #                 'res_id': post.id,
    #             })
    #             # Send the email with the attachment
    #             template.send_mail(post.id, force_send=True, email_values={
    #                 'attachment_ids': [(4, attachment.id)]  # Attach the generated report to the email
    #             })

    def send_invoice_email_post(self):
        # Reference the email template you want to use
        template = self.env.ref('nhcl_rental_management.invoice_message_post')

        # Search for all posted invoices (out_invoice type) with a valid invoice date
        account_post = self.env['account.move'].search(
            [('state', '=', 'posted'), ('move_type', '=', 'out_invoice'), ('invoice_date', '!=', False)]
        )

        for post in account_post:
            if post.invoice_date == fields.Date.today():
            	template = self.env.ref('nhcl_rental_management.invoice_message_post')
               
                
            	account_post = self.env['account.move'].search([('state', '=', 'posted'), ('move_type', '=','out_invoice'), ('invoice_date', '!=', False)])
            	for post in account_post:
            		if post.invoice_date == fields.Date.today():
                		#print("working successfully")
                		template.send_mail(post.id, force_send=True)

                # Render the PDF for the invoice
                # pdf_content, pdf_filename = report._render_qweb_pdf(post.id)
                #
                # # Create the attachment for the generated PDF
                # attachment = self.env['ir.attachment'].create({
                #     'name': pdf_filename,
                #     'type': 'binary',
                #     'datas': base64.b64encode(pdf_content),  # Correctly base64 encode the binary content
                #     'mimetype': 'application/pdf',
                #     'res_model': 'account.move',
                #     'res_id': post.id,
                # })

                # Send the email with the attachment
                # email_values = {
                #     'attachment_ids': [(4, attachment.id)]  # Attach the generated report to the email
                # }
                #
                # # Send the email using the template
                # template.send_mail(post.id, force_send=True, email_values=email_values)
                #
                #

    # it's for the getting record of the areunit in the invoice screen from same customer previous record
    def getrecord_areaunit(self):
        # Search for all moves where tenancy_id is set
        rec = self.env['account.move'].search([('tenancy_id', '!=', False)])
        for data in rec:
            if data.partner_id.id == self.partner_id.id:
                for line in data.line_ids:
                    if line.nhcl_area_units:
                        for myline in self.line_ids:
                            update_record = myline.write({'nhcl_area_units': line.nhcl_area_units})
                return " "

    def action_post(self):
        res = super(AccountMove, self).action_post()
        template = self.env.ref('nhcl_rental_management.invoice_message_post')
        template.send_mail(self.id, force_send=True)
        if self.nhcl_invoice_type == 'cam':
            self.getrecord_areaunit()
        if self.invoice_date or self.payment_reference:
            return res


    def write(self, vals):
        # Prevent recursive write calls by not updating the fields if already set
        if 'name' not in vals and 'payment_reference' not in vals:
            # Call the parent method to perform the write operation
            res = super(AccountMove, self).write(vals)
            # Generate the invoice number based on the invoice type
            type_inv = self.nhcl_invoice_type
            invoice_number = self._generate_invoice_number(type_inv)

            self.name = invoice_number
            self.payment_reference = invoice_number
            return res
        return super(AccountMove, self).write(vals)


    def _generate_invoice_number(self, invoice_type):
        year = fields.Date.today().year  # Current year
        sequence_code = None
        if invoice_type == 'rent':
            sequence_code = 'invoice.rent.sequence'
        elif invoice_type == 'cam':
            sequence_code = 'invoice.cam.sequence'
        elif invoice_type == 'electric':
            sequence_code = 'electric.invoice.sequence'
        elif invoice_type == 'gas':
            sequence_code = 'gas.invoice.sequence'
        elif invoice_type == 'marketing':
            sequence_code = 'marketing.invoice.sequence'
        elif invoice_type == 'advanced':
            sequence_code = 'advanced.invoice.sequence'
        elif invoice_type == 'regular':
            sequence_code = 'account.invoice.sequence'
            # print(sequence_code)
        sequence = self.env['ir.sequence'].next_by_code(sequence_code) or '00001'
        # print(sequence)
        return f"{sequence}"




class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    opening_reading = fields.Integer(string='Opening Reading')
    closing_reading = fields.Integer(string='Closing Reading')
    consumption = fields.Integer(string='Consumption')
    consumed_units = fields.Integer(string='Consumed Units')
    nhcl_area_units = fields.Char(string='Area Units')

    # @api.model
    # def write(self, vals):
    #     res = super(AccountMoveLine, self).write(vals)
    #
    #     # Check if the parent move is in draft and if needs_approval flag is not set
    #     for line in self:
    #         if line.move_id.state == 'draft' and not line.move_id.needs_approval:
    #             line.move_id.needs_approval = True
    #
    #     return res
