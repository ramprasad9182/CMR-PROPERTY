/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { TextInputPopup } from "../custom_popup/text_input_popup";
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";

patch(ControlButtons.prototype, {

     setup() {
        super.setup();
        // add state to ControlButtons
        this.state = useState({
            selectedCard: null,
        });
    },
    async onClickPopupSingleField() {
        console.log(">>> Button Clicked, fetching cards...");

        // Fetch cards directly from server when button is clicked
        const cards = await this.env.services.orm.searchRead(
            "food.court.cards",
            [["issue", "=", true]],   // no domain = fetch all cards
            ["id", "card_number", "mobile", "balance"]  // fields to fetch
        );

        console.log(">> > Cards Fetched:", cards);

        if (!cards || !cards.length) {
            this.dialog.add(TextInputPopup, {
                title: _t("No Cards Found"),
                cards: [],
                getPayload: () => {},
            });
            return;
        }

        const selectedCard = await new Promise((resolve) => {
            this.dialog.add(TextInputPopup, {
                title: _t("Select Customer Card"),
                cards: cards,   // directly fetched
                getPayload: (card) => resolve(card),
            });
        });

//        if (selectedCard) {
//            console.log(">>> Selected Card:", selectedCard);
//            // attach to order/customer here
//             const order = this.pos.get_order();
//             console.log('order details',order)
//             console.log("???",selectedCard.card_number,"//////")
//            order.selectedCard = selectedCard;
//        }
            if (selectedCard) {
                console.log(">>> Selected Card:", selectedCard);

                const order = this.pos.get_order();
                console.log('order details', order);
                console.log("???", selectedCard.card_number, "//////");

                // store in order
                order.selectedCard = selectedCard;

                // store in button state so template can display
                this.state.selectedCard = selectedCard.card_number;  // or selectedCard if you want full object
            }

    },
});
