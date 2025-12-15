"""@api.model
def send_email_to_tenancy(self):
    # Get the email template
    template = self.env.ref('nhcl_rental_management.renewal_notification_email_template')
    print(template)
    for record in self:
        if datetime.datetime.today() == self.renewal_date:
            template.send_mail(record.id, force_send=True)
            """


"""
    @api.model
    def send_email_to_tenancy(self):
        # Get the email template
        template = self.env.ref('nhcl_rental_management.renewal_notification_email_template')
        emails_sent = 0

        for record in self.env['tenancy.details'].search([]):
            if fields.Date.today() == record.renewal_date:
                template.send_mail(record.id, force_send=True)
                emails_sent += 1

        # Post a message to the custom channel
        custom_channel = self.env.ref('nhcl_rental_management.custom_notification_channel')
        if custom_channel:
            custom_channel.message_post(
                body=f'{emails_sent} renewal notification email(s) sent successfully.'
                if emails_sent > 0
                else 'No tenancies were due for renewal today.',
                subtype_xmlid='mail.mt_note'
            )
        for record in self.env['tenancy.details'].search([]):
            if fields.Date.today() == record.renewal_date:
                template.send_mail(record.id, force_send=True)
                print("send message sucess fully")
                return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Email Sent!',
                            'message': 'The email has been sent successfully.',
                            'type': 'success',  # 'success', 'warning', 'danger', 'info'
                            'sticky': False,  # Notification auto-closes
                        },
                    }
                    
                    
 @api.onchange('renewal_type','ndays')
    def change_the_value_add(self):
        # if not self.start_date or not self.duration_id or not self.ndays:
        #     return  # Ensure start_date and duration are available
        # years=self.ndays# here i am getting the year
        # self.year_ids = [(5, 0, 0)]
        # print(years,'calling the ........')# Clear existing records in year_ids

        if self.renewal_type == 'year':
            print("Onchange triggered for Renewal Type: Year")
            if not self.start_date or not self.duration_id or not self.ndays:
                    return  # Ensure start_date and duration are available
            years = self.ndays  # here i am getting the year
            self.year_ids = [(5, 0, 0)]

            # Calculate the number of periods based on the duration
            num_periods = (self.duration_id.month // 12) // years  # Assuming 'duration' holds the number of years
            print(num_periods)
            if int(num_periods) <= 0:
                return  # Prevent invalid periods

            base_date = self.start_date  # Start from the given start_date
            new_records = []

            for i in range(int(num_periods)):
                if i == 0:
                    start_year = base_date 
                    end_year = start_year + relativedelta(years=self.ndays,days=-60)  # Calculate the end of the year
                    print(start_year, ".....", end_year, "inside if condition")

                    new_records.append((0, 0, {
                        'start_year': start_year,
                        'end_year': end_year,
                    }))
                else:
                    start_year = start_year + relativedelta(years=1 * self.ndays)
                    end_year = start_year + relativedelta(years=self.ndays,days=-60)
                    print(start_year, ".....", end_year, "inside else condition")

                    new_records.append((0, 0, {
                        'start_year': start_year,
                        'end_year': end_year,
                    }))

            # Assign the list of records to the One2many field
            self.year_ids = new_records """

"""
def create(self, vals):
# Fetch the nhcl_invoice_type from the vals
invoice_type = vals.get('nhcl_invoice_type')
print(invoice_type)
if invoice_type in ['rent', 'cam']:  # Only handle 'rent' and 'cam' cases
vals['name'] = self._generate_invoice_number(invoice_type)
else:
print('default behaviour')
return super(AccountMove, self).create(vals)
# Default behavior for regular invoices
print('outside func')
return super(AccountMove, self).create(vals)
    """