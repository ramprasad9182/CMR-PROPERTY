/** @odoo-module */
import { registry } from "@web/core/registry";
import { loadJS } from "@web/core/assets";
import { ChartRenderer } from "./chart_renderer/chart_renderer";
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, useRef, onMounted, useState } = owl;

export class OwlRentalDashboard extends Component {

    async getPropertyType() {
        const data = await this.orm.readGroup("property.details", [], ['type', 'name'], ['type']);
        this.state.propertyType = {
            data: {
                labels: data.map(d => d.type),
                datasets: [
                    {
                        label: '',
                        data: data.map(d => d.type_count || 0), // Default to 0 if undefined
                        hoverOffset: 10
                    }
                ]
            }
        };
    }

    async getPropertyStage() {
        const data = await this.orm.readGroup("property.details", [], ['stage', 'name'], ['stage']);
        this.state.propertyStage = {
            data: {
                labels: data.map(d => d.stage),
                datasets: [
                    {
                        label: '',
                        data: data.map(d => d.stage_count || 0), // Default to 0 if undefined
                        hoverOffset: 10
                    }
                ]
            }
        };
    }

    async getBrokerTenancy() {
        const groups = await this.orm.readGroup(
            "tenancy.details",
            [['is_any_broker', '=', true]],
            ['broker_id'],
            ['broker_id'],
            { limit: 5 } // Limit to top 5 brokers
        );
        const brokerTenancy = {};
        for (const group of groups) {
            if (group.broker_id && group.broker_id[0]) {
                const brokerId = parseInt(group.broker_id[0]);
                const brokers = await this.orm.read("res.partner", [brokerId], ['name']);
                if (brokers && brokers.length > 0 && brokers[0].name) {
                    brokerTenancy[brokers[0].name] = group.broker_id_count || 0; // Default to 0 if undefined
                }
            }
        }
        const sortedBrokers = Object.entries(brokerTenancy).sort((a, b) => b[1] - a[1]);
        const brokerNames = sortedBrokers.map(([name]) => name);
        const brokerCounts = sortedBrokers.map(([, count]) => count);
        this.state.brokerTenancy = {
            data: {
                labels: brokerNames,
                datasets: [
                    {
                        label: 'Broker Tenancy Count',
                        data: brokerCounts,
                        hoverOffset: 10
                    }
                ]
            },
            topBrokers: {
                names: brokerNames,
                counts: brokerCounts
            }
        };
    }

    async getBrokerPropertySold() {
        const groups = await this.orm.readGroup(
            "property.vendor",
            [['is_any_broker', '=', true],['stage', '=', 'sold']],
            ['broker_id'],
            ['broker_id'],
            { limit: 5 } // Limit to top 5 brokers
        );
        const brokerSold = {};
        for (const group of groups) {
            if (group.broker_id && group.broker_id[0]) {
                const brokerId = parseInt(group.broker_id[0]);
                const brokers = await this.orm.read("res.partner", [brokerId], ['name']);
                if (brokers && brokers.length > 0 && brokers[0].name) {
                    brokerSold[brokers[0].name] = group.broker_id_count || 0; // Default to 0 if undefined
                }
            }
        }
        const sortedBrokers = Object.entries(brokerSold).sort((a, b) => b[1] - a[1]);
        const brokerNames = sortedBrokers.map(([name]) => name);
        const brokerCounts = sortedBrokers.map(([, count]) => count);
        this.state.brokerPropertySold = {
            data: {
                labels: brokerNames,
                datasets: [
                    {
                        label: 'Broker Sold Count',
                        data: brokerCounts,
                        hoverOffset: 10
                    }
                ],
            },
        };  () => {
          // After updating the state, update the chart data and re-render it
          myChart.data = this.state.brokerPropertySold.data; // Update chart data
          myChart.update();  // Trigger chart re-render
        };
    }
     // property tenancy due/paid
    async getPropertyDuePaid(){
        const data = await this.orm.searchRead(
            "rent.invoice", // Model
            [["payment_state", "in", ["paid", "not_paid","in_payment"]]], // Domain
            ["amount", "payment_state"] // Fields to retrieve
        )
        // Initialize amounts
        let paidAmount = 0;
        let dueAmount = 0;
        // Aggregate amounts
        data.forEach(record => {
            if (record.payment_state === "paid" || record.payment_state === "in_payment") {
                paidAmount += record.amount || 0;
            } else if (record.payment_state === "not_paid") {
                dueAmount += record.amount || 0;
            }
        });
        this.state.propertyDuePaid = {
            data: {
                labels: ["Tenancy Paid", "Tenancy Due"],
                datasets: [
                  {
                    label: 'Amount',
                    data: [paidAmount, dueAmount],
                    hoverOffset: 10
                  }
                ]
            },
        }
    }

