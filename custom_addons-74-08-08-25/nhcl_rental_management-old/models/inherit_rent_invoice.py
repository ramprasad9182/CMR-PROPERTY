from datetime import datetime

from odoo import api,fields,models

class RentInvoice(models.Model):
    _inherit = 'rent.invoice'

    rent_depo_date = fields.Date(string='Caution Deposit Money Handover Date')


class DateRangeWizard(models.TransientModel):
    _name = 'date.range.wizard'
    _description = 'Date Range Wizard'

    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="To Date", required=True)

    def action_print_report_rent(self):
        """Fetch records from rent.invoice and pass to the report"""
        invoices = self.env['rent.invoice'].search([
            ('invoice_date', '>=', self.from_date),
            ('invoice_date', '<=', self.to_date),
        ])
        #print(invoices)
        res=[]

        for data in invoices:

            # tax=(data.amount-data.tenancy_id.total_rent)
            # print(data.amount,"-",data.tenancy_id.total_rent,"-",tax)
            # tax2=tax % data.tenancy_id.total_rent
            # print(tax,"%",data.tenancy_id.total_rent,".....")
            tax=data.rent_invoice_id.invoice_line_ids[0].product_id.taxes_id[0].name
            tax_amount=data.rent_invoice_id.invoice_line_ids[0].price_total - data.rent_invoice_id.invoice_line_ids[0].price_subtotal
            #print(tax_amount,"tax_amount.....")
            total_tax_amount=data.rent_invoice_id.invoice_line_ids[0].price_total
            status=data.tenancy_id.contract_type


            res+=[{data.id:'id','invoice':data.rent_invoice_id.name,'brand':data.customer_id.name,'Brand':data.tenancy_id.brand_name,'amount':data.amount,'tax':tax,'tax_amount':tax_amount,'total_tax_amount':total_tax_amount,'status':status}]
            #print(res)

            # print(data.tenancy_id.brand_name)
            # print(data.id)
        # record=self.env['rent.invoice'].browse(invoices)
        # for rec in record:
        #     print(rec.customer_id.name)
        from_date=self.from_date
        to_date=self.to_date
        #print(from_date)
        month_name = datetime.strptime(str(from_date), "%Y-%m-%d").strftime("%B")
        # print(from_date,)
        # print('calling the function',invoices)
        #
        # data = {
        #     'from_date': self.from_date,
        #     'to_date': self.to_date,
        #     'invoice_ids': invoices,  # Passing IDs for the report
        # }

        return self.env.ref('nhcl_rental_management.action_report_rent_invoice').report_action(self,{"from_date":from_date,'to_date':to_date,'res':res,'month_name':month_name})
