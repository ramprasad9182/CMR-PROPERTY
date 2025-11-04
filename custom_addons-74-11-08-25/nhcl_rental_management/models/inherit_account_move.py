import calendar
import typing
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from calendar import monthrange
from email.policy import default
from odoo.exceptions import UserError, ValidationError
from odoo import fields, api, models, _
import base64


class AccountMove(models.Model):
    _inherit = 'account.move'

    state = fields.Selection(
        [('draft', 'Draft'), ('approve', 'Approve'), ('posted', 'Posted'), ('cancel', 'Cancelled')], default='draft')

    needs_approval = fields.Boolean(string="Needs Approval", default=False)
    nhcl_invoice_type = fields.Selection(
        [('rent', 'Rent'), ('cam', 'Cam'), ('regular', 'Regular'), ('advanced', 'Rent Security Deposit'),
         ('marketing', 'Marketing'),
         ('electric', 'Utility Charge'), ('gas', 'Gas'), ('signage', 'Signage'), ('mg', 'MG'), ('mg_or', 'MG or RS'),
         ('rs', 'RS'), ('adv_cam_fee', 'CAM Security Deposit'), ('slb', 'Slab Wise')], string="Invoice Type",
        copy=False,)
    invoice_month_range = fields.Char(string="Invoice Month Range", compute="_compute_invoice_month_range",
                                      store=True, )
    cam_fields = fields.Boolean(string="Check", compute='get_fields', default=False)
    amount_in_words = fields.Char(string='Amount in Words', compute='_compute_amount_in_words', store=True)
    for_ammount = fields.Integer(string='Amount change', compute='_get_amount', default=1)
    check_post = fields.Integer(string='Check post', default=0)
    months = fields.Selection([
        ('jan', 'January'),
        ('feb', 'February'),
        ('mar', 'March'),
        ('apr', 'April'),
        ('may', 'May'),
        ('jun', 'June'),
        ('jul', 'July'),
        ('aug', 'August'),
        ('sep', 'September'),
        ('oct', 'October'),
        ('nov', 'November'),
        ('dec', 'December')
    ], string="Months")
    date = fields.Date(string='Invoice Date', default=fields.Date.context_today)
    penality = fields.Float(string='Penality')
    comparision_yr_mnth = fields.Many2one('tenancy.relation.year', string='Comparison')
    billing_from = fields.Date(string='Billing Period From', default=lambda self: date.today().replace(day=1))
    billing_to = fields.Date(string='Billing Period To', default=lambda self: date.today().replace(day=1))
    billing_range_display = fields.Char(string='Billing Range', compute='_compute_billing_range')
    # marketing type invoice field
    po_number_category = fields.Char(string='Po Number')
    po_date = fields.Date(string='Po Date')
    site_location_num = fields.Char(string='Site Location Number')
    total_amount_show = fields.Float(string='Total Amount', compute='total_amount_count_discount')
    discount_amount_show = fields.Float(string='Discount Value', compute='total_amount_count_discount')
    rs_amount = fields.Float(string="RS Amount")
    mg_amount = fields.Float(string="MG Amount")
    slab_amount = fields.Float(string="Slab Amount")

    nhcl_invoice_type_label = fields.Char(
        string='Invoice Type Label',
        compute='_compute_invoice_type_label',
        store=False  # No need to store unless used in search/sort
    )

    def _compute_invoice_type_label(self):
        for rec in self:
            rec.nhcl_invoice_type_label = dict(self._fields['nhcl_invoice_type'].selection).get(rec.nhcl_invoice_type,
                                                                                                '')
    #
    @api.onchange('billing_from','billing_to')
    def _onchange_billing_from(self):
        print('calling monthsssssssssssssssssssss')
        if self.billing_from and self.nhcl_invoice_type in ['rent','cam']:
            month_str = self.billing_from.strftime('%b').lower()
            self.months = month_str
            print("self.months ",self.months )

    @api.depends('invoice_line_ids')
    def total_amount_count_discount(self):
        for rec in self:
            if rec.invoice_line_ids:
                line = rec.invoice_line_ids[0]
                rec.total_amount_show = line.price_unit
                rec.discount_amount_show = line.price_unit * (line.discount / 100)
            else:
                rec.total_amount_show = 0
                rec.discount_amount_show = 0

    @api.constrains('billing_from', 'billing_to', 'invoice_line_ids')
    def _compute_billing_range(self):
        for record in self:

            if record.billing_from and record.billing_to and record.invoice_line_ids:

                record.invoice_line_ids[0].description2 = ""
                from_str = record.billing_from.strftime("%-d %B %Y")
                to_str = record.billing_to.strftime("%-d %B %Y")
                record.billing_range_display = f"{from_str} to {to_str}"
                if record.invoice_line_ids and record.nhcl_invoice_type == 'rent':

                    desc = 'Rental Invoice for the period of'
                    record.invoice_line_ids[0].description2 = desc + f"{from_str} to {to_str}"
                elif record.invoice_line_ids and record.nhcl_invoice_type == 'cam':

                    desc = 'CAM Invoice for the period of'
                    record.invoice_line_ids[0].description2 = desc + f"{from_str} to {to_str}"
            else:
                record.billing_range_display = ""
                # continue

    @api.constrains('billing_from', 'billing_to', 'invoice_line_ids.price_unit')
    def _compute_billing_range_price_total(self):
        if self.invoice_line_ids:
            matched_cam = None
            for record in self:
                if record.billing_from and record.billing_to and record.tenancy_id and record.invoice_line_ids and record.nhcl_invoice_type == 'rent':
                    # print("hii")
                    from_date = record.billing_from
                    to_date = record.billing_to
                    billed_days = (to_date - from_date).days + 1
                    print("billed day", billed_days)
                    month_days = monthrange(from_date.year, from_date.month)[1]

                    matched_renewal = None
                    for renewal in record.tenancy_id.year_ids:
                        start = renewal.start_year
                        end = renewal.end_date

                        if isinstance(start, date) and isinstance(end, date):
                            if start <= from_date <= end:
                                matched_renewal = renewal
                                print("matched_renewal", matched_renewal)
                                break

                    if matched_renewal:
                        rent_amount = matched_renewal.amount
                        price_unit = round((rent_amount / month_days) * billed_days, 2)
                        print("price_unit", price_unit)
                        print("rent_amount", rent_amount)
                    else:
                        # Fallback: use total rent directly (not prorated)
                        price_unit = record.tenancy_id.total_rent
                        print("done")

                        # ✅ Apply the computed price_unit to all invoice lines (or selectively)

                    for line in record.invoice_line_ids:
                        line.price_unit = price_unit
                        print("line.price_unit", line.price_unit)
                elif record.billing_from and record.billing_to and record.tenancy_id and record.invoice_line_ids and record.nhcl_invoice_type == 'cam':
                    print("CAM Billing")
                    from_date = record.billing_from
                    to_date = record.billing_to
                    billed_days = (to_date - from_date).days + 1
                    month_days = monthrange(from_date.year, from_date.month)[1]
                    # month_days = self.months

                    for cam in record.tenancy_id.cam_year_ids:
                        start = cam.cam_start_year
                        end = cam.cam_end_date
                        print(cam.cam_amount)
                        if isinstance(start, date) and isinstance(end, date):
                            if start <= from_date <= (end or start):  # in case end is None

                                # print('matched data')
                                matched_cam = cam
                                print(matched_cam, "//////////", matched_cam.cam_yid.tenancy_seq,
                                      matched_cam.cam_start_year, matched_cam.cam_amount)
                                break

                    if matched_cam:
                        cam_amount = matched_cam.cam_amount
                        price_unit = round((cam_amount / month_days) * billed_days, 2)
                    else:
                        price_unit = 0.0  # fallback
                    for line in record.invoice_line_ids:
                        line.price_unit = price_unit
                else:
                    continue
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

    @api.depends('needed_terms', 'invoice_date', 'invoice_date_due')
    def _compute_invoice_date_due(self):
        # First run Odoo's logic
        super()._compute_invoice_date_due()

        for move in self:
            # If no payment term is set, override the due date
            if not move.invoice_payment_term_id:
                base_date = move.invoice_date or fields.Date.context_today(move)
                if move.nhcl_invoice_type in ['rent', 'cam', 'electric','rs']:
                    move.invoice_date_due = base_date + timedelta(days=7)
                elif move.nhcl_invoice_type == 'gas':
                    move.invoice_date_due = base_date + timedelta(days=2)
                # elif move.nhcl_invoice_type == 'signage':
                #     move.invoice_date_due = base_date + timedelta(days=2)
                else:
                    move.invoice_date_due = base_date

    @api.onchange('nhcl_invoice_type', 'invoice_line_ids')
    def get_fields(self):
        invoice = self.env.context.get('default_move_type') == 'out_invoice'
        credit_note = self.env.context.get('default_move_type') == 'out_refund' and self.env.context.get(
            'display_account_trust', False)
        for rec in self:

            if (invoice and rec.nhcl_invoice_type == 'electric') or (
                    credit_note and rec.nhcl_invoice_type == 'electric'):
                rec.cam_fields = True
            else:
                rec.cam_fields = False

            # multiplying_factor logic
            for line in rec.invoice_line_ids:
                if rec.nhcl_invoice_type == 'gas':
                    line.multiplying_factor = 4.8020
                # else:
                #     line.multiplying_factor = 0.0

    # this is for the invoice date for report

    def _generate_electric_lines(self):
        for move in self:
            if move.nhcl_invoice_type != 'electric' or not move.partner_id:
                return
            comparison_month = move.comparision_yr_mnth.name
            if not  comparison_month:
                continue
            year=comparison_month[-1:-5:-1]
            print(comparison_month)
            print(year[::-1],year)

            d = move.months

            bill = self.env['catagory.bill'].search([
                ('ten', '=', move.partner_id.id),
                ('months', '=', d), ('is_invoice_created', '=', False), ('year', '=', year[::-1])
            ], limit=1)
            if not bill or not bill.ct_line_ids:
                raise ValidationError('Already created one Eb bill or does not present')
            lines = bill.ct_line_ids.sorted(key=lambda l: l.dt)
            first_line = lines[0]
            last_line = lines[-1]
            reset_line = next((l for l in lines if l.open_unit < 1), None)
            prev_line = None
            for i, line in enumerate(lines):
                if line.open_unit < 1:
                    if i > 0:
                        prev_line = lines[i - 1]
                        break

            product = self.env['product.product'].search([('name', '=', 'Air Conditional APEPDCL')], limit=1)
            if not product:
                raise ValidationError("Product 'Air Conditional APEPDCL' not found.")

            invoice_lines = []

            if not reset_line:
                # Case 1
                opening = first_line.open_unit
                closing = last_line.close_unit
                consumption = (closing - opening)  # * 1000
                invoice_lines.append((0, 0, {
                    'product_id': product.id,
                    'name': "Electricity Usage",
                    'opening_reading': opening,
                    'closing_reading': closing,
                    'consumption': consumption,
                }))
            else:
                # Case 2
                opening_1 = first_line.open_unit  # 50
                closing_1 = prev_line.close_unit  # open_unit#20
                consumption_1 = (closing_1 - opening_1) * 1000  # 20*1000-50
                invoice_lines.append((0, 0, {
                    'product_id': product.id,
                    'name': "Electricity Usage (Before Reset)",
                    'opening_reading': opening_1,
                    'closing_reading': closing_1,
                    'consumption': consumption_1,
                }))
                opening_2 = reset_line.open_unit  # open_unit
                closing_2 = last_line.close_unit
                consumption_2 = closing_2 - opening_2
                invoice_lines.append((0, 0, {
                    'product_id': product.id,
                    'name': "Electricity Usage (After Reset)",
                    'opening_reading': opening_2,
                    'closing_reading': closing_2,
                    'consumption': consumption_2,
                }))
            hvac = self.env['hvac.reading'].search([
                ('tenant_id', '=', move.partner_id.id),
                ('month', '=', d)
            ], limit=1)
            # this is for the hvac screen value line creation
            if hvac and hvac.hvac_line_ids:
                hvac_lines = hvac.hvac_line_ids.sorted(key=lambda l: l.date)
                first_line = hvac_lines[0]
                last_line = hvac_lines[-1]
                reset_line = next((l for l in hvac_lines if l.opening_unit < 1), None)
                prev_line = None
                for i, line in enumerate(hvac_lines):
                    if line.opening_unit < 1:
                        if i > 0:
                            prev_line = hvac_lines[i - 1]
                            break
                product_hvac = self.env['product.product'].search(
                    [('name', '=', 'Air Conditioning')], limit=1)
                if not product_hvac:
                    raise ValidationError("Product 'Air Conditioning' not found.")

                if not reset_line:
                    print('caling if ')
                    # Case 1: No reset
                    opening = first_line.opening_unit
                    closing = last_line.closing_unit
                    consumption = closing - opening

                    invoice_lines.append((0, 0, {
                        'product_id': product_hvac.id,
                        'name': "HVAC Usage",
                        'opening_reading': opening,
                        'closing_reading': closing,
                        'consumption': consumption,
                    }))
                else:
                    print('calling else')
                    # Case 2: Reset occurred
                    opening_1 = first_line.opening_unit
                    closing_1 = prev_line.closing_unit
                    consumption_1 = (closing_1 - opening_1) * 1000

                    invoice_lines.append((0, 0, {
                        'product_id': product_hvac.id,
                        'name': "HVAC Usage (Before Reset)",
                        'opening_reading': opening_1,
                        'closing_reading': closing_1,
                        'consumption': consumption_1,
                    }))

                    opening_2 = reset_line.opening_unit
                    closing_2 = last_line.closing_unit
                    consumption_2 = closing_2 - opening_2

                    invoice_lines.append((0, 0, {
                        'product_id': product_hvac.id,
                        'name': "HVAC Usage (After Reset)",
                        'opening_reading': opening_2,
                        'closing_reading': closing_2,
                        'consumption': consumption_2,
                    }))

            dg = self.env['dg.reading'].search([
                ('tenant_id', '=', move.partner_id.id),
                ('month', '=', d), ('year', '=', year[::-1])
            ], limit=1)
            # this is for the DG  screen value line creation
            if dg and dg.dg_line_ids:
                dg_lines = dg.dg_line_ids.sorted(key=lambda l: l.date)
                first_line = dg_lines[0]
                last_line = dg_lines[-1]
                reset_line = next((l for l in dg_lines if l.opening_unit < 1), None)
                prev_line = None
                for i, line in enumerate(hvac_lines):
                    if line.opening_unit < 1:
                        if i > 0:
                            prev_line = hvac_lines[i - 1]
                            break
                product_hvac = self.env['product.product'].search(
                    [('name', '=', 'DG01')], limit=1)
                if not product_hvac:
                    raise ValidationError("Product 'DG01' not found.")

                if not reset_line:
                    print('caling if ')
                    # Case 1: No reset
                    opening = first_line.opening_unit
                    closing = last_line.closing_unit
                    consumption = closing - opening
                    invoice_lines.append((0, 0, {
                        'product_id': product_hvac.id,
                        'name': "DG01 Usage",
                        'opening_reading': opening,
                        'closing_reading': closing,
                        'consumption': consumption,
                    }))
                else:
                    print('calling else')
                    # Case 2: Reset occurred
                    opening_1 = first_line.opening_unit
                    closing_1 = prev_line.closing_unit
                    consumption_1 = (closing_1 - opening_1) * 1000

                    invoice_lines.append((0, 0, {
                        'product_id': product_hvac.id,
                        'name': "DG01 Usage (Before Reset)",
                        'opening_reading': opening_1,
                        'closing_reading': closing_1,
                        'consumption': consumption_1,
                    }))
                    opening_2 = reset_line.opening_unit
                    closing_2 = last_line.closing_unit
                    consumption_2 = closing_2 - opening_2

                    invoice_lines.append((0, 0, {
                        'product_id': product_hvac.id,
                        'name': "DG01 Usage (After Reset)",
                        'opening_reading': opening_2,
                        'closing_reading': closing_2,
                        'consumption': consumption_2,
                    }))
            # cool water line created
            hot_water = self.env['hot.water.reading'].search([
                ('tenant_id', '=', move.partner_id.id),
                ('month', '=', d)
            ], limit=1)

            if hot_water and hot_water.hot_water_line_ids:
                hw_lines = hot_water.hot_water_line_ids.sorted(key=lambda l: l.date)
                first_line = hw_lines[0]
                last_line = hw_lines[-1]
                reset_line = next((l for l in hw_lines if l.opening_unit < 1), None)
                prev_line = None
                for i, line in enumerate(hw_lines):
                    if line.opening_unit < 1:
                        if i > 0:
                            prev_line = hw_lines[i - 1]
                            break
                product_hw = self.env['product.product'].search([('name', '=', 'Air Conditional APEPDCL')], limit=1)
                if not product_hw:
                    raise ValidationError("Product 'Air Conditional APEPDCL.")

                if not reset_line:
                    # No reset case
                    opening = first_line.opening_unit
                    closing = last_line.closing_unit
                    consumption = closing - opening
                    invoice_lines.append((0, 0, {
                        'product_id': product_hw.id,
                        'name': "Cool Water Usage",
                        'opening_reading': opening,
                        'closing_reading': closing,
                        'consumption': consumption,
                    }))
                else:
                    # Reset occurred
                    opening_1 = first_line.opening_unit
                    closing_1 = prev_line.closing_unit
                    consumption_1 = (closing_1 - opening_1) *1000

                    invoice_lines.append((0, 0, {
                        'product_id': product_hw.id,
                        'name': "Cool Water Usage (Before Reset)",
                        'opening_reading': opening_1,
                        'closing_reading': closing_1,
                        'consumption': consumption_1,
                    }))
                    opening_2 = reset_line.opening_unit
                    closing_2 = last_line.closing_unit
                    consumption_2 = closing_2 - opening_2
                    invoice_lines.append((0, 0, {
                        'product_id': product_hw.id,
                        'name': "Cool Water Usage (After Reset)",
                        'opening_reading': opening_2,
                        'closing_reading': closing_2,
                        'consumption': consumption_2,
                    }))
            # Get Water Reading for the partner and month
            water = self.env['water.reading'].search([
                ('tenant_id', '=', move.partner_id.id),
                ('month', '=', d)
            ], limit=1)

            if water and water.water_line_ids:
                water_lines = water.water_line_ids.sorted(key=lambda l: l.date)
                first_line = water_lines[0]
                last_line = water_lines[-1]
                reset_line = next((l for l in water_lines if l.opening_unit < 1), None)
                prev_line = None
                for i, line in enumerate(water_lines):
                    if line.opening_unit < 1:
                        if i > 0:
                            prev_line = water_lines[i - 1]
                            break

                # Get Product for Water Billing
                product_water = self.env['product.product'].search([
                    ('name', '=', 'Water Usage')
                ], limit=1)

                if not product_water:
                    raise ValidationError("Product 'Water Usage' not found.")

                if not reset_line:
                    # Case 1: No Reset
                    opening = first_line.opening_unit
                    closing = last_line.closing_unit
                    consumption = max(closing - opening, 0.0)

                    invoice_lines.append((0, 0, {
                        'product_id': product_water.id,
                        'name': "Water Usage",
                        'opening_reading': opening,
                        'closing_reading': closing,
                        'consumption': consumption,
                    }))
                else:
                    # Case 2: Reset Occurred

                    # Before Reset
                    opening_1 = first_line.opening_unit
                    closing_1 = prev_line.closing_unit
                    consumption_1 = max(closing_1 - opening_1, 0.0) * 1000

                    invoice_lines.append((0, 0, {
                        'product_id': product_water.id,
                        'name': "Water Usage (Before Reset)",
                        'opening_reading': opening_1,
                        'closing_reading': closing_1,
                        'consumption': consumption_1,
                    }))

                    # After Reset
                    opening_2 = reset_line.opening_unit
                    closing_2 = last_line.closing_unit
                    consumption_2 = max(closing_2 - opening_2, 0.0)

                    invoice_lines.append((0, 0, {
                        'product_id': product_water.id,
                        'name': "Water Usage (After Reset)",
                        'opening_reading': opening_2,
                        'closing_reading': closing_2,
                        'consumption': consumption_2,
                    }))
            move.invoice_line_ids = [(5, 0, 0)] + invoice_lines

    def get_previous_month(self, current_month):
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul',
                  'aug', 'sep', 'oct', 'nov', 'dec']
        index = months.index(current_month)
        return months[index - 1] if index > 0 else months[-1]

    @api.model
    def create(self, vals):
        if vals.get('billing_from') and vals.get('nhcl_invoice_type') in ['rent','cam']:
            print('getting data')
            billing_from = fields.Date.from_string(vals['billing_from'])
            vals['months'] = billing_from.strftime('%b').lower()

        move = super().create(vals)
        # Step 3: Generate electric lines if applicable
        if move.nhcl_invoice_type == 'electric':
            move._generate_electric_lines()

        return move

    # @api.constrains('partner_id')
    # def get_tenancy_record(self):
    #     for rec in self:
             #if self.move_type in ['out_invoice', 'out_refund']:
        #         if not rec.tenancy_id:
        #             raise UserError('This Customer not present in the Tenancy')

    @api.onchange('billing_from')
    def _onchange_billing_from(self):
        if not self.billing_from:
            return

        # Format as "Jul-2025"
        formatted_name = self.billing_from.strftime('%b-%Y')  # e.g., "Jul-2025"

        # Search if it already exists
        year_rec = self.env['tenancy.relation.year'].search([('name', '=', formatted_name)], limit=1)

        # If not found, create
        if not year_rec:
            year_rec = self.env['tenancy.relation.year'].create({'name': formatted_name})

    @api.depends('billing_from','billing_to')
    def _compute_invoice_month_range(self):
        for record in self:
            if record.invoice_date:
                # Parse the invoice_date into a date object
                invoice_date1 = fields.Date.from_string(record.billing_from)
                invoice_date2 = fields.Date.from_string(record.billing_to)
                formatted_range = f"{invoice_date1.strftime('%d/%b/%Y')} to {invoice_date2.strftime('%d/%b/%Y')}"
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

                account_post = self.env['account.move'].search(
                    [('state', '=', 'posted'), ('move_type', '=', 'out_invoice'), ('invoice_date', '!=', False)])
                for post in account_post:
                    if post.invoice_date == fields.Date.today():
                        # print("working successfully")
                        template.send_mail(post.id, force_send=True)

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


    def send_email_invoice(self):
        template = self.env.ref('nhcl_rental_management.invoice_message_post')
        template2 = self.env.ref('nhcl_rental_management.invoice_cam_post')
        template3 = self.env.ref('nhcl_rental_management.invoice_utility_post')
        template4 = self.env.ref('nhcl_rental_management.invoice_gas_post')

        # Send appropriate email
        if self.nhcl_invoice_type == 'cam':
            print("Invoice type is CAM. Sending CAM email...")
            template2.send_mail(self.id, force_send=True)
            self.getrecord_areaunit()
            print("CAM email sent and area unit recorded.")
        elif self.nhcl_invoice_type == 'gas':
            print("Invoice type is GAS. Sending GAS email...")
            template4.send_mail(self.id, force_send=True)
        elif self.nhcl_invoice_type == 'electric':
            print("Invoice type is ELECTRIC. Sending Electric email...")
            template3.send_mail(self.id, force_send=True)
        else:
            print("Default email being sent.")
            template.send_mail(self.id, force_send=True)

    def action_post(self):
        if self.move_type == 'out_invoice':
            for invoice in self:
                # if invoice.name in [False, '/']:

                    invoice_date = date.today()

                    if invoice_date.month < 4:
                        fy_start = invoice_date.year - 1
                    else:
                        fy_start = invoice_date.year

                    fy_code = f"{str(fy_start)[-2:]}{str(fy_start + 1)[-2:]}"  # e.g., '2526'
                    type_inv = invoice.nhcl_invoice_type
                    invoice_number = invoice._generate_invoice_number(type_inv, fy_code)
                    invoice.name = invoice_number
                    invoice.payment_reference = invoice_number
                    # Map selection keys to month numbers for comparison
                    month_order = {
                        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                        'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                        'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                    }

                    for invoice in self:
                        print('satisfied')
                        if invoice.months and invoice.move_type == 'out_invoice':
                            print('comming inside ///')
                            inv_month_num = month_order[invoice.months]

                            # Search all draft invoices for same tenant + type + company
                            draft_invoices = self.env['account.move'].search([
                                ('id', '!=', invoice.id),
                                ('partner_id', '=', invoice.partner_id.id),
                                ('nhcl_invoice_type', '=', invoice.nhcl_invoice_type),
                                ('move_type', '=', 'out_invoice'),
                                ('state', '=', 'draft'),
                            ], order="create_date desc", limit=1)
                            print(draft_invoices)

                            for draft in draft_invoices:
                                print('comming draft ///')
                                if draft.months:
                                    draft_month_num = month_order[draft.months]
                                    print(draft_month_num, "////", inv_month_num)
                                    if draft_month_num < inv_month_num:
                                        print(draft.name)
                                        raise UserError(_(
                                            f"You cannot post this invoice because another draft entry "
                                            f" exists for {dict(draft._fields['months'].selection).get(draft.months)} "
                                            f"which is after {dict(invoice._fields['months'].selection).get(invoice.months)} "
                                            f"for customer {invoice.partner_id.display_name}."
                                        ))

            res = super(AccountMove, self).action_post()

            for invoice in self:
                # Electric-specific logic
                if invoice.nhcl_invoice_type == 'electric' and invoice.invoice_date:
                    print("Processing electric invoice for:", invoice.name)
                    prev_month = invoice.months
                    category_bills = self.env['catagory.bill'].search([
                        ('ten', '=', invoice.partner_id.id),
                        ('months', '=', prev_month),
                        ('is_invoice_created', '=', False)
                    ])
                    print(f"Found {len(category_bills)} category bills to update.")

                    for bill in category_bills:
                        bill.is_invoice_created = True
                        print(f"Marked bill {bill.id} as invoiced.")

                # ❗ Skip validation if context flag is set
                if self.env.context.get('skip_rent_validation'):
                    print("Skipping rent/RS/MG/SLB validation due to context.")
                    continue

                # Validation logic for rent vs RS/MG/SLB
                if invoice.move_type == 'out_invoice' and invoice.tenancy_id:
                    print("Validating RS/MG vs Rent comparison...")
                    rent_invoices = self.env['account.move'].search([
                        ('tenancy_id', '=', invoice.tenancy_id.id),
                        ('nhcl_invoice_type', '=', 'rent'),
                        ('move_type', '=', 'out_invoice'),
                        ('state', '!=', 'cancel'),
                    ])
                    rs_invoice = self.env['account.move'].search([
                        ('tenancy_id', '=', invoice.tenancy_id.id),
                        ('nhcl_invoice_type', '=', 'rs'),
                        ('move_type', '=', 'out_invoice'),
                        ('state', '!=', 'cancel'),
                    ], limit=1)
                    sb_invoice = self.env['account.move'].search([
                        ('tenancy_id', '=', invoice.tenancy_id.id),
                        ('nhcl_invoice_type', '=', 'slb'),
                        ('move_type', '=', 'out_invoice'),
                        ('state', '!=', 'cancel'),
                    ], limit=1)
                    mg_invoice = self.env['account.move'].search([
                        ('tenancy_id', '=', invoice.tenancy_id.id),
                        ('nhcl_invoice_type', '=', 'mg'),
                        ('move_type', '=', 'out_invoice'),
                        ('state', '!=', 'cancel'),
                    ], limit=1)

                    print("Invoices fetched: Rent =", len(rent_invoices),
                          ", RS =", bool(rs_invoice),
                          ", SB =", bool(sb_invoice),
                          ", MG =", bool(mg_invoice))

                    rent_price = sum(rent_invoices.mapped('invoice_line_ids').mapped('price_unit'))
                    rs_price = sum(rs_invoice.invoice_line_ids.mapped('price_unit')) if rs_invoice else 0
                    sb_price = sum(sb_invoice.invoice_line_ids.mapped('price_unit')) if sb_invoice else 0
                    mg_price = sum(mg_invoice.invoice_line_ids.mapped('price_unit')) if mg_invoice else 0

                    print(f"Rent Price: {rent_price}, RS Price: {rs_price}, SB Price: {sb_price}, MG Price: {mg_price}")

                    msg = ""
                    if invoice.nhcl_invoice_type == 'rent':
                        invoice_type = invoice.tenancy_id.invoice_type
                        print("Invoice type from tenancy:", invoice_type)

                        if invoice_type == 'rs':
                            if invoice.rs_amount == 0:
                                msg = "RS Amount is not given"
                        elif invoice_type == 'mg':
                            if invoice.mg_amount == 0:
                                msg = "MG Amount is not given"
                        elif invoice_type == 'slb':
                            if invoice.slab_amount == 0:
                                msg = "Slab Amount is not given"
                        elif invoice_type == 'rs_or_mg':
                            if invoice.rs_amount == 0:
                                msg = "RS Amount is not given"
                            elif invoice.mg_amount == 0:
                                msg = "MG Amount is not given"

                        if msg:
                            print("Validation failed:", msg)
                            raise UserError(_(msg))

                        # Compare rent price with RS/SB/MG
                        if rent_price < rs_price:
                            raise UserError(_(f"Rent amount ({rent_price}) is less than RS amount ({rs_price})"))
                        if rent_price < sb_price:
                            raise UserError(_(f"Rent amount ({rent_price}) is less than SB amount ({sb_price})"))
                        if rent_price < mg_price:
                            raise UserError(_(f"Rent amount ({rent_price}) is less than MG amount ({mg_price})"))

                    # ✅ 🔒 ADDITIONAL VALIDATION for RS month & comparison match
                    elif invoice.nhcl_invoice_type == 'rs':
                        print("ntered")
                        related_rent_invoice = self.env['account.move'].search([
                            ('tenancy_id', '=', invoice.tenancy_id.id),
                            ('nhcl_invoice_type', '=', 'rent'),
                            ('comparision_yr_mnth', '=', invoice.comparision_yr_mnth.id),
                            ('move_type', '=', 'out_invoice'),
                            ('state', '!=', 'cancel'),
                        ], limit=1)
                        print("related",related_rent_invoice)

                        if related_rent_invoice:
                            print("related")
                            rent_month = related_rent_invoice.comparision_yr_mnth
                            rs_month = invoice.comparision_yr_mnth
                            print(rs_month.name,"rs_month")
                            print(rent_month.name,"invoice.months")
                            if rent_month != rs_month:
                                raise UserError(_(
                                    f"The RS invoice month '{rs_month}' does not match the Rent invoice month '{rent_month}' "
                                    f"for comparison period {invoice.comparision_yr_mnth.name}."
                                ))
                        else:
                            raise ValidationError('please change the  comparison month')

                        if rs_price < rent_price:
                            raise UserError(_(f"RS amount ({rs_price}) is less than Rent amount ({rent_price})"))

                    elif invoice.nhcl_invoice_type == 'mg' and mg_price < rent_price:
                        raise UserError(_(f"MG amount ({mg_price}) is less than Rent amount ({rent_price})"))
                    elif invoice.nhcl_invoice_type == 'slb' and sb_price < rent_price:
                        raise UserError(_(f"SB amount ({sb_price}) is less than Rent amount ({rent_price})"))

                    print("All validations passed.")

            print("action_post finished for:", self.name)
            return res



    def write(self, vals):
        # Prevent recursive write calls if name or payment_reference are being updated
        for demo in self:
            billing_from = fields.Date.from_string(vals.get('billing_from', demo.billing_from))
            nhcl_invoice_type = vals.get('nhcl_invoice_type', demo.nhcl_invoice_type)
            if billing_from and nhcl_invoice_type in ['rent', 'cam']:
                vals['months'] = billing_from.strftime('%b').lower()
        # if 'name' not in vals and 'payment_reference' not in vals:
        #     # Call the parent write method
            res = super(AccountMove, self).write(vals)
            # invoice_date = fields.Date.from_string(vals.get('date')) if vals.get('date') else date.today()
            #
            # # Calculate financial year: 2025 → 2526
            # if invoice_date.month < 4:
            #     fy_start = invoice_date.year - 1
            # else:
            #     fy_start = invoice_date.year
            #
            # fy_code = f"{str(fy_start)[-2:]}{str(fy_start + 1)[-2:]}"  # e.g., '2526'
            # print(fy_code)
            # for record in self:
                # if not record.name or record.name == '/':
                #     type_inv = record.nhcl_invoice_type
                #     invoice_number = record._generate_invoice_number(type_inv, fy_code)
                #
                #     # Assign generated invoice number
                #     record.name = invoice_number
                #     record.payment_reference = invoice_number
            if vals.get('nhcl_invoice_type') == 'electric' or 'partner_id' in vals:
                    demo._generate_electric_lines()

            return res

        # Fall back to default write if `name` or `payment_reference` is explicitly being set
        return super(AccountMove, self).write(vals)

    def _generate_invoice_number(self, invoice_type, fy_code):
        year = fields.Date.today().year  # Current year
        sequence_code = None
        if invoice_type == 'rent':
            sequence = self.env['ir.sequence'].with_context(fy=fy_code).next_by_code('invoice.rent.sequence')
            # sequence_code = 'invoice.rent.sequence'
            return sequence
        elif invoice_type == 'cam':
            # sequence_code = 'invoice.cam.sequence'
            sequence = self.env['ir.sequence'].with_context(fy=fy_code).next_by_code('invoice.cam.sequence')
            return sequence
        elif invoice_type == 'electric':
            # sequence_code = 'electric.invoice.sequence'
            sequence = self.env['ir.sequence'].with_context(fy=fy_code).next_by_code('electric.invoice.sequence')
            return sequence
        elif invoice_type == 'gas':
            # sequence_code = 'gas.invoice.sequence'
            sequence = self.env['ir.sequence'].with_context(fy=fy_code).next_by_code('gas.invoice.sequence')
            return sequence
        elif invoice_type == 'marketing':
            sequence_code = 'marketing.invoice.sequence'
            sequence = self.env['ir.sequence'].next_by_code(sequence_code)
            return sequence
        elif invoice_type == 'advanced':
            sequence_code = 'advanced.invoice.sequence'
            sequence = self.env['ir.sequence'].next_by_code(sequence_code)
            return sequence
        elif invoice_type == 'regular':
            sequence_code = 'account.invoice.sequence'
            sequence = self.env['ir.sequence'].next_by_code(sequence_code)
            return sequence
        elif invoice_type == 'signage':
            sequence = self.env['ir.sequence'].with_context(fy=fy_code).next_by_code('Signage.invoice.sequence')
            return sequence
        elif invoice_type == 'rs':
            sequence_code = 'rs.invoice.sequence'
            sequence = self.env['ir.sequence'].next_by_code(sequence_code)
            return sequence
        elif invoice_type == 'mg_or':
            sequence_code = 'mg.rs.invoice.sequence'
            sequence = self.env['ir.sequence'].next_by_code(sequence_code)
            return sequence
        elif invoice_type == 'adv_cam_fee':
            sequence_code = 'invoice.add.cam.sequence'
            sequence = self.env['ir.sequence'].next_by_code(sequence_code)
            return sequence
            # print(sequence_code)
        sequence = self.env['ir.sequence'].next_by_code(sequence_code) or '00001'
        print(sequence)
        return f"{sequence}"

    def get_and_update_invoice_data(self):
        today = fields.Date.today()
        ten_rec = self.env['tenancy.details'].search(
            [('contract_type', '=', 'running_contract'), ('is_partial_month', '=', True)],
            order='tenancy_seq ASC')
        print(ten_rec, "did not find any record ........")

        for rec in ten_rec:
            print(rec.tenancy_seq)
            c = 0
            for val in rec.year_ids:

                if val.end_year == today:  # and not val.is_invoice_generated:

                    # 🔽 First invoice
                    invoice_vals_1 = {
                        'partner_id': rec.tenancy_id.id,
                        'move_type': 'out_invoice',
                        'invoice_date': today,
                        'nhcl_invoice_type': 'rent',
                        'invoice_line_ids': [(0, 0, {
                            'product_id': self.env.ref('rental_management.property_product_1').id,
                            'name': 'Property Value ',
                            'quantity': 1,
                            'price_unit': 0,
                            'nhcl_area_units': rec.carpet_area if rec.carpet_value_take else rec.chargeable_area
                        })],
                    }
                    print(invoice_vals_1)
                    invoice_1 = self.env['account.move'].sudo().create(invoice_vals_1)
                    invoice_1.tenancy_id = rec.id

                    # 🔽 Second invoice
                    invoice_vals_2 = {
                        'partner_id': rec.tenancy_id.id,
                        'move_type': 'out_invoice',
                        'invoice_date': today,
                        'nhcl_invoice_type': 'rent',
                        'invoice_line_ids': [(0, 0, {
                            'product_id': self.env.ref('rental_management.property_product_1').id,
                            'name': 'Property Value ',
                            'quantity': 1,
                            'price_unit': 0,
                            'nhcl_area_units': rec.carpet_area if rec.carpet_value_take else rec.chargeable_area
                        })],
                    }

                    invoice_2 = self.env['account.move'].sudo().create(invoice_vals_2)
                    invoice_2.tenancy_id = rec.id
                    # ✅ Prevent reprocessing
                    val.is_invoice_generated = True
                c += 1
        self.get_and_update_cam_invoice_data()

        return True

    def get_and_update_cam_invoice_data(self):
        print('calling cam creation ???????????????')
        today = fields.Date.today()
        # Step 1: Find tenancy records with CAM Year lines ending today
        ten_cam = self.env['tenancy.details'].search([
            ('contract_type', '=', 'running_contract'),
            ('is_partial_month', '=', True),
            ('cam_year_ids.cam_end_year', '=', today)
        ])
        print(ten_cam)

        for rec in ten_cam:
            print('getting data')
            for cam_line in rec.cam_year_ids:
                nhcl_area_units = None
                if rec.use_carpet:
                    nhcl_area_units = rec.cam_carpet_area
                elif rec.use_chargeable:
                    nhcl_area_units = rec.cam_chargeable_area
                else:
                    nhcl_area_units = 0
                if cam_line.cam_end_year == today:
                    # Optional: Skip if invoice already generated
                    if getattr(cam_line, 'is_invoice_generated', False):
                        continue

                    # Step 2: Prepare invoice line for CAM
                    cam_invoice_vals = {
                        'partner_id': rec.tenancy_id.id,
                        'move_type': 'out_invoice',
                        'invoice_date': today,
                        'nhcl_invoice_type': 'cam',
                        'invoice_line_ids': [(0, 0, {
                            'product_id': self.env['product.product'].search([('name', '=', 'Cam Maintenance')],
                                                                             limit=1).id,
                            # Replace with actual external ID
                            'name': f'CAM Charges Renewal on {today}',
                            'quantity': 1,
                            'price_unit': cam_line.cam_amount or 0.0,
                            'nhcl_area_units': nhcl_area_units#rec.chargeable_area
                        })],
                    }

                    cam_invoice = self.env['account.move'].sudo().create(cam_invoice_vals)
                    cam_invoice.tenancy_id = rec.id
                    print('created sucessfull created')

                    # this is for the secound invoice creation
                    sec_invoice_vals = {
                        'partner_id': rec.tenancy_id.id,
                        'move_type': 'out_invoice',
                        'invoice_date': today,
                        'nhcl_invoice_type': 'cam',
                        'invoice_line_ids': [(0, 0, {
                            'product_id': self.env['product.product'].search([('name', '=', 'Cam Maintenance')],
                                                                             limit=1).id,
                            'name': f'CAM Charges Renewal on {today}',
                            'quantity': 1,
                            'price_unit': cam_line.cam_amount or 0.0,
                            'nhcl_area_units': nhcl_area_units
                        })],
                    }
                    sec_invoice = self.env['account.move'].sudo().create(sec_invoice_vals)
                    sec_invoice.tenancy_id = rec.id

                    # Step 3: Mark invoice generated
                    cam_line.is_invoice_generated = True
        return True

    @api.model
    def _apply_delta_recurring_entries(self, date, date_origin, period):
        """
        Calculates the next recurring date based on the given period.
        Adds one month by default to the result from the super method.
        """
        next_date = super(AccountMove, self)._apply_delta_recurring_entries(date, date_origin, period)
        print("Original next_date from parent:", next_date)

        # Optional adjustment
        # next_date = next_date + relativedelta(months=1)
        return next_date

    def _copy_recurring_entries(self):
        """
        Custom recurring entry logic:
        - Skips auto-posting in the renewal month.
        - Resumes posting in following months.
        """
        for record in self:
            print(record.tenancy_id.year_ids)

            record.auto_post_origin_id = record.auto_post_origin_id or record

            # Calculate the next posting date
            next_date = self._apply_delta_recurring_entries(
                record.date, record.auto_post_origin_id.date, record.auto_post
            )
            for data in record.tenancy_id.year_ids:
                if data.end_year.month == next_date.month and data.end_year.year == next_date.year:
                    print('Doneeeeeeeeeeeeeeeeeeee')

            # Stop if beyond the auto-post limit
            if record.auto_post_until and next_date > record.auto_post_until:
                continue

            # Skip posting if renewal starts this month
            renewal_in_same_month = any(
                renewal.end_year.month == (next_date.month - 1) and
                renewal.end_year.year == next_date.year
                for renewal in record.tenancy_id.year_ids
            )
            print("///////", renewal_in_same_month)
            if record.tenancy_id.is_partial_month and record.nhcl_invoice_type == 'rent':
                if renewal_in_same_month:
                    print(f"Skipping auto-posting for {record.name} in renewal month: {next_date.strftime('%B %Y')}")
                    continue  # Skip this month's posting

            # Otherwise, copy with updated date
            # record.copy(default=record._get_fields_to_copy_recurring_entries({'date': next_date}))
            record.copy(default=record._get_fields_to_copy_recurring_entries({
                'date': next_date,
                'nhcl_invoice_type': record.nhcl_invoice_type,
            }))
            print(f"Processed recurring entry for {record.name} with new date {next_date}")

    @api.model
    def default_get(self, fields_list):
        res = super(AccountMove, self).default_get(fields_list)
        try:
            # Replace this with the actual external ID for Andhra Pradesh
            default_state = self.env.ref('base.state_in_ap')  # Andhra Pradesh
            if default_state:
                res['l10n_in_state_id'] = default_state.id
        except ValueError:
            pass  # In case the external ID is missing or not installed
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    opening_reading = fields.Float(string='Opening Reading', digits=(16, 4))
    closing_reading = fields.Float(string='Closing Reading', digits=(16, 4))
    consumption = fields.Float(string="Consumption", store=True,default=0)
    consumed_units = fields.Float(string='Consumed Units', digits=(16, 4), compute='consumption_unit', store=True)
    nhcl_area_units = fields.Char(string='Area Units')
    rate = fields.Float(string='Rate', digits=(8, 4))
    multiplying_factor = fields.Float(string='Multiplying Factor', digits=(8, 4), store=True)
    description2 = fields.Char(string='Product')
    net_rent = fields.Float(string='Net Rent')
    percentage = fields.Float(string='Rate')
    mg_carpet = fields.Integer(string='Mg Carpet')
    mg_percentage = fields.Integer(string='Mg Percentage')

    price_unit = fields.Float(compute='_compute_price_unit', store=True)
    net_slab = fields.Float(string='Slab Rent')
    percentage_slab = fields.Float(string='Slab Percentage')





    @api.depends('consumption', 'multiplying_factor')
    def consumption_unit(self):
        for rec in self:
            rec.consumed_units = rec.consumption * rec.multiplying_factor

    @api.depends('consumed_units', 'rate', 'move_id.nhcl_invoice_type', 'net_rent', 'percentage', 'net_slab',
                 'percentage_slab', 'mg_percentage', 'mg_carpet')
    def _compute_price_unit(self):
        for rec in self:
            # print('calling')
            if rec.move_id.nhcl_invoice_type in ['electric', 'gas']:
                rec.price_unit = rec.consumed_units * rec.rate
            elif rec.move_id.nhcl_invoice_type in ['rs']:
                rec.price_unit = (rec.net_rent * (rec.percentage or 0.0) / 100.0)
            elif rec.move_id.nhcl_invoice_type == 'mg':
                rec.price_unit = rec.mg_carpet + (rec.mg_carpet * rec.mg_percentage / 100)
            elif rec.move_id.nhcl_invoice_type in ['slb']:
                rec.price_unit = rec.net_slab + (rec.net_slab * (rec.percentage_slab or 0.0) / 100.0)
            else:
                rec.price_unit = 0.0

    # @api.depends('opening_reading', 'closing_reading')
    # def _compute_consumption(self):
    #     for line in self:
    #         if line.closing_reading > line.opening_reading:
    #             line.consumption = (line.closing_reading - line.opening_reading)
    #         elif line.opening_reading >= line.closing_reading:
    #             # line.consumption = (line.closing_reading * 1000) - line.opening_reading
    #             line.closing_reading = (line.closing_reading * 1000)
    #             line.consumption = (line.closing_reading) - line.opening_reading
    #             print(line.consumption,'??????????????????????????jjjjjjjjjj')
    #         else:
    #             line.consumption = 0.0

    # @api.onchange('price_unit')
    # def _onchange_price_unit(self):
    #     print('price chnage happen')
    #     for line in self:
    #         move = line.move_id
    #         if move.tenancy_id:
    #             rent_invoice = self.env['account.move'].search([
    #                 ('nhcl_invoice_type', '=', 'rent'),
    #                 ('tenancy_id', '=', move.tenancy_id.id),
    #                 ('state', '!=', 'cancel'),
    #             ], limit=1)
    #             print(rent_invoice,rent_invoice.name)
    #
    #             # if rent_invoice:
    #             #     if move.nhcl_invoice_type == 'rs':
    #             #         rent_invoice.rs_amount = line.price_unit
    #             #     elif move.nhcl_invoice_type == 'mg':
    #             #         rent_invoice.mg_amount = line.price_unit
    #             #     elif move.nhcl_invoice_type == 'slb':
    #             #         rent_invoice.slab_amount = line.price_unit
    #
    #             if rent_invoice:
    #                 if move.nhcl_invoice_type == 'rs':
    #                     rent_invoice.rs_amount = line.price_unit
    #                 elif move.nhcl_invoice_type == 'mg':
    #                     rent_invoice.mg_amount = line.price_unit
    #                 elif move.nhcl_invoice_type == 'slb':
    #                     rent_invoice.slab_amount = line.price_unit
    # @api.depends('opening_reading', 'closing_reading')
    # def _compute_consumption(self):
    #     for line in self:
    #         if line.closing_reading > line.opening_reading and line.opening_reading > 0:
    #             line.consumption = (line.closing_reading - line.opening_reading) * 1000
    #         # elif line.opening_reading > line.closing_reading:
    #         #     # line.consumption = (line.closing_reading * 1000) - line.opening_reading
    #         #     line.closing_reading = (line.closing_reading * 1000)
    #         #     line.consumption = (line.closing_reading) - line.opening_reading
    #         else:
    #             line.consumption = (line.closing_reading) - line.opening_reading

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id')
    def _compute_totals(self):
        # Call the original method from the parent class
        super()._compute_totals()

        # Apply rounding to price_subtotal
        for line in self:
            if line.display_type in ('product', 'cogs') and line.price_subtotal:
                line.price_subtotal = round(line.price_subtotal)
                line.price_unit = round(line.price_unit)



    @api.onchange('price_unit','move_id.months')
    def _onchange_price_unit(self):
        print('price change happened')
        for line in self:
            move = line.move_id
            if move.tenancy_id:
                rent_invoices = self.env['account.move'].search([
                    ('nhcl_invoice_type', '=', 'rent'),
                    ('tenancy_id', '=', move.tenancy_id.id),
                    ('state', '!=', 'cancel'),
                ])
                print("Found Rent Invoices:", rent_invoices.mapped('name'))

                for rent_invoice in rent_invoices:
                    # if move.nhcl_invoice_type == 'rent':
                    #     print("self.months",move.months)
                    #     print("rent_invoice",rent_invoice.months)
                    #     move.months = rent_invoice.months

                    if move.nhcl_invoice_type == 'rs':
                        print("99999999999999999999999999999999")
                        rent_invoice.rs_amount = line.price_unit
                        print( rent_invoice.months,rent_invoice.name)
                        move.months = rent_invoice.months
                        print("rent_invoice.rs_amount ", rent_invoice.rs_amount)
                    elif move.nhcl_invoice_type == 'mg':
                        rent_invoice.mg_amount = line.price_unit
                    elif move.nhcl_invoice_type == 'slb':
                        rent_invoice.slab_amount = line.price_unit

    @api.onchange('net_slab')
    def _onchange_net_slab(self):
        if not self.net_slab or not self.move_id.partner_id:
            return

        partner = self.move_id.partner_id

        # Get slab.master for the partner
        slab = self.env['slab.master'].search([('customer_id', '=', partner.id)], limit=1)
        if not slab:
            self.percentage_slab = 0.0
            raise ValidationError("No slab master defined for this customer.")

        # Find the matching slab line
        matching_line = slab.slab_line_ids.filtered(
            lambda line: line.from_slab <= self.net_slab <= line.to_slab
        )

        if matching_line:
            self.percentage_slab = matching_line[0].percentage
        else:
            self.percentage_slab = 0.0
            raise ValidationError("Net Slab does not fall under any defined slab range.")






