// The screen is a Vue app built from apps/av_platform/frontend (ADR-004).
// av_platform.desk.boot_session puts its current entry file into frappe.boot.av_desk.
frappe.pages["av-project"].on_page_load = function (wrapper) {
	const assets = frappe.boot.av_desk;
	const fail = () => {
		frappe.ui.make_app_page({ parent: wrapper, title: __("AV Platform"), single_column: true });
		frappe.msgprint(__("The interface bundle is missing. Rebuild apps/av_platform/frontend."));
	};
	if (!assets) return fail();
	import(assets.entry).then(() => window.av_desk.mount_page(wrapper, "av-project", "project"), fail);
};
