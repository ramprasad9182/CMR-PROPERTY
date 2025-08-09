from odoo import fields, api, models, _
from odoo.exceptions import UserError,ValidationError
import pytz
from datetime import datetime
import re


class ResPartner(models.Model):
    _inherit = 'res.partner'

    tenant_type = fields.Many2one('tenant.type', string="Tenancy Type")
    adhar_no = fields.Char(string='Aadhar No')
    director_name = fields.Char(string='Director Name')
    din_no = fields.Char(string='Din No')
    nhcl_pan_no = fields.Char(string='Pan No')
    nhcl_res_cin_no = fields.Char(string='Cin No')

    cam = fields.Char(string='Cam Email')
    utility = fields.Char(string='Utility Email')
    gas = fields.Char(string='Gas Email')

    @api.constrains('cam', 'utility', 'gas','email')
    def _check_emails_format(self):
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        for rec in self:
            for field_name in ['cam', 'utility', 'gas','email']:
                email_value = getattr(rec, field_name)
                if email_value and not re.match(email_pattern, email_value):
                    raise ValidationError(
                        f"Invalid email format in '{field_name.replace('_', ' ').capitalize()}': {email_value}")

    @api.constrains('adhar_no', 'phone','mobile')
    def _check_adhar_phone(self):
        for rec in self:
            if  rec.adhar_no and not rec.adhar_no.isdigit():
                raise ValidationError('Aadhar number must be Number.')
            if (rec.adhar_no) and (len(rec.adhar_no) != 12):
                raise ValidationError("Aadhar Number must be exactly 12 digits.")
            if rec.phone and not rec.phone.isdigit():
                raise ValidationError('Phone number must be Number.')
            if rec.phone and (not rec.phone.isdigit() or len(rec.phone) != 10):
                raise ValidationError("Phone number must be exactly 10 digits.")
            if rec.mobile and not rec.mobile.isdigit():
                raise ValidationError('mobile number must be Number.')
            if rec.mobile and (not rec.mobile.isdigit() or len(rec.mobile) != 10):
                raise ValidationError("mobile number must be exactly 10 digits.")


class Comapny(models.Model):
    _inherit = 'res.company'

    nhcl_com_cin_no = fields.Char(string='Cin No')
    nhcl_com__director_name = fields.Char(string='Director Name')
    nhcl_com_din_no = fields.Char(string='Din No')
    nhcl_com_adhar_no = fields.Char(string='Aadhar No')

    @api.constrains('nhcl_com_adhar_no')
    def _check_adhar_phone(self):
        for rec in self:
            if rec.nhcl_com_adhar_no and not rec.nhcl_com_adhar_no.isdigit():
                raise ValidationError('Aadhar number must be a Number.')
            if (rec.nhcl_com_adhar_no) and (len(rec.nhcl_com_adhar_no) != 12):
                raise ValidationError("Aadhar Number must be exactly 12 digits.")


class AccountGroup(models.Model):
    _inherit = 'account.group'

    nhcl_parent_id = fields.Many2one('account.group', string="Parent Group")


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    def _get_prefix_suffix(self, date=None, date_range=None):
        def _interpolate(s, d):
            return (s % d) if s else ''

        def _interpolation_dict():
            now = range_date = effective_date = datetime.now(pytz.timezone(self._context.get('tz') or 'UTC'))
            if date or self._context.get('ir_sequence_date'):
                effective_date = fields.Datetime.from_string(date or self._context.get('ir_sequence_date'))
            if date_range or self._context.get('ir_sequence_date_range'):
                range_date = fields.Datetime.from_string(date_range or self._context.get('ir_sequence_date_range'))

            sequences = {
                'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
                'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S'
            }
            res = {}
            for key, fmt in sequences.items():
                res[key] = effective_date.strftime(fmt)
                res['range_' + key] = range_date.strftime(fmt)
                res['current_' + key] = now.strftime(fmt)

            # ➕ Inject fiscal year code (fy) from context or compute here
            fy = self._context.get('fy')
            if not fy:
                month = int(res['month'])
                year = int(res['year'])
                fy_start = year - 1 if month < 4 else year
                fy = f"{str(fy_start)[-2:]}{str(fy_start + 1)[-2:]}"  # '2526'
            res['fy'] = fy

            return res

        self.ensure_one()
        d = _interpolation_dict()

        try:
            interpolated_prefix = _interpolate(self.prefix, d)
            interpolated_suffix = _interpolate(self.suffix, d)
        except (ValueError, TypeError, KeyError) as e:
            raise UserError(_('Invalid prefix/suffix in sequence “%s”: %s') % (self.name, e))

        return interpolated_prefix, interpolated_suffix
