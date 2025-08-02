from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta
from num2words import num2words

from odoo import fields, api, models
from odoo.exceptions import ValidationError
import calendar


class TenancyDetails(models.Model):
    _inherit = 'tenancy.details'
    _description = 'Information Related To customer Tenancy while Creating Contract'

    # adding fields
    tenancy_type = fields.Char(string='Tenancy Type', compute='_depends_company_id', copy=False)
    # this is for sft and fixed rate
    sft_fixed = fields.Selection([('sft', 'SFT'), ('Fixed', 'Fixed'), ], string='Type', copy=False)
    supporting_ids = fields.One2many('support.documents', 'support_id', copy=False)
    unit_no = fields.Char(string='Unit No', copy=False)
    brand_name = fields.Char(string='Brand Name', copy=False)

    # this is for SFT
    carpet_area = fields.Float(string='Carpet Area', copy=False)
    percentage = fields.Float(string='Loading Percentage', default='25.0', copy=False)
    chargeable_area = fields.Float(string='Chargeable Area', compute='_calculate_chargeable_area', copy=False)
    rate = fields.Float(string='Rate Per sft', copy=False)

    # this is for Fixed
    lum_sum = fields.Char(string='Lum sum', copy=False)
    rate2 = fields.Float(string='Rate', copy=False)
    year_ids = fields.One2many('year.add', 'yid', string='yearids', copy=False)
    cam_year_ids = fields.One2many('cam.year', 'cam_yid', string='cam_yearids', copy=False)
    is_brand_name_readonly = fields.Integer(default=0,
                                            compute='_compute_is_brand_name_readonly',
                                            store=True,
                                            )  #
    caution_deposite = fields.Float(string='Sequrity Deposite(IFRD)', copy=False)
    caution_invoice_created = fields.Boolean(
        string="Caution Invoice Created",
        default=False,
        help="Indicates whether the invoice for caution deposit has been created."
        , copy=False)
    # add renewal type
    renewal_type = fields.Selection(
        [('monthly', 'Monthly'), ('quat', 'Quarterly'), ('half', 'Half Yearly'), ('year', 'Yearly')],
        string='Rent Renewal Type', copy=False)
    quaterly = fields.Integer(string='Quarterly Days', default=90, copy=False)
    halfday = fields.Integer(string='Half Yearly Days', default=180, copy=False)
    ndays = fields.Integer(string="Years", default=2, copy=False)
    month_date = fields.Integer(string="Month", default=1, copy=False)
    renewal_date = fields.Date(string='Renewal Date', compute='_compute_renewal_date', store=True, copy=False)

    # this is for cam and rent rate
    cam_rate = fields.Float(string='CAM Rate Per sft')
    # rent_rate=fields.Float(string='RENT Rate')
    cam_total = fields.Float(string='Cam Amount', compute='_compute_total_amount')
    cau_depo_date = fields.Date(string='Caution Deposit Date')

    total_cam_in_words = fields.Char(string='Cam Total Words', compute='_total_amount_words_for_cam')
    # hiding the rend
    hide_rent = fields.Boolean(string='Hide', default=False)
    # FOR THE notification
    notif_60_sent = fields.Boolean(default=False)
    notif_45_sent = fields.Boolean(default=False)
    notif_30_sent = fields.Boolean(default=False)
    notif_15_sent = fields.Boolean(default=False)

    # for the cam tye related fields
    cam_type = fields.Selection([('cam_sft', 'Cam SFT'), ('cam_lumsum', 'Lum Sum'), ], string='CAM Type', copy=False)
    cam_carpet = fields.Float(string='Cam Carpet', compute='cam_carpet_value')
    cam_chargeable = fields.Float(string='Cam Chargeable', compute='cam_charge_value')
    cam_fixed = fields.Float(string='Cam Fixed')

    cam_carpet_area = fields.Float(string='Cam Carpet Area', copy=False)
    cam_percentage = fields.Float(string='Cam Loading %', default='25.0', copy=False)
    cam_chargeable_area = fields.Float(string='Cam Chargeable Area', compute='_calculate_chargeable_area_cam',copy=False)

    # Checkboxes
    use_carpet = fields.Boolean(string='■')
    use_chargeable = fields.Boolean(string='■')

    # for the trade all fieds are here
    trade_category = fields.Char(string="Trade Category")
    trade_sub_category_1 = fields.Char(string="Trade Sub Category 1")
    trade_sub_category_2 = fields.Char(string="Trade Sub Category 2")
    trade_name = fields.Char(string="Trade Name")
    trade_no = fields.Char(string="Trade No")
    valid_till = fields.Date(string="Valid Till")  # Stored as char, but format should be date-like (e.g., '2025-12-31')

    lease_to_owner = fields.Char(string="Lease To: Owner Company")
    lease_to_franchise = fields.Char(string="Lease To: Franchise Company")
    lease_to_triparty = fields.Char(string="Lease To: Tri-Party Agreement")

    possession_notice_date = fields.Date(string="Possession Notice Date")
    possession_days = fields.Char(string="No. of Days of Possession")
    possession_date = fields.Date(string="Possession Date")

    fitout_period_days = fields.Integer(string="Fit-Out Period In Days")
    fitout_completion_date = fields.Date(string="Fit-Out Completion Date")
    fitout_exclusive = fields.Date(string="Fit-Out Exclusive of Possession Date")

    move_out = fields.Char(string="Move Out")

    # for the security related fields
    signing_agreement = fields.Float(string='Signing Agreement', digits=(8, 4))
    signing_agreement_date = fields.Date(string='Signing Agreement Date')

    store_occupied = fields.Float(string='Store Occupied', digits=(8, 4))
    store_occupied_date = fields.Date(string='Store Occupied Date')

    store_opened = fields.Float(string='Store Opened', digits=(8, 4))
    store_opened_date = fields.Date(string='Store Opened Date')

    time_of_execution = fields.Float(string='Time of Execution', digits=(8, 4))
    time_of_execution_date = fields.Date(string='Time of Execution Date')

    time_of_possession = fields.Float(string='Time of Possession', digits=(8, 4))
    time_of_possession_date = fields.Date(string='Time of Possession Date')

    # it's for the creating the invoice who are coming in the middle of the month
    is_partial_month = fields.Boolean(
        string="Is Partial Month",
        compute='_compute_is_partial_month',
        store=True
    )
    invoice_type = fields.Selection([
        ('rs', 'RS'),
        # ('mg', 'MG'),
        # ('rs_or_mg', 'RS or MG'),
        ('slb', 'Slab Wise'),
    ], string='Invoice Type', required=False)
    carpet_value_take = fields.Boolean(
        string="Carpet Amount Rent",
    )
    cam_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('halfyearly', 'Half-Yearly'),
        ('yearly', 'Yearly'),
    ], string="CAM Type Renewal")
    cam_quaterly = fields.Integer(string='Quarterly Days', default=90, copy=False)
    cam_halfday = fields.Integer(string='Half Yearly Days', default=180, copy=False)
    cam_ndays = fields.Integer(string="Years", default=2, copy=False)
    cam_month_date = fields.Integer(string="Month", default=1, copy=False)

    @api.depends('start_date')
    def _compute_is_partial_month(self):
        for record in self:
            if record.start_date:
                record.is_partial_month = record.start_date.day != 1
            else:
                record.is_partial_month = False

    # it's for the cam_total value
    @api.depends('chargeable_area', 'cam_rate')
    def _compute_total_amount(self):
        for record in self:
            record.cam_total = (record.chargeable_area * record.cam_rate)

    @api.depends('cam_carpet_area', 'cam_rate', 'use_carpet', 'use_chargeable')
    def cam_carpet_value(self):
        for record in self:
            if record.use_carpet:
                record.cam_carpet = record.cam_carpet_area * record.cam_rate
            else:
                record.cam_carpet = 0.0

    @api.depends('chargeable_area', 'cam_rate', 'use_carpet', 'use_chargeable')
    def cam_charge_value(self):
        for record in self:
            if record.use_chargeable:
                record.cam_chargeable = record.cam_chargeable_area * record.cam_rate
            else:
                record.cam_chargeable = 0.0

    @api.onchange('use_carpet')
    def _onchange_use_carpet(self):
        if self.use_carpet:
            self.use_chargeable = False

    @api.onchange('use_chargeable')
    def _onchange_use_chargeable(self):
        if self.use_chargeable:
            self.use_carpet = False

    @api.onchange('tenancy_id')
    def _onchange_tenancy_id(self):
        if self.tenancy_id and self.tenancy_id.tenant_type.name == 'Kiosks':
            self.month_date = 11
        else:
            self.month_date = 1

    @api.depends('use_carpet', 'use_chargeable')
    def _total_amount_words_for_cam(self):
        for record in self:
            if record.use_carpet:
                amount = record.cam_carpet
            elif record.use_chargeable:
                amount = record.cam_chargeable
            else:
                amount = record.cam_fixed

            # Convert to words (Indian system, title case, remove commas)
            amount_words = num2words(amount, lang='en_IN')
            amount_words_clean = amount_words.replace(",", "").title() + " Only"

            record.total_cam_in_words = amount_words_clean

    @api.onchange('cam_type')
    def value_cam_type_chnage(self):
        for rec in self:
            if rec.cam_type == 'cam_sft':
                rec.cam_fixed = 0
            else:
                rec.use_carpet = False
                rec.use_chargeable = False

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

    @api.depends('cam_carpet_area', 'cam_percentage')
    def _calculate_chargeable_area_cam(self):
        for record in self:
            if (record.cam_carpet_area and record.cam_percentage) and record.cam_percentage != '0.00':
                record.cam_chargeable_area = ((record.cam_percentage / 100.0) * record.cam_carpet_area) + record.cam_carpet_area
            else:
                record.cam_chargeable_area = record.cam_carpet_area

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
    @api.onchange('renewal_type', 'ndays', 'end_year', 'month_date', 'quaterly', 'halfday', 'end_date', 'start_date',
                  'total_rent')
    def change_the_value_add(self):
        if not (self.renewal_type and self.start_date and self.end_date):
            return

        self.year_ids = [(5, 0, 0)]
        base_date = self.start_date
        new_records = []

        if self.renewal_type == 'year':
            increment = relativedelta(years=self.ndays)
        elif self.renewal_type == 'quat':
            increment = relativedelta(months=3)
        elif self.renewal_type == 'half':
            increment = relativedelta(months=6)
        elif self.renewal_type == 'monthly':
            increment = relativedelta(months=self.month_date or 1)
        else:
            return

        while base_date < self.end_date:
            start_year = base_date
            end_year = start_year + increment
            if end_year > self.end_date:
                end_year = self.end_date  # cap to end
            new_records.append((0, 0, {
                'start_year': start_year,
                'end_date': end_year - timedelta(days=1),
                'end_year': end_year,
            }))
            base_date = end_year

        self.year_ids = new_records

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

    # this is for the tenancy finance team draft post message
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
                # self.talend_invoice()
        self.cam_product_invoice()
        self.notif_finance_tm()
        res = super(TenancyDetails, self).action_active_contract()
        return res

    def cam_product_invoice(self):
        """Create an invoice for cam."""
        invoice_date = fields.Date.today()
        for record in self:
            if self.cam_type:

                rec = self.env['product.product'].search([('name', '=', 'Cam Maintenance')], limit=1)
                price_unit = 0
                nhcl_area_units = 0

                if record.use_carpet:
                    price_unit = record.cam_carpet
                    print("price unit use carpet", price_unit)
                    # area_used = record.carpet_area
                    nhcl_area_units = self.cam_carpet_area
                elif record.use_chargeable:
                    price_unit = record.cam_chargeable
                    print("price unit use_chargable", price_unit)
                    nhcl_area_units = self.cam_chargeable_area
                else:
                    price_unit = record.cam_fixed
                    nhcl_area_units = 0
                if rec:
                    # area_used = record.chargeable_area
                    invoice_vals = {
                        'partner_id': record.tenancy_id.id,
                        'move_type': 'out_invoice',
                        'invoice_date': fields.Date.today(),
                        'nhcl_invoice_type': 'cam',
                        'invoice_line_ids': [(0, 0, {
                            'product_id': rec.id,
                            'name': 'Cam ',
                            'quantity': 1,
                            'price_unit': price_unit,
                            'nhcl_area_units': nhcl_area_units

                        })],
                    }
                    invoice_id = self.env['account.move'].sudo().create(invoice_vals)
                    invoice_id.tenancy_id = self.id
                    # invoice_id.action_post()
                    rent_invoice = {
                        'tenancy_id': record.id,
                        'type': 'maintenance',
                        'invoice_date': invoice_date,
                        'description': 'Cam for' + record.property_id.name,
                        'rent_invoice_id': invoice_id.id,
                        # 'amount': invoice_id.amount_total,
                        'amount': price_unit,
                        'rent_amount': self.total_rent,
                        'rent_depo_date': self.cau_depo_date
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
                            'price_unit': price_unit,
                            'nhcl_area_units': nhcl_area_units

                        })],
                    }
                    invoice_id = self.env['account.move'].sudo().create(invoice_vals)
                    invoice_id.tenancy_id = self.id
                    # invoice_id.action_post()
                    rent_invoice = {
                        'tenancy_id': record.id,
                        'type': 'maintenance',
                        'invoice_date': invoice_date,
                        'description': 'Cam for' + record.property_id.name,
                        'rent_invoice_id': invoice_id.id,
                        # 'amount': invoice_id.amount_total,
                        'amount': price_unit,
                        'rent_amount': self.total_rent,
                        'rent_depo_date': self.cau_depo_date
                    }
                    self.env['rent.invoice'].create(rent_invoice)

    @api.depends('carpet_area', 'percentage')
    def _calculate_chargeable_area(self):
        for record in self:
            if (record.carpet_area and record.percentage) and record.percentage != '0.00':
                record.chargeable_area = ((record.percentage / 100.0) * record.carpet_area) + record.carpet_area
            else:
                record.chargeable_area = record.carpet_area

    @api.depends('tenancy_id')
    def _depends_company_id(self):
        for record in self:
            record.tenancy_type = record.tenancy_id.tenant_type.name

    @api.constrains('contract_type')
    def _compute_is_brand_name_readonly(self):
        for record in self:
            if record.contract_type == 'running_contract':
                record.is_brand_name_readonly = 1

    # this is for if yhe value is less than zero then dont take caution deposit
    @api.constrains('caution_deposite')
    def _check_caution_deposite(self):
        for record in self:
            if record.caution_deposite < 0:
                raise ValidationError("Caution Deposit value cannot be less than zero.")

    @api.onchange('rate', 'sft_fixed', 'percentage', 'lum_sum', 'carpet_value_take', 'carpet_area')
    def _check_total(self):
        for rec in self:
            if self.sft_fixed != 'Fixed':
                if self.carpet_value_take:
                    rec.total_rent = rec.carpet_area * rec.rate
                else:
                    rec.total_rent = rec.chargeable_area * rec.rate
            else:
                rec.total_rent = rec.lum_sum

    @api.depends('renewal_type')
    def _check_renewal_type(self):
        for record in self:
            if record.renewal_type == 'year' and fields.Date.today() == self.start_date + relativedelta(years=2):
                self.hide_rent = True

    def cron_job_invoice_create(self):
        tenancy_records = self.env['tenancy.details'].search(
            [('contract_type', '=', 'running_contract'), ('is_partial_month', '=', True)], order='tenancy_seq ASC'
        )
        today = fields.Date.today()  # may 8 2025
        first_day_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        last_day_last_month = today.replace(day=1) - timedelta(days=1)
        invoice_year = first_day_last_month.year
        invoice_month = first_day_last_month.month
        total_days = calendar.monthrange(invoice_year, invoice_month)[1]
        for rec in tenancy_records:
            if rec.start_date > last_day_last_month:
                continue  # Tenancy hasn't started yet

            # Determine if any renewal happened in this billing month
            renewal_line = None
            renewal_date = None
            previous_amount = rec.total_rent

            all_renewals = rec.year_ids.sorted('start_year')

            for line in all_renewals:
                if line.start_year and line.start_year <= last_day_last_month:
                    renewal_line = line  # get latest applicable
                    renewal_date = line.start_year
                else:
                    break

            if renewal_line and renewal_date.year == invoice_year and renewal_date.month == invoice_month:
                renewal_day = renewal_date.day
                new_rent = renewal_line.amount

                if renewal_day == 1:
                    self._create_invoice(
                        rec, new_rent, invoice_year, invoice_month,
                        "Full Month - New Rent (Renewal on Day 1)"
                    )
                else:
                    # Split the invoice between old and new rent
                    old_days = renewal_day - 1
                    new_days = total_days - old_days

                    old_rent_amount = (previous_amount / total_days) * old_days
                    new_rent_amount = (new_rent / total_days) * new_days

                    self._create_invoice(
                        rec, old_rent_amount, invoice_year, invoice_month,
                        f"Old Rent for {old_days} days"
                    )
                    self._create_invoice(
                        rec, new_rent_amount, invoice_year, invoice_month,
                        f"New Rent for {new_days} days"
                    )

                renewal_line.is_invoice_generated = True  # prevent duplicate invoices
            else:
                # No renewal: use last known rent
                rent_amount = previous_amount
                if renewal_line:
                    rent_amount = renewal_line.amount
                self._create_invoice(
                    rec, rent_amount, invoice_year, invoice_month,
                    "Full Month - Regular Rent"
                )
        print('successfully created two invoice')

    def _create_invoice(self, tenancy, amount, year, month, note):
        # Dummy implementation – replace with your actual invoice logic
        print(f"Creating invoice for {tenancy.tenancy_seq} | {year}-{month} | Amount: {amount:.2f} | Note: {note}")

    # create a new one2many child record, from every tenant to a floor plan directly
    def _create_a_floor_plan_for_tenancy(self):
        for rec in self:
            rec.property_id.floreplan_ids = [(0, 0, {
                'title': rec.tenancy_seq,
                'floor_no': str(rec.floor_no),
                'total_sft': rec.carpet_area,
                'status': 'active' if rec.contract_type == 'running_contract' else 'inactive',
                'tenancy': rec.id,
                'property_id': rec.property_id.id,
            })]

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res._create_a_floor_plan_for_tenancy()
        return res

    def supporting_documents(self):
        channel = self.env['discuss.channel'].search([('name', '=', 'Supporting Expiry')])
        if not channel:
            user_ids = self.env['res.users'].search([]).ids
            channel = self.env['discuss.channel'].create({
                'name': 'Supporting Expiry',
                'channel_type': 'group',
                'channel_partner_ids': [(4, user.partner_id.id) for user in
                                        self.env['res.users'].browse(user_ids)],
            })
        tenancy_data = self.env['tenancy.details'].search([('contract_type', '=', 'running_contract')])
        for rec in tenancy_data:
            today_date = fields.Date.today()
            for sp in rec.supporting_ids:
                past_date = sp.end_date - relativedelta(months=1)
                print(past_date, today_date)
                if past_date == today_date:
                    channel.message_post(
                        body=f"the certificate type  {sp.attachment_name} is expirying on the {sp.end_date} please review it. aleart",
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment',
                    )
                    print('satisfied')

    @api.model
    def cron_notify_tenancy_end_dates(self):
        today = date.today()

        # Mapping: how many days before + which flag to use
        notify_days = {
            60: 'notif_60_sent',
            45: 'notif_45_sent',
            30: 'notif_30_sent',
            15: 'notif_15_sent',
        }
        channel = self.env['discuss.channel'].search([('name', '=', 'Expairy Tenancy Alert')])
        template = self.env.ref('nhcl_rental_management.expairy_date_before_2month')
        # Create the channel if it does not exist
        if not channel:
            user_ids = self.env['res.users'].search([]).ids
            channel = self.env['discuss.channel'].create({
                'name': 'Expairy Tenancy Alert',
                'channel_type': 'group',
                'channel_partner_ids': [(4, user.partner_id.id) for user in self.env['res.users'].browse(user_ids)],
            })

        for days_before, flag_field in notify_days.items():
            target_date = today + timedelta(days=days_before)

            # Only get tenancies that end on the target date and haven’t been notified yet
            records = self.env['tenancy.details'].search([
                ('end_date', '=', target_date),
                (flag_field, '=', False),
            ])

            for tenancy in records:
                # Post notification to chatter
                tenancy.message_post(
                    body=f"Reminder: Tenancy is ending on {tenancy.end_date}. ({days_before} days remaining)",
                    subject="Tenancy Expiry Notification"
                )
                template.send_mail(tenancy.id, force_send=True)
                channel.message_post(
                    body=f"email sent to tenant: {tenancy.tenancy_id.name} for Expairy",
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )
                print('wowowowowowowowowoqwow')

                # Set the correct notification flag to True
                setattr(tenancy, flag_field, True)

    @api.onchange('cam_frequency', 'start_date', 'end_date', 'cam_month_date', 'cam_quaterly', 'cam_halfday',
                  'cam_ndays')
    def _generate_cam_lines(self):
        if not (self.cam_frequency and self.start_date and self.end_date):
            return

        self.cam_year_ids = [(5, 0, 0)]  # Clear previous lines

        base_date = self.start_date
        new_records = []

        # Define period increment based on frequency
        if self.cam_frequency == 'monthly':
            increment = relativedelta(months=self.cam_month_date or 1)

        elif self.cam_frequency == 'quarterly':
            increment = relativedelta(months=3)

        elif self.cam_frequency == 'halfyearly':
            increment = relativedelta(months=6)

        elif self.cam_frequency == 'yearly':
            increment = relativedelta(years=self.cam_ndays or 1)

        else:
            return

        while base_date < self.end_date:
            start_period = base_date
            end_period = start_period + increment

            if end_period > self.end_date:
                end_period = self.end_date

            new_records.append((0, 0, {
                'cam_start_year': start_period,
                'cam_end_date': end_period - timedelta(days=1),
                'cam_end_year': end_period,
            }))
            base_date = end_period

        self.cam_year_ids = new_records
