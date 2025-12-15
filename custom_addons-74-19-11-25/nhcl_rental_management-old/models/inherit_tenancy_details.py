from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import fields, api, models
from odoo.exceptions import ValidationError


class TenancyDetails(models.Model):
    _inherit = 'tenancy.details'
    _description = 'Information Related To customer Tenancy while Creating Contract'

    # adding fields
    tenancy_type = fields.Char(string='Tenancy Type', compute='_depends_company_id', copy=False)
    # this is for sft and fixed rate
    sft_fixed = fields.Selection([('sft', 'SFT'), ('Fixed', 'Fixed'),], string='Type', copy=False)
    supporting_ids = fields.One2many('support.documents', 'support_id', copy=False)
    unit_no = fields.Float(string='Unit No', copy=False)
    brand_name = fields.Char(string='Brand Name', copy=False)

    # this is for SFT
    carpet_area = fields.Float(string='Carpet Area', copy=False)
    percentage = fields.Float(string='Loading Percentage', default='25.0', copy=False)
    chargeable_area = fields.Float(string='Chargeable Area', compute='_calculate_chargeable_area', copy=False)
    rate = fields.Float(string='Rate Per sft', copy=False)

    # this is for Fixed
    lum_sum = fields.Char(string='Lum sum', copy=False)
    rate2 = fields.Float(string='Rate', copy=False)
    year_ids = fields.One2many('year_add', 'yid', string='yearids', copy=False)
    is_brand_name_readonly = fields.Integer( default=0,
        compute='_compute_is_brand_name_readonly',
        store=True,
    )    #
    caution_deposite = fields.Float(string='Caution Deposite', copy=False)
    caution_invoice_created = fields.Boolean(
        string="Caution Invoice Created",
        default=False,
        help="Indicates whether the invoice for caution deposit has been created."
    , copy=False)
    # add renewal type
    renewal_type = fields.Selection([('quat', 'Quarterly'), ('half', 'Half Yearly'), ('year', 'Yearly')],
                                    string='Renewal Type', copy=False)
    quaterly = fields.Integer(string='Quarterly Days', default=90, copy=False)
    halfday = fields.Integer(string='Half Yearly Days', default=180, copy=False)
    ndays = fields.Integer(string="Years", default=2, copy=False)
    renewal_date = fields.Date(string='Renewal Date', compute='_compute_renewal_date', store=True, copy=False)

    # this is for cam and rent rate
    cam_rate=fields.Float(string='CAM Rate Per sft')
    # rent_rate=fields.Float(string='RENT Rate')
    cam_total = fields.Float(string='Total Cam', compute='_compute_total_amount')
    total_cam_in_words=fields.Char(string='Cam Total Words',compute='_total_amount_words_for_cam')
    # hiding the rend
    hide_rent=fields.Boolean(string='Hide',default=False)

    # it's for the cam_total value
    @api.depends('chargeable_area', 'cam_rate')
    def _compute_total_amount(self):
        for record in self:
            record.cam_total = record.chargeable_area * record.cam_rate

    def _total_amount_words_for_cam(self):
        for rec in self:
            self.total_cam_in_words=self.convert_to_indian_words(rec.cam_total)

    # it's for the total words for the cam
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

        def num_to_words(n):
            # Convert a number to words (Indian format)
            if n < 10:
                return units[n]
            elif n < 20:
                return teens[n - 10]
            elif n < 100:
                return tens[n // 10] + (" " + units[n % 10] if n % 10 != 0 else "")
            else:
                result = ""
                place = 0
                while n > 0:
                    rem = n % 100
                    if rem > 0:
                        if place > 0:
                            result = num_to_words(rem) + " " + thousands[place] + " " + result
                        else:
                            result = num_to_words(rem) + " " + result
                    n //= 100
                    place += 1
                return result.strip()

        integer_part_in_words = num_to_words(integer_part)
        decimal_part_in_words = f"{decimal_part:02d}/100" if decimal_part else ""
        return f"{integer_part_in_words} Rupees {decimal_part_in_words} Only"

    # for calculating value form yearly or quaterly
    @api.depends('renewal_type', 'quaterly', 'halfday', 'ndays')
    def _compute_renewal_date(self):
        for record in self:
            # today = datetime.today()
            today = self.start_date
            renewal_date = None
            if record.renewal_type == 'quat':
                renewal_date = today + timedelta(days=record.quaterly) - timedelta(days=20)
            elif record.renewal_type == 'half':
                renewal_date = today + timedelta(days=record.halfday) - timedelta(days=30)
            elif record.renewal_type == 'year':
                renewal_date = today + timedelta(days=record.ndays * 365) - timedelta(days=60)
            record.renewal_date = renewal_date if renewal_date else None

    # adding the value of year based on the type of renewal type
    @api.onchange('renewal_type', 'ndays','end_year')
    def change_the_value_add(self):
        if self.renewal_type and self.start_date and self.duration_id and self.ndays:
            # Clear existing year_ids
            self.year_ids = [(5, 0, 0)]
            base_date = self.start_date  # Start from the given start_date
            new_records = []

            # Determine the number of periods and increment logic based on renewal_type
            if self.renewal_type == 'year':
                increment = relativedelta(years=self.ndays)
                num_periods = (self.duration_id.month // 12) // self.ndays
            elif self.renewal_type == 'quat':
                increment = relativedelta(months=3)
                num_periods = self.duration_id.month // 3
            elif self.renewal_type == 'half':
                increment = relativedelta(months=6)
                num_periods = self.duration_id.month // 6
            else:
                return  # Unsupported renewal_type, exit

            # Ensure num_periods is a valid positive integer
            if int(num_periods) <= 0:
                return
            # Generate records for year_ids
            for i in range(int(num_periods)):
                start_year = base_date
                end_year = start_year + increment
                new_records.append((0, 0, {
                    'start_year': start_year,
                    'end_year': end_year,
                }))
                base_date = end_year  # Update base_date for the next period

            self.year_ids = new_records
    # def change_the_value_add(self):
    #     if self.renewal_type == 'year':
    #         if not self.start_date or not self.duration_id or not self.ndays:
    #             return  # Ensure start_date and duration are available
    #         years = self.ndays  # here i am getting the year
    #         self.year_ids = [(5, 0, 0)]
    #         # Calculate the number of periods based on the duration
    #         num_periods = (self.duration_id.month // 12) // years  # Assuming 'duration' holds the number of years
    #         if int(num_periods) <= 0:
    #             return  # Prevent invalid periods
    #         base_date = self.start_date  # Start from the given start_date
    #         new_records = []
    #
    #         for i in range(int(num_periods)):
    #             if i == 0:
    #                 start_year = base_date
    #                 end_year = start_year + relativedelta(years=self.ndays)  # Calculate the end of the year
    #                 new_records.append((0, 0, {
    #                     'start_year': start_year,
    #                     'end_year': end_year,
    #                 }))
    #             else:
    #                 start_year = start_year + relativedelta(years=1 * self.ndays)
    #                 end_year = start_year + relativedelta(years=self.ndays)
    #                 new_records.append((0, 0, {
    #                     'start_year': start_year,
    #                     'end_year': end_year,
    #                 }))
    #         self.year_ids = new_records

    def send_email_based_on_year(self):
        template = self.env.ref('nhcl_rental_management.escalation_notification_email_template')
        for record in self.env['tenancy.details'].search([('renewal_type', '=', 'year')]):
            for line in record.year_ids:
                if line.end_year:
                    if fields.Date.today() == line.end_year - timedelta(days=-61):
                        template.send_mail(record.id, force_send=True)

    # renewal date send email and chanel for this
    @api.model
    def send_email_to_tenancy(self):
        template = self.env.ref('nhcl_rental_management.renewal_notification_email_template')
        emails_sent = 0

        channel = self.env['discuss.channel'].search([('name', '=', 'Tenancy Chat')])

        # Create the channel if it does not exist
        if not channel:
            user_ids = self.env['res.users'].search([]).ids
            channel = self.env['discuss.channel'].create({
                'name': 'Tenancy Chat',
                'channel_type': 'group',
                'channel_partner_ids': [(4, user.partner_id.id) for user in self.env['res.users'].browse(user_ids)],
            })
        for record in self.env['tenancy.details'].search([]):
            if fields.Date.today() == record.renewal_date:
                template.send_mail(record.id, force_send=True)
                emails_sent += 1
                message_body = f"Renewal reminder email sent to tenant: {record.tenancy_id.name} for renewal date: {record.renewal_date}."
                # Post a message in the channel
                channel.message_post(
                    body=message_body,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )

#this is for the tenancy finance team draft post message
    def notif_finance_tm(self):
        """Notify the finance team via Discuss channel when a tenancy is in draft mode."""

        # Search for the 'Finance Team' Discuss channel
        channel = self.env['discuss.channel'].search([('name', '=', 'Finance Team')], limit=1)

        # Create the channel if it does not exist
        if not channel:
            user_ids = self.env['res.users'].search([]).ids
            channel = self.env['discuss.channel'].create({
                'name': 'Finance Team',
                'channel_type': 'group',
                'channel_partner_ids': [(4, user.partner_id.id) for user in self.env['res.users'].browse(user_ids)],
            })

        # Post a message to the channel
        channel.message_post(
            body=f"Finance Team, please review {self.tenancy_id.name}. It is currently in draft mode.",
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

    def action_active_contract(self):
        for record in self:
            if record.caution_deposite > 0 and not record.caution_invoice_created:
                record.caution_invoice_created = True
                # self.write(vals)
                self.talend_invoice()
                self.cam_product_invoice()
        self.notif_finance_tm()
        res = super(TenancyDetails, self).action_active_contract()
        return res

    # caution deposit for this method
    def talend_invoice(self):
        """Create an invoice based on the caution_deposite value."""
        invoice_date = fields.Date.today()
        for record in self:
            rec = self.env['product.product'].search([('name', '=', 'Caution Deposit')])
            if rec:
                invoice_vals = {
                    'partner_id': record.tenancy_id.id,
                    'move_type': 'out_invoice',
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': [(0, 0, {
                        'product_id': rec.id,
                        'name': 'Caution Deposit',
                        'quantity': 1,
                        'price_unit': record.caution_deposite,
                        'nhcl_area_units': self.chargeable_area,

                    })],
                }
                invoice_id = self.env['account.move'].sudo().create(invoice_vals)
                invoice_id.tenancy_id = self.id
                invoice_id.action_post()
                rent_invoice = {
                    'tenancy_id': record.id,
                    'type': 'deposit',
                    'invoice_date': invoice_date,
                    'description': 'Installment of ' + record.property_id.name,
                    'rent_invoice_id': invoice_id.id,
                    # 'amount': invoice_id.amount_total,
                    'amount': record.caution_deposite,
                    'rent_amount': self.total_rent
                }
                self.env['rent.invoice'].create(rent_invoice)
            else:
                product = {
                    'name': 'Caution Deposit',
                    'type': 'service',
                }
                f = self.env['product.product'].create(product)
                invoice_vals = {
                    'partner_id': record.tenancy_id.id,
                    'move_type': 'out_invoice',
                    'invoice_date': invoice_date,
                    'invoice_line_ids': [(0, 0, {
                        'product_id': f.id,
                        'name': 'Caution Deposit',
                        'quantity': 1,
                        'price_unit': record.caution_deposite,

                    })],
                }
                invoice_id = self.env['account.move'].sudo().create(invoice_vals)
                invoice_id.tenancy_id = self.id
                invoice_id.action_post()
                rent_invoice = {
                    'tenancy_id': record.id,
                    'type': 'deposit',
                    'invoice_date': invoice_date,
                    'description': 'Installment of ' + record.property_id.name,
                    'rent_invoice_id': invoice_id.id,
                    # 'amount': invoice_id.amount_total,
                    'amount': record.caution_deposite,
                    'rent_amount': self.total_rent
                }
                self.env['rent.invoice'].create(rent_invoice)
    # this is for the cam product details
    def cam_product_invoice(self):
        """Create an invoice for cam."""
        invoice_date = fields.Date.today()
        for record in self:
            rec = self.env['product.product'].search([('name', '=', 'Cam Maintenance')])
            if rec:
                invoice_vals = {
                    'partner_id': record.tenancy_id.id,
                    'move_type': 'out_invoice',
                    'invoice_date': fields.Date.today(),
                    'nhcl_invoice_type': 'cam',
                    'invoice_line_ids': [(0, 0, {
                        'product_id': rec.id,
                        'name': 'Cam ',
                        'quantity': 1,
                        'price_unit': ((record.chargeable_area)*(record.cam_rate)),
                        'nhcl_area_units': self.chargeable_area

                    })],
                }
                invoice_id = self.env['account.move'].sudo().create(invoice_vals)
                invoice_id.tenancy_id = self.id
                #invoice_id.action_post()
                rent_invoice = {
                    'tenancy_id': record.id,
                    'type': 'maintenance',
                    'invoice_date': invoice_date,
                    'description': 'Cam for' + record.property_id.name,
                    'rent_invoice_id': invoice_id.id,
                    # 'amount': invoice_id.amount_total,
                    'amount': (record.chargeable_area)*(record.cam_rate),
                    'rent_amount': self.total_rent
                }
                self.env['rent.invoice'].create(rent_invoice)
            else:
                product = {
                    'name': 'Cam Maintenance',
                    'type': 'service',
                }
                f = self.env['product.product'].create(product)
                invoice_vals = {
                    'partner_id': record.tenancy_id.id,
                    'move_type': 'out_invoice',
                    'invoice_date': invoice_date,
                    'nhcl_invoice_type': 'cam',
                    'invoice_line_ids': [(0, 0, {
                        'product_id': f.id,
                        'name': 'Cam',
                        'quantity': 1,
                        'price_unit': (record.chargeable_area)*(record.cam_rate),
                        'nhcl_area_units': self.chargeable_area

                    })],
                }
                invoice_id = self.env['account.move'].sudo().create(invoice_vals)
                invoice_id.tenancy_id = self.id
                #invoice_id.action_post()
                rent_invoice = {
                    'tenancy_id': record.id,
                    'type': 'maintenance',
                    'invoice_date': invoice_date,
                    'description': 'Cam for' + record.property_id.name,
                    'rent_invoice_id': invoice_id.id,
                    # 'amount': invoice_id.amount_total,
                    'amount': (record.chargeable_area)*(record.cam_rate),
                    'rent_amount': self.total_rent
                }
                self.env['rent.invoice'].create(rent_invoice)

    @api.depends('carpet_area', 'percentage')
    def _calculate_chargeable_area(self):
        for record in self:
            if record.carpet_area and record.percentage:
                record.chargeable_area = ((record.percentage / 100.0) * record.carpet_area) + record.carpet_area
            else:
                record.chargeable_area = 0.0

    @api.depends('tenancy_id')
    def _depends_company_id(self):
        for record in self:
            record.tenancy_type = record.tenancy_id.tenant_type.name

    @api.constrains('contract_type')
    def _compute_is_brand_name_readonly(self):
        for record in self:
            if record.contract_type == 'running_contract':
                record.is_brand_name_readonly = 1

    # this is for if yhe valu is less than zero then dont take cautiondeposit
    @api.constrains('caution_deposite')
    def _check_caution_deposite(self):
        for record in self:
            if record.caution_deposite < 0:
                raise ValidationError("Caution Deposit value cannot be less than zero.")

    @api.onchange('rate','sft_fixed','percentage','lum_sum')
    def _check_total(self):
        for rec in self:
            if self.sft_fixed != 'Fixed':
               rec.total_rent=rec.chargeable_area*rec.rate
            else:
                rec.total_rent=rec.lum_sum

    @api.depends('renewal_type')
    def _check_renewal_type(self):
        for record in self:
             if record.renewal_type == 'year' and  fields.Date.today() == self.start_date + relativedelta(years=2):
                 self.hide_rent=True

    # @api.onchange
    # def Change_amount_rent_approve(self):
    #     if self.contract_type == 'running_contract':
    #         record=self.env['tenancy.detrails']




