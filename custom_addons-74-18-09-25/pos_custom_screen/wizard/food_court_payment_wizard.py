from odoo import models, fields

class FoodCourtPaymentWizard(models.TransientModel):
    _name = "food.court.payment.wizard"
    _description = "Food Court Payment Wizard"

    amount = fields.Float("Amount", required=True)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
        ('voucher', 'Voucher')
    ], string="Payment Method", required=True)

    def action_confirm(self):
        card = self.env["food.court.card"].browse(self.env.context.get("active_id"))
        transaction_type = self.env.context.get("transaction_type", "issue")

        self.env["food.court.transaction"].create({
            "card_id": card.id,
            "transaction_type": transaction_type,
            "amount": self.amount,
            "payment_method": self.payment_method,
        })

        if transaction_type in ["issue", "recharge"]:
            print(self.amount)
            print(card.balance,card.card_deposit)
            card.balance += self.amount
            card.card_deposit += self.amount

        elif transaction_type == "return":
            card.balance = 0
            card.active = False

        return {"type": "ir.actions.act_window_close"}
