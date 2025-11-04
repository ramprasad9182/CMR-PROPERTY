from odoo import models, fields, api
from odoo.exceptions import ValidationError

class FoodCourtCard(models.Model):
    _name = "food.court.cards"
    _description = "Food Court Card"
    _rec_name = 'card_number'
    _sql_constraints = [
        ('card_number_uniq', 'unique(card_number)', 'Card number must be unique.')
    ]

    card_number = fields.Char("Card Number", required=True, copy=False, index=True)
    customer_name = fields.Char("Customer Name")   # manual char field
    mobile = fields.Char("Mobile Number")
    issue_date = fields.Datetime("Issue Date")

    card_amount = fields.Float("Card Amount", default=0.0)
    card_deposit = fields.Float("Card Deposit", default=0.0)
    deposit_used = fields.Float("Deposit", default=0.0)
    used=fields.Float(String='Used')
    balance = fields.Float("Balance", default=0.0)
    redeemable_balance = fields.Float("Redeemable Balance", default=0.0)

    issue = fields.Boolean("Issued", default=False)
    inactive = fields.Boolean("Inactive", default=False)

    @api.constrains('mobile')
    def _check_mobile(self):
        for rec in self:
            if rec.mobile:
                if not rec.mobile.isdigit():
                    raise ValidationError("Mobile number must contain only digits.")
                if len(rec.mobile) != 10:
                    raise ValidationError("Mobile number must be 10 digits long.")

    def action_recharge(self):
        for rec in self:
            amount = self.env.context.get("amount", 0)  # get amount from context
            if amount > 0:
                rec.card_amount = amount  # add recharge to card balance
    def action_clear_balance(self):
        for rec in self:
            if not rec.issue:
                rec.card_amount=0
                rec.balance=0
                rec.card_deposit=0
                rec.redeemable_balance=0
                rec.deposit_used=0
            else:
                raise ValidationError("Can't Clear It's already Issued")

    def action_issue_card(self):
        """Mark card as issued and set issue date, store transaction"""
        for card in self:
            if card.issue:
                raise ValidationError("This card is already issued!")
            print( not card.card_amount)
            if  not card.card_amount:
                raise ValidationError("Can't Procssed with empty value!")


            # Update the card
            card.write({
                'issue': True,
                'issue_date': fields.Datetime.now(),
                'balance': card.card_amount-card.card_deposit,
                'redeemable_balance': card.card_amount-card.card_deposit,
            })

            # Record transaction
            self.env['food.court.transactions'].create({
                'card_id': card.id,
                'transaction_type': 'issue',
                'amount': card.card_amount,
                'balance_after': card.balance,
                'deposit_used_after': card.deposit_used,
                'reason': 'Card Issued',
                'payment_method': 'cash',  # optional
                'receipt_number': '',  # optional
            })
            # existing_partner = self.env['res.partner'].search([('name', '=', self.customer_name)], limit=1)
            #
            # if not existing_partner:
            #     self.env['res.partner'].create({
            #         'name': self.customer_name,
            #         'mobile': self.mobile,
            #         'partner_type': 'customer',
            #         'user_type': 'customer',
            #     })

        return {
            'effect': {
                'fadeout': 'slow',
                'message': "Card issued successfully!",
                'type': 'rainbow_man',
            }
        }

    @api.onchange("card_amount")
    def default_deposit_(self):
        for rec in self:
            if rec.card_amount:
                rec.card_deposit = 20
                rec.deposit_used = 20

    @api.model
    def create(self, vals):
        if 'card_deposit' not in vals:
            vals['card_deposit'] = 20.0
        if 'deposit_used' not in vals:
            vals['deposit_used'] = vals.get('card_deposit', 20.0)
        return super().create(vals)

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if 'card_amount' in vals and rec.card_amount:
                rec.card_deposit = 20
                rec.deposit_used = 20
        return res


    @api.model
    def get_current_user_name(self):
        return self.env.user.name


