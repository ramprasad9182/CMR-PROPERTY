from odoo import api, models, fields
from odoo.exceptions import ValidationError, UserError


class Mall(models.Model):
    _name = 'mall.main'

    name = fields.Char(string='Name', required=True, copy=False)


class MallDemo(models.Model):
    _name = 'mall.demo'

    mall_id = fields.Many2one('property.details')
    mall_master_id = fields.Many2one('mall.main', string="Retail Mix")
    mall_length = fields.Integer(string='Length(ft)')
    mall_width = fields.Integer(string='Width(ft)')
    mall_height = fields.Integer(string='Height(ft)')
    mall_no_of_unit = fields.Char(string='Floor')
    mall_carpet_area = fields.Integer(string='Area(ft²)')


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
    _name = 'support.documents'

    responsible = fields.Many2one('hr.employee')
    nhcl_description = fields.Char(string='Description')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='Expiry Date')
    attachments = fields.Binary(string='Attachments', attachment_name='attachment_name')
    attachment_name = fields.Char(string='File Name')
    amount = fields.Float(string='Amount',digits=(16, 2))
    support_id = fields.Many2one('tenancy.details')

    @api.constrains('attachments')
    def _check_mandatory_fields(self):
        for record in self:
            if record.attachments:
                if not record.nhcl_description:
                    raise ValidationError("Description must be provided when attachments are added.")
                if not record.start_date:
                    raise ValidationError("Start Date must be provided when attachments are added.")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    cam = fields.Char(string='Cam Email')
    utility = fields.Char(string='Utility Email')
    gas = fields.Char(string='Gas Email')


class YearAddInTenancy(models.Model):
    _name = 'year.add'

    start_year = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    end_year = fields.Date(string='Renewal Date')
    yid = fields.Many2one('tenancy.details')
    percentage = fields.Integer(string='Percentage')
    amount = fields.Float(string='Amount', compute='_amount_change', store=True)
    is_invoice_generated = fields.Boolean(string="Invoice Created", default=False)
    is_first_line = fields.Boolean("Is First Line", compute="_compute_is_first_line", store=True)

    @api.depends('yid')
    def _compute_is_first_line(self):
        for record in self:
            record.is_first_line = False  # default
            if record.yid:
                first_line = self.env['year.add'].search(
                    [('yid', '=', record.yid.id)],
                    order='id',
                    limit=1
                )
                record.is_first_line = (record.id == first_line.id)

    @api.depends('percentage', 'yid')
    def _amount_change(self):
        tenancies = self.mapped('yid')

        for tenancy in tenancies:
            related_lines = self.env['year.add'].search(
                [('yid', '=', tenancy.id)],
                order='id'
            )

            for i, line in enumerate(related_lines):
                if i == 0:
                    # First line: total rent only
                    line.amount = tenancy.total_rent
                else:
                    prev_line = related_lines[i - 1]
                    base = prev_line.amount
                    percentage = line.percentage
                    line.amount = base + (base * percentage / 100)


