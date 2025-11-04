/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class TextInputPopup extends Component {
    static template = "pos_custom_screen.TextInputPopup";
    static components = { Dialog };
    static props = { title: String, cards: Array, getPayload: Function, close: Function };

    setup() {
        this.state = useState({
            selectedCard: null,
        });
    }

    selectCard(card) {
    console.log('jjjjj',card)
        this.state.selectedCard = card;
    }

    confirm() {
        this.props.getPayload(this.state.selectedCard);
        this.props.close();
    }

    close() {
        this.props.close();
    }
}