    async getPropertySoldDuePaid() {
        const data = await this.orm.searchRead(
            "property.vendor", // Model
            [["stage", "in", ["sold"]]], // Domain
            ["sale_price"], // Field to retrieve related invoices
        );
        const invoices = await this.orm.searchRead(
            "rent.invoice", // Model
            [["type", "=", "rent"]], // Domain
            ["amount"] // Fields to retrieve
        );
        // Initialize amounts
        let paidAmount = 0;
        let unpaidAmount = 0;
        // Summarize data by payment state
//       invoice.forEach(sold_invoice_id => {
//            if (invoice.payment_state === "paid" || invoice.payment_state === "in_payment") {
//                paidAmount += invoice.amount || 0;
//            } else if (invoice.payment_state === "not_paid") {
//                unpaidAmount += invoice.amount || 0;
//            }
//        });
        this.state.propertySoldDuePaid = {
            data: {
                labels: ["Property Sold Paid", "Property Sold Due"],
                datasets: [
                  {
                    label: 'Amount',
                    data: [paidAmount, unpaidAmount],
                    hoverOffset: 10
                  }
                ],
            },
        };
    }
    setup() {
        this.state = useState({
            statistics: {
                totalProperties: 0,
                availableProperties: 0,
                soldProperties: 0,
                bookedProperties: 0,
                onSale: 0,
                onLease: 0,
            },
            //Sale Details
            saleDetails: {
                totalBooked: 0,
                property: 0,
                totalSold: 0,
            },
            tenancyDetails: {
                draftContracts: 0,
                runningContracts: 0,
                expiredContracts: 0,
                totalRentAmount: 0,
                invoiceDueReminder: 0,
            },

             getPropertyType: { data: { labels: [], datasets: [] } },
             getPropertyStage: { data: { labels: [], datasets: [] } },
             getBrokerTenancy: { data: { labels: [], datasets: [] } },
             getBrokerPropertySold: { data: { labels: [], datasets: [] } },
             getPropertyDuePaid: { data: { labels: [], datasets: [] } },
             getPropertySoldDuePaid: { data: { labels: [], datasets: [] } },

             // Floor check

             floorZero: {
                totalZero: 0,
                activeZero: 0,
                inactiveZero: 0,
            },
            floorOne: {
                total: 0,
                active: 0,
                inactive: 0,
            },
            floorTwo: {
                totalTwo: 0,
                activeTwo: 0,
                inactiveTwo: 0,
            },
            floorThree: {
                totalThree: 0,
                activeThree: 0,
                inactiveThree: 0,
            },
            floorFour: {
                totalFour: 0,
                activeFour: 0,
                inactiveFour: 0,
            },
            floorFive: {
                totalFive: 0,
                activeFive: 0,
                inactiveFive: 0,
            },


        });
        this.orm = useService("orm");
        this.actionService = useService("action");
        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    async loadDashboardData() {
        try {
            // Batch the data-fetching tasks
            const [
                totalProperties,
                availableProperties,
                soldProperties,
                bookedProperties,
                onSale,
                onLease,
                totalBooked,
                property,
                totalSold,
                draftContracts,
                runningContracts,
                expiredContracts,
                invoiceDueReminder,
                totalRentAmount,
                getPropertyType,
                getPropertyStage,
                getBrokerTenancy,
                getBrokerPropertySold,
                getPropertyDuePaid,
                getPropertySoldDuePaid,
                totalZero,
                activeZero,
                inactiveZero,
                total,
                active,
                inactive,
                totalTwo,
                activeTwo,
                inactiveTwo,
                totalThree,
                activeThree,
                inactiveThree,
                totalFour,
                activeFour,
                inactiveFour,
                totalFive,
                activeFive,
                inactiveFive,

            ] = await Promise.all([
                this.getPropertyCount(['available', 'sale', 'sold', 'draft', 'booked', 'on_lease']),
                this.getPropertyCount(['available']),
                this.getPropertyCount(['sold']),
                this.getPropertyCount(['booked']),
                this.getPropertyCount(['sale']),
                this.getPropertyCount(['on_lease']),
                this.getSaleDetails(['booked']),
                this.getSaleDetails(['sold']),
                this.getSaleAmount(['sold']),
                this.getTenancyCount(['new_contract']),
                this.getTenancyCount(['running_contract']),
                this.getTenancyCount('expire_contract'),
                this.getInvoiceCount('not_paid','paid'),
                this.calculateTotalRentAmount(),
                this.getPropertyType(),
                this.getPropertyStage(),
                this.getBrokerTenancy(),
                this.getBrokerPropertySold(),
                this.getPropertyDuePaid(),
                this.getPropertySoldDuePaid(),
                this.getTotalZeroCount(),
                this.getActiveZeroCount(),
                this.getInactiveZeroCount(),
                this.getTotalCount(),
                this.getActiveCount(),
                this.getInactiveCount(),
                this.getTotalTwoCount(),
                this.getActiveTwoCount(),
                this.getInactiveTwoCount(),
                this.getTotalThreeCount(),
                this.getActiveThreeCount(),
                this.getInactiveThreeCount(),
                this.getTotalFourCount(),
                this.getActiveFourCount(),
                this.getInactiveFourCount(),
                this.getTotalFiveCount(),
                this.getActiveFiveCount(),
                this.getInactiveFiveCount(),
            ]);

            // Update the state once all data is fetched
            this.state.statistics = {
                totalProperties,
                availableProperties,
                soldProperties,
                bookedProperties,
                onSale,
                onLease,
            };
            this.state.getPropertyType,
            this.state.getPropertyStage,
            this.state.getBrokerTenancy,
            this.state.getBrokerPropertySold,
            this.state.getPropertyDuePaid,
            this.state.getPropertySoldDuePaid,
            this.state.saleDetails = {
                totalBooked,
                property,
                totalSold,
            };
            this.state.tenancyDetails = {
                draftContracts,
                runningContracts,
                expiredContracts,
                totalRentAmount,
                invoiceDueReminder,
            };
            this.state.floorZero= {
                totalZero,
                activeZero,
                inactiveZero,
            };

            this.state.floorOne = {
                total,
                active,
                inactive,
            };
            this.state.floorTwo = {
                totalTwo,
                activeTwo,
                inactiveTwo,
            };
            this.state.floorThree = {
                totalThree,
                activeThree,
                inactiveThree,
            };
            this.state.floorFour = {
                totalFour,
                activeFour,
                inactiveFour,
            };
            this.state.floorFive = {
                totalFive,
                activeFive,
                inactiveFive,
            };
        } catch (error) {
            console.error("Error loading dashboard data:", error);
        }
    }

     // calculate Ground floor plan
    async getTotalZeroCount() {
        const data1 = await this.orm.searchCount("floor.plan", [['floor_no', '=', "0"], ['status', '=', "active"]]);
        const data2 = await this.orm.searchCount("floor.plan", [['floor_no', '=', "0"], ['status', '=', "inactive"]]);
        const data4= data1+data2;
        return data4;
    }
    async getActiveZeroCount() {
        return this.orm.searchCount("floor.plan", [['floor_no', '=', "0"],['status', '=', "active"]]);
    }
    async getInactiveZeroCount() {
        return this.orm.searchCount("floor.plan", [['floor_no', '=', "0"],['status', '=', "inactive"]]);
//    const data2 = 10;
//    const data1 = await this.orm.searchCount("floor.plan", [['floor_no', '=', "1"], ['status', '=', "active"]]);
//    const data4= data2-data1;
//    return data4;
    }


     // calculate 1st floor plan
    async getTotalCount() {
        const data1 = await this.orm.searchCount("floor.plan", [['floor_no', '=', "1"], ['status', '=', "active"]]);
        const data2 = await this.orm.searchCount("floor.plan", [['floor_no', '=', "1"], ['status', '=', "inactive"]]);
        const data4= data1+data2;
        return data4;
    }
    async getActiveCount() {
        return this.orm.searchCount("floor.plan", [['floor_no', '=', "1"],['status', '=', "active"]]);
    }
    async getInactiveCount() {
        return this.orm.searchCount("floor.plan", [['floor_no', '=', "1"],['status', '=', "inactive"]]);
//    const data2 = 10;
//    const data1 = await this.orm.searchCount("floor.plan", [['floor_no', '=', "1"], ['status', '=', "active"]]);
//    const data4= data2-data1;
//    return data4;
    }


     // calculate 2nd floor plan
    async getTotalTwoCount() {
        const data1 = await this.orm.searchCount("floor.plan", [['floor_no', '=', "2"], ['status', '=', "active"]]);
        const data2 = await this.orm.searchCount("floor.plan", [['floor_no', '=', "2"], ['status', '=', "inactive"]]);
        const data4= data1+data2;
        return data4;
    }
    async getActiveTwoCount() {
        return this.orm.searchCount("floor.plan", [['floor_no', '=', "2"],['status', '=', "active"]]);
    }
    async getInactiveTwoCount() {
        return this.orm.searchCount("floor.plan", [['floor_no', '=', "2"],['status', '=', "inactive"]]);
//        const data2 = 10;
//        const data1 = await this.orm.searchCount("floor.plan", [['floor_no', '=', "2"],[ 'status', '=', "active"]]);
//        const data4= data2-data1;
//        return data4;
    }

    // calculate 3rd floor plan
    async getTotalThreeCount() {
        const data1 = await this.orm.searchCount("floor.plan", [['floor_no', '=', "3"], ['status', '=', "active"]]);
        const data2 = await this.orm.searchCount("floor.plan", [['floor_no', '=', "3"], ['status', '=', "inactive"]]);
        const data4= data1+data2;
        return data4;
    }
    async getActiveThreeCount() {
        return this.orm.searchCount("floor.plan", [['floor_no', '=', "3"],[ 'status', '=', "active"]]);
    }
    async getInactiveThreeCount() {
        return this.orm.searchCount("floor.plan", [['floor_no', '=', "3"],['status', '=', "inactive"]]);
//        const data2 = 10;
//        const data1 = await this.orm.searchCount("floor.plan", [['floor_no', '=', "3"],[ 'status', '=', "active"]]);
//        const data4= data2-data1;
//        return data4;
    }

    // calculate 4th floor plan
    async getTotalFourCount() {
        const data1 = await this.orm.searchCount("floor.plan", [['floor_no', '=', "4"], ['status', '=', "active"]]);
        const data2 = await this.orm.searchCount("floor.plan", [['floor_no', '=', "4"], ['status', '=', "inactive"]]);
        const data4= data1+data2;
        return data4;
    }
    async getActiveFourCount() {
        return this.orm.searchCount("floor.plan", [['floor_no', '=', "4"],[ 'status', '=', "active"]]);
    }
    async getInactiveFourCount() {
        return this.orm.searchCount("floor.plan", [['floor_no', '=', "4"],['status', '=', "inactive"]]);
//        const data2 = 10;
//        const data1 = await this.orm.searchCount("floor.plan", [['floor_no', '=', "4"],[ 'status', '=', "active"]]);
//        const data4= data2-data1;
//        return data4;
    }

    // calculate 5th floor plan
    async getTotalFiveCount() {
        const data1 = await this.orm.searchCount("floor.plan", [['floor_no', '=', "5"], ['status', '=', "active"]]);
        const data2 = await this.orm.searchCount("floor.plan", [['floor_no', '=', "5"], ['status', '=', "inactive"]]);
        const data4= data1+data2;
        return data4;
    }
    async getActiveFiveCount() {
        return this.orm.searchCount("floor.plan", [['floor_no', '=', "5"],[ 'status', '=', "active"]]);
    }
    async getInactiveFiveCount() {
        return this.orm.searchCount("floor.plan", [['floor_no', '=', "5"],['status', '=', "inactive"]]);
//        const data2 = 10;
//        const data1 = await this.orm.searchCount("floor.plan", [['floor_no', '=', "5"],[ 'status', '=', "active"]]);
//        const data4= data2-data1;
//        return data4;
    }
// view action
    viewTotalGround(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Ground Floor Total",
            res_model: "floor.plan",
            domain: [["floor_no", "=", "0"], ["status", "=", ["active","inactive"]]],
            views: [[false, 'kanban']],
            context: { create: false }
        });
    }
    viewTotalActiveGround(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Ground Floor Active",
            res_model: "floor.plan",
            domain: [["floor_no", "=", "0"], ["status", "=", ["active","inactive"]]],
            views: [[false, 'kanban']],
            context: { create: false }
        });
    }
    viewTotalInactiveGround(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Ground Floor Inactive",
            res_model: "floor.plan",
            domain: [["floor_no", "=", "0"], ["status", "=", ["active","inactive"]]],
            views: [[false, 'kanban']],
            context: { create: false }
        });
    }

    viewTotalOne(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "First Floor Total",
            res_model: "floor.plan",
            domain: [["floor_no", "=", "1"], ["status", "=", ["active","inactive"]]],
            views: [[false, 'kanban']],
            context: { create: false }
        });
    }
    viewTotalActiveOne(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "First Floor Active",
            res_model: "floor.plan",
            domain: [["floor_no", "=", "1"], ["status", "=", "active"]],
            views: [[false, 'kanban']],
            context: { create: false }
        });
    }
    viewTotalInactiveOne(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "First Floor Inactive",
            res_model: "floor.plan",
            domain: [["floor_no", "=", "1"], ["status", "=", "inactive"]],
            views: [[false, 'kanban']],
            context: { create: false }
        })
    }
    viewTotalTwo(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Second Floor Total",
            res_model: "floor.plan",
            domain: [["floor_no", "=", "2"], ["status", "=", ["active","inactive"]]],
            views: [[false, 'kanban']],
            context: { create: false }
        });
    }
    viewTotalActiveTwo(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Second Floor Active",
            res_model: "floor.plan",
            domain: [["floor_no", "=", "2"], ["status", "=", "active"]],
            views: [[false, 'kanban']],
            context: { create: false }
        });
    }
    viewTotalInactiveTwo(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Second Floor Inactive",
            res_model: "floor.plan",
            domain: [["floor_no", "=", "2"], ["status", "=", "inactive"]],
            views: [[false, 'kanban']],
            context: { create: false }
        })
    }
    viewTotalThree(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Third Floor Total",
            res_model: "floor.plan",
            domain: [["floor_no", "=", "3"], ["status", "=", ["active","inactive"]]],
            views: [[false, 'kanban']],
            context: { create: false }
        });
    }
    viewTotalActiveThree(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Third Floor Active",
            res_model: "floor.plan",
            domain: [["floor_no", "=", "3"], ["status", "=", "active"]],
            views: [[false, 'kanban']],
            context: { create: false }
        });
    }
    viewTotalInactiveThree(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Third Floor Inactive",
            res_model: "floor.plan",
            domain: [["floor_no", "=", "3"], ["status", "=", "inactive"]],
            views: [[false, 'kanban']],
            context: { create: false }
        })
    }
    viewTotalFour(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Fourth Floor Total",
            res_model: "floor.plan",
            domain: [["floor_no", "=", "4"], ["status", "=", ["active","inactive"]]],
            views: [[false, 'kanban']],
            context: { create: false }
        });
    }
    viewTotalActiveFour(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Fourth Floor Active",
            res_model: "floor.plan",
            domain: [["floor_no", "=", "4"], ["status", "=", "active"]],
            views: [[false, 'kanban']],
            context: { create: false }
        });
    }
    viewTotalInactiveFour(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Fourth Floor Inactive",
            res_model: "floor.plan",
            domain: [["floor_no", "=", "4"], ["status", "=", "inactive"]],
            views: [[false, 'kanban']],
            context: { create: false }
        })
    }

   viewTotalFive(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Fifth Floor Total",
            res_model: "floor.plan",
            domain: [["floor_no", "=", "5"], ["status", "=", ["active","inactive"]]],
            views: [[false, 'kanban']],
            context: { create: false }
        });
    }
    viewTotalActiveFive(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Fifth Floor Active",
            res_model: "floor.plan",
            domain: [["floor_no", "=", "5"], ["status", "=", "active"]],
            views: [[false, 'kanban']],
            context: { create: false }
        });
    }
    viewTotalInactiveFive(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Fifth Floor Inactive",
            res_model: "floor.plan",
            domain: [["floor_no", "=", "5"], ["status", "=", "inactive"]],
            views: [[false, 'kanban']],
            context: { create: false }
        })
    }

    viewTotalProperties(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Total Properties",
            res_model: "property.details",
            domain: [['stage','in',['available', 'sale', 'sold', 'draft', 'booked', 'on_lease']]],
            views: [[false, 'kanban'],[false, 'list'], [false, 'form']],
            context: { create: false }
        })
    }

    viewAvailableProperties(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Available Properties",
            res_model: "property.details",
            domain: [['stage','in',['available']]],
            views: [[false, 'kanban'],[false, 'list'], [false, 'form']],
            context: { create: false }
        })
    }

    viewSoldProperties(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Sold Properties",
            res_model: "property.details",
            domain: [['stage','in',['sold']]],
            views: [[false, 'kanban'],[false, 'list'], [false, 'form']],
            context: { create: false }
        })
    }

    viewBookedProperties(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Booked Properties",
            res_model: "property.details",
            domain: [['stage','in',['booked']]],
            views: [[false, 'kanban'],[false, 'list'], [false, 'form']],
            context: { create: false }
        })
    }

    viewOnSaleProperties(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "On Sale Properties",
            res_model: "property.details",
            domain: [['stage','in',['sale']]],
            views: [[false, 'kanban'],[false, 'list'], [false, 'form']],
            context: { create: false }
        })
    }

    viewOnLeaseProperties(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "On Lease Properties",
            res_model: "property.details",
            domain: [['stage','in',['on_lease']]],
            views: [[false, 'kanban'],[false, 'list'], [false, 'form']],
            context: { create: false }
        })
    }
