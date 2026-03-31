/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormRenderer } from "@web/views/form/form_renderer";

patch(FormRenderer.prototype, {
    // Unique identifier for this patch
    dynamicCheckListPatch: {
        name: "cmr_new_recruitments.dynamic_checklist_tab",
    },

    onMounted() {
        this._super();

        console.log("✅ dynamic_checklist_tab patch mounted");

        const checklistVisible = this.props.record?.data?.checklist_tab_visible;
        console.log("checklist_tab_visible =", checklistVisible);

        if (checklistVisible) {
            console.log("👉 Trying to activate tab: custom_tab");
            this.activateNotebookPage("custom_tab");
        }
    },

    activateNotebookPage(pageName) {
        console.log("🔎 activateNotebookPage called with:", pageName);

        const notebook = this.el.querySelector(".o_notebook");
        if (!notebook) {
            console.warn("⚠️ Notebook not found!");
            return;
        }

        const tabs = notebook.querySelectorAll(".nav-link");
        const pages = notebook.querySelectorAll(".tab-pane");

        console.log("📌 Found tabs:", tabs.length, "pages:", pages.length);

        tabs.forEach(tab => tab.classList.remove("active"));
        pages.forEach(page => page.classList.remove("active", "show"));

        const targetTab = notebook.querySelector(`[data-bs-target="#${pageName}"]`);
        const targetPage = notebook.querySelector(`#${pageName}`);

        console.log("🎯 targetTab:", targetTab, "targetPage:", targetPage);

        if (targetTab && targetPage) {
            targetTab.classList.add("active");
            targetPage.classList.add("active", "show");
            console.log("✅ Tab switched successfully!");
        } else {
            console.warn("⚠️ Custom tab not found for:", pageName);
        }
    },
});
