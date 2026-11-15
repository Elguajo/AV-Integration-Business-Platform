import frappe
from frappe.model.document import Document


class AVWorkStage(Document):
    def validate(self):
        self.is_closed = int(self.task_status == "Completed")
        if not self.enabled and not self.is_new() and frappe.db.exists("Task", {"av_stage": self.name}):
            frappe.throw("Move the tasks out of this stage before disabling it.")
