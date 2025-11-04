from odoo import models, fields

class FoodCourtTransaction(models.Model):
    _name = "food.court.transactions"
    _description = "Food Court Card Transaction History"
    _order = "date desc"

    card_id = fields.Many2one('food.court.cards', string='Card', required=True)
    card_number = fields.Char('Card Number', related='card_id.card_number', store=True)
    customer_name = fields.Char('Customer Name', related='card_id.customer_name', store=True)

    transaction_type = fields.Selection([
        ('issue', 'Issue'),
        ('recharge', 'Recharge'),
        ('return', 'Return'),
    ], required=True)

    amount = fields.Float('Amount')                     # Deposit, Recharge, or Refund
    balance_after = fields.Float('Balance After Action')
    deposit_used_after = fields.Float('Deposit Used After Action')

    reason = fields.Text('Reason')                     # Optional reason for recharge/return
    payment_method = fields.Selection([
        ('cash', 'Cash'), ('card', 'Card'), ('upi', 'UPI'), ('voucher', 'Voucher')
    ])
    receipt_number = fields.Char('Receipt No.')
    date = fields.Datetime('Date', default=fields.Datetime.now)