//Sale Details

    viewTotalBookedProperties(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Total Booked Properties",
            res_model: "property.vendor",
            domain: [['stage', '=', 'booked']],
            views: [[false, 'kanban'],[false, 'list'], [false, 'form']],
            context: { create: false }
        })
    }

    viewPropertySold(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Sold Properties",
            res_model: "property.vendor",
            domain: [['stage','in',['sold']]],
            views: [[false, 'kanban'],[false, 'list'], [false, 'form']],
            context: { create: false }
        })
    }

    viewTotalSoldAmount(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Total Sold Amount",
            res_model: "property.vendor",
            domain: [['stage','in',['sold']]],
            views: [[false, 'kanban'],[false, 'list'], [false, 'form']],
            context: { create: false }
        })
    }
//Tenancy Details

    viewDraftContract(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Draft Contract",
            res_model: "tenancy.details",
            domain: [['contract_type', '=', 'new_contract']],
            views: [[false, 'kanban'],[false, 'list'], [false, 'form']],
            context: { create: false }
        })
    }

    viewRunningContract(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Running Contract",
            res_model: "tenancy.details",
            domain: [['contract_type', '=', 'running_contract']],
            views: [[false, 'kanban'],[false, 'list'], [false, 'form']],
            context: { create: false }
        })
    }

    viewExpiredContract(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Expired Contract",
            res_model: "tenancy.details",
            domain: [['contract_type', '=', 'expire_contract']],
            views: [[false, 'kanban'],[false, 'list'], [false, 'form']],
            context: { create: false }
        })
    }

    viewTotalRentAmount(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Property Rent",
            res_model: "rent.invoice",
            domain: ['|', ['type', '=', 'rent'], ['type', '=', 'full_rent']],
            views: [[false, 'kanban'],[false, 'list'], [false, 'form']],
            context: { create: false }
        })
    }

    viewInvoiceDueReminder(){
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Pending Invoice",
            res_model: "rent.invoice",
            domain: [['payment_state', '=', ['not_paid','paid']]],
            views: [[false, 'list'], [false, 'form'], [false, 'search']],
            context: {"search_default_landlord":1,
                        "create": false},
        })
    }


    async getPropertyCount(stages) {
        return this.orm.searchCount("property.details", [['stage', 'in', stages]]);
    }
    async getSaleDetails(stages) {
        return this.orm.searchCount("property.vendor", [['stage', 'in', stages]]);
    }
    async getSaleAmount(stages) {
//        return this.orm.searchCount("property.vendor", [['stage', 'in', stages]]);
        const [SaleAmount] = await Promise.all([
        this.orm.searchRead("property.vendor", [["stage", "=", "sold"]], ["sale_price"])
        ])
        const totalSalePrice = SaleAmount.reduce((sum, record) => sum + (record.sale_price || 0), 0);
        return (totalSalePrice).toLocaleString('en-IN', {
                style: 'currency',
                currency: 'INR'
              });
    }

    async getTenancyCount(contractType) {
        return this.orm.searchCount("tenancy.details", [['contract_type', '=', contractType]]);
    }

    async getInvoiceCount(paymentState) {
        return this.orm.searchCount("rent.invoice", [['payment_state', '=', paymentState]]);
    }

    async calculateTotalRentAmount() {
        const [propertyData, rentData, fullRentData] = await Promise.all([
            this.orm.searchRead("property.vendor", [["stage", "=", "sold"]], ["sale_price"]),
            this.orm.searchRead("rent.invoice", [["type", "=", "rent"]], ["amount"]),
            this.orm.searchRead("rent.invoice", [["type", "=", "full_rent"]], ["rent_amount"]),
        ]);
        const totalSalePrice = propertyData.reduce((sum, record) => sum + (record.sale_price || 0), 0);
        const totalRentAmount = rentData.reduce((sum, record) => sum + (record.amount || 0), 0);
        const totalFullRentAmount = fullRentData.reduce((sum, record) => sum + (record.rent_amount || 0), 0);

        return (totalSalePrice + totalRentAmount + totalFullRentAmount).toLocaleString('en-IN', {
                style: 'currency',
                currency: 'INR'
              });
    }

}
OwlRentalDashboard.template = "owl.OwlRentalDashboard";
OwlRentalDashboard.components = { ChartRenderer };
registry.category("actions").add("owl.rental_dashboard", OwlRentalDashboard);
