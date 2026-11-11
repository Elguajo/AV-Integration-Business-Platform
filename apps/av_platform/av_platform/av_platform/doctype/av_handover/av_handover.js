frappe.ui.form.on("AV Handover", {
    refresh(frm) {
        if (frm.doc.docstatus !== 1 || frm.doc.project_manager !== frappe.session.user) return;
        if (frm.doc.project) {
            frm.add_custom_button(__("Open project"), () => frappe.set_route("Form", "Project", frm.doc.project));
        }
        if (frm.doc.review_status !== "Pending") return;
        const review = (decision, note = "") => frappe.call({
            method: "av_platform.av_platform.doctype.av_handover.av_handover.review_handover",
            args: {name: frm.doc.name, decision, note}, freeze: true,
            freeze_message: __("Saving PM decision…"),
            callback: () => frm.reload_doc(),
        });
        frm.add_custom_button(__("Accept handover"), () => review("accept"));
        frm.add_custom_button(__("Return to Sales"), () => frappe.prompt(
            {fieldname: "note", fieldtype: "Small Text", label: __("Required corrections"), reqd: 1},
            ({note}) => review("return", note), __("Return handover"), __("Return to Sales")
        ));
    },
});