class YearAddInTenancy_cam(models.Model):
    _name = 'cam.year'

    cam_start_year = fields.Date(string='Start Date')
    cam_end_year = fields.Date(string='Renewal Date')
    cam_end_date = fields.Date(string='End Date')
    cam_yid = fields.Many2one('tenancy.details')
    is_invoice_generated = fields.Boolean(string="Invoice Created", default=False)
    cam_percentage = fields.Integer(string='Percentage')
    cam_amount = fields.Float(string='Amount', compute='cam_amount_chnage')
    is_first_line_cam = fields.Boolean("Is First Line", compute="_compute_is_first_line", store=True, default=False)

    @api.depends('cam_yid')
    def _compute_is_first_line(self):
        for record in self:
            record.is_first_line_cam = False  # default
            if record.cam_yid:
                first_line = self.env['cam.year'].search(
                    [('cam_yid', '=', record.cam_yid.id)],
                    order='id',
                    limit=1
                )
                record.is_first_line_cam = (record.id == first_line.id)

    # @api.onchange('cam_percentage')
    # def cam_amount_chnage(self):
    #     related_lines = self.env['cam.year'].search([('cam_yid.tenancy_seq', '=', self.cam_yid.tenancy_seq)],
    #                                                 order='id')
    #     for rec in self:
    #         if rec.cam_percentage and related_lines:
    #             rec.cam_amount = 0
    #             c = 0
    #             if related_lines:
    #                 for record in self:
    #                     tenancy = record.cam_yid
    #                     print(tenancy.tenancy_id.name, record.cam_percentage, record.id, record.cam_amount)
    #                     if record.cam_percentage and tenancy:
    #                         print('satisfied')
    #                         if tenancy.use_carpet:
    #                             if c == 0:
    #                                 record.cam_amount = tenancy.cam_carpet
    #                                 print('updated')
    #                             else:
    #                                 record.cam_amount = related_lines.cam_yid.cam_year_ids[c - 1].cam_amount + (
    #                                         related_lines.cam_yid.cam_year_ids[
    #                                             c - 1].cam_amount * record.cam_percentage / 100)
    #                         else:
    #                             if c == 0:
    #                                 record.cam_amount = tenancy.cam_chargeable
    #                             else:
    #                                 record.cam_amount = related_lines.cam_yid.cam_year_ids[c - 1].cam_amount + (
    #                                         related_lines.cam_yid.cam_year_ids[
    #                                             c - 1].cam_amount * record.cam_percentage / 100)
    #                     else:
    #                         record.cam_amount = 0
    #                     c += 1
    #         else:
    #             rec.cam_amount = 0
    @api.depends('cam_percentage', 'cam_yid.cam_year_ids.cam_percentage')
    def cam_amount_chnage(self):
        for rec in self:
            if not rec.cam_yid:
                # rec.cam_amount = 0
                continue

            # Get all related CAM year lines of the same tenancy
            related_lines = self.env['cam.year'].search([('cam_yid', '=', rec.cam_yid.id)], order='id')

            amount = 0
            for i, line in enumerate(related_lines):
                if line.id == rec.id:
                    # Found the current line in the loop
                    print(line.cam_yid.cam_type)
                    if line.cam_yid.cam_type == 'cam_sft':
                        if i == 0:
                            if rec.cam_yid.use_carpet:
                                amount = rec.cam_yid.cam_carpet
                            else:
                                amount = rec.cam_yid.cam_chargeable
                        else:
                            prev_line = related_lines[i - 1]
                            base = prev_line.cam_amount
                            percentage = rec.cam_percentage
                            amount = base + (base * percentage / 100)
                        break  # stop once you calculate the current line
                    else:
                        print('lum_sum')
                        if i == 0:
                            amount = rec.cam_yid.cam_fixed
                        else:
                            prev_line = related_lines[i - 1]
                            base = prev_line.cam_amount
                            percentage = rec.cam_percentage
                            amount = base + (base * percentage / 100)
                        break  # stop

            rec.cam_amount = amount


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    class MaintenanceRequest(models.Model):
        _inherit = 'maintenance.request'

        def change_button_next(self):
            for rec in self:
                current_stage = rec.stage_id.name.lower()
                next_stage_name = None

                if current_stage == 'new request':
                    next_stage_name = 'In Progress'
                elif current_stage == 'in progress':
                    next_stage_name = 'Repaired'
                elif current_stage == 'repaired':
                    next_stage_name = 'Scrap'

                if next_stage_name:
                    next_stage = self.env['maintenance.stage'].search(
                        [('name', '=', next_stage_name)],
                        limit=1
                    )
                    if next_stage:
                        rec.stage_id = next_stage

        def change_button_back(self):
            for rec in self:
                current_stage = rec.stage_id.name.lower()

                # BLOCK condition: Prevent going back if in 'Repaired' and corrective
                if current_stage == 'repaired' and rec.maintenance_type == 'corrective':
                    raise UserError(
                        "You cannot change the stage of a corrective maintenance request once it's in 'Repaired'.")

                previous_stage_name = None

                if current_stage == 'repaired':
                    previous_stage_name = 'In Progress'
                elif current_stage == 'in progress':
                    previous_stage_name = 'New Request'

                if previous_stage_name:
                    previous_stage = self.env['maintenance.stage'].search([
                        ('name', '=', previous_stage_name)
                    ], limit=1)

                    if previous_stage:
                        rec.stage_id = previous_stage


class RelationYear(models.Model):
    _name = 'tenancy.relation.year'

    name=fields.Char(string='Name')
