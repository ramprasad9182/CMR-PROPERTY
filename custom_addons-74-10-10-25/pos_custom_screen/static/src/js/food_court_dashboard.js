/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class FoodCourtDashboard extends Component {
    setup() {
        this.actionService = this.env.services.action;
        this.orm = useService("orm");
        this.state = useState({ userName: "" });

        // ✅ hook must be inside setup
        onWillStart(async () => {
            const result = await this.orm.call(
                "food.court.cards",         // model
                "get_current_user_name",    // method
                []                          // args
            );
            console.log("User from Python:", result);
            this.state.userName = result;  // if Python returns string
        });
    }

    async openAction(actionXmlId) {
        await this.actionService.doAction(actionXmlId);
    }
}

FoodCourtDashboard.template = "pos_custom_screen.FoodCourtDashboards";

registry.category("actions").add("food_court_dashboard", FoodCourtDashboard);