class FoodCourtRecharge(models.Model):
    _name = "food.court.recharge"
    _description = "Card Recharge Records"
    _rec_name = 'card_id'

    card_id = fields.Many2one('food.court.cards', string='Card', required=True)
    card_number = fields.Char('Card Number', related='card_id.card_number', store=True)
    customer_name = fields.Char('Customer Name', related='card_id.customer_name', store=True)
    mobile = fields.Char("Mobile Number",related='card_id.mobile')
    issue_date = fields.Datetime("Issue Date",related='card_id.issue_date')
    card_amount = fields.Float("Card Amount", related='card_id.card_amount')
    card_deposit = fields.Float("Card Deposit", related='card_id.card_deposit')
    balance = fields.Float("Balance", related='card_id.balance')
    issue = fields.Boolean("Issued", related='card_id.issue')
    inactive = fields.Boolean("Inactive", related='card_id.inactive')
    deposit_used = fields.Float("Deposit", related='card_id.deposit_used')
    used = fields.Float(String='Used')
    redeemable_balance = fields.Float("Redeemable Balance", related='card_id.redeemable_balance')

    amount = fields.Float('Recharge Amount', required=True)
    reason = fields.Text('Recharge Reason')
    recharge_on = fields.Datetime('Recharge Date', default=fields.Datetime.now)
    payment_method = fields.Selection([
        ('cash', 'Cash'), ('card', 'Card'), ('upi', 'UPI'), #('voucher', 'Voucher')
    ])
    receipt_number = fields.Char('Receipt No.')

    # @api.model
    # def create(self, vals):
    #     record = super(FoodCourtRecharge, self).create(vals)
    #     card = record.card_id
    #     card.balance += record.amount
    #     card.redeemable_balance += record.amount
    #     return record

    def action_recharge_card(self):
        """Recharge card and update both card table and transaction history"""
        for record in self:
            card = record.card_id

            if not card.issue:
                raise ValidationError("Card is not issued yet!")

            if record.amount <= 0:
                raise ValidationError("Please enter a valid recharge amount.")

            # 1️⃣ Update the main card table
            card.balance += record.amount
            card.redeemable_balance += record.amount
            # Optionally, you can also update deposit_used or redeemable_balance if needed
            # card.deposit_used += some_value
            # card.redeemable_balance += some_value

            # 2️⃣ Record transaction history
            self.env['food.court.transactions'].create({
                'card_id': card.id,
                'transaction_type': 'recharge',
                'amount': record.amount,
                'balance_after': card.balance,
                'deposit_used_after': card.deposit_used,
                'reason': record.reason,
                'payment_method': record.payment_method,
                'receipt_number': record.receipt_number,
                'date': record.recharge_on,
            })

        return {
            'effect': {
                'fadeout': 'slow',
                'message': f"Card {card.card_number} recharged successfully!",
                'type': 'rainbow_man',
            }
        }

    def action_recharge(self):
        for rec in self:
            amount = self.env.context.get("amount", 0)  # get amount from context
            if amount > 0:
                rec.amount = amount  # add recharge to card balance

    def action_clear_balance(self):
        for rec in self:
            # if not rec.issue:
                rec.amount = 0
                # rec.balance = 0
                # rec.card_deposit = 0
                # rec.redeemable_balance = 0
                # rec.deposit_used = 0
            # else:
            #     raise ValidationError("Can't Clear It's already Issued")




class FoodCourtReturn(models.Model):
    _name = "food.court.return"
    _description = "Card Return Records"
    _rec_name = 'card_id'

    card_id = fields.Many2one('food.court.cards', string='Card', required=True)
    card_number = fields.Char('Card Number', related='card_id.card_number', store=True)
    customer_name = fields.Char('Customer Name', related='card_id.customer_name', store=True)

    reason = fields.Text('Return Reason')
    return_on = fields.Datetime('Return Date', default=fields.Datetime.now)
    refund_amount = fields.Float('Refund Amount')
    payment_method = fields.Selection([
        ('cash', 'Cash'), ('card', 'Card'), ('upi', 'UPI'), #('voucher', 'Voucher')
    ])
    receipt_number = fields.Char('Receipt No.')

    mobile = fields.Char("Mobile Number", related='card_id.mobile')
    issue_date = fields.Datetime("Issue Date", related='card_id.issue_date')
    card_amount = fields.Float("Card Amount", related='card_id.card_amount')
    card_deposit = fields.Float("Card Deposit", related='card_id.card_deposit')
    balance = fields.Float("Balance", related='card_id.balance')
    issue = fields.Boolean("Issued", related='card_id.issue')
    inactive = fields.Boolean("Inactive", related='card_id.inactive')
    deposit_used = fields.Float("Deposit", related='card_id.deposit_used')
    used = fields.Float(String='Used')
    redeemable_balance = fields.Float("Redeemable Balance", related='card_id.redeemable_balance')

    # @api.model
    # def create(self, vals):
    #     record = super(FoodCourtReturn, self).create(vals)
    #     card = record.card_id
    #     # Refund logic: clear balance & deposit
    #     record.refund_amount = vals.get('refund_amount') or (card.balance + card.card_deposit)
    #     card.balance = 0.0
    #     card.deposit_used = 0.0
    #     card.card_deposit = 0.0
    #     card.issue = False
    #     card.inactive = True
    #     return record
    def action_return_card(self):
        for record in self:
            card = record.card_id
            if not card:
                raise ValidationError("No card selected for return.")

            # Calculate refund
            refund = record.refund_amount or (card.balance + card.card_deposit)
            # record.refund_amount = refund
            card.redeemable_balance = record.redeemable_balance-record.refund_amount
            card.balance = record.balance-record.refund_amount

            # 🔹 Update card details (make inactive)
            card.write({
                # 'balance': 0.0,
                # 'deposit_used': 0.0,
                # 'card_deposit': 0.0,
                'issue': False,
                'inactive': True,  # ✅ mark as inactive in food.court.cards
            })

            # 🔹 Log transaction
            self.env['food.court.transactions'].create({
                'card_id': card.id,
                'transaction_type': 'return',
                'amount': refund,
                'balance_after': card.balance,
                'deposit_used_after': card.deposit_used,
                'reason': record.reason,
                'payment_method': record.payment_method,
                'receipt_number': record.receipt_number,
            })

        return True

    def action_recharge(self):
        for rec in self:
            amount = self.env.context.get("amount", 0)  # get amount from context
            if amount > 0:
                rec.refund_amount = amount  # add recharge to card balance

    def action_clear_balance(self):
        for rec in self:
            # if not rec.issue:
            rec.refund_amount = 0
            # rec.balance = 0
            # rec.card_deposit = 0
            # rec.redeemable_balance = 0
            # rec.deposit_used = 0
        # else:
        #     raise ValidationError("Can't Clear It's already Issued")


