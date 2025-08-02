from odoo import api,models,fields
from odoo.exceptions import ValidationError


class Mall(models.Model):
    _name='mall.main'

    name = fields.Char(string='Name', required=True, copy=False)


class MallDemo(models.Model):
    _name ='mall.demo'

    mall_id = fields.Many2one('property.details')
    mall_master_id = fields.Many2one('mall.main',string="Retail Mix")
    mall_length=fields.Integer(string='Length(ft)')
    mall_width=fields.Integer(string='Width(ft)')
    mall_height=fields.Integer(string='Height(ft)')
    mall_no_of_unit =fields.Integer(string='Floor')
    mall_carpet_area=fields.Integer(string='Area(ft²)')


class TenantType(models.Model):
    _name = 'tenant.type'
    _description = 'Tenant Type'

    name = fields.Char(string='Name', required=True, copy=False)


class PreventingMaintenance(models.Model):
    _name = 'preventing.maintenance'
    _description = 'Preventing Maintenance'

    nhcl_start_date = fields.Date(string='Start Date')
    nhcl_schedule_date = fields.Date(string='Schedule Date')
    nhcl_end_date = fields.Date(string='End Date')
    nhcl_description = fields.Text(string='Description')
    nhcl_status = fields.Text(string='Status')
    nhcl_remarks = fields.Text(string='Remarks')
    maintenance_request_id = fields.Many2one(
        'maintenance.request', string='Maintenance Request'
    )

class SupportDocuments(models.Model):
    _name='support.documents'

    responsible=fields.Many2one('hr.employee')
    nhcl_description=fields.Char(string='Description')
    start_date=fields.Date(string='Start Date')
    attachments=fields.Binary(string='Attachments')
    attachment_name = fields.Char(string='File Name')
    support_id = fields.Many2one('tenancy.details')

    @api.constrains('attachments')
    def _check_mandatory_fields(self):
        for record in self:
            if record.attachments:
                if not record.nhcl_description:
                    raise ValidationError("Description must be provided when attachments are added.")
                if not record.start_date:
                    raise ValidationError("Start Date must be provided when attachments are added.")

    # @api.onchange('attachments')
    # def _onchange_attachments(self):
    #     if self.attachments:
    #         # Extract the filename from the binary data
    #         self.attachment_name = self._get_attachment_filename()
    #
    # def _get_attachment_filename(self):
    #     # Logic to extract the filename, if necessary
    #     # For example, assuming the file is uploaded with the filename:
    #     return "your_file_name.ext"


class YearAddInTenancy(models.Model):
    _name='year_add'

    start_year=fields.Date(string='Start Date')
    end_year=fields.Date(string='Renewal Date')
    yid=fields.Many2one('tenancy.details')