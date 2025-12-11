# --- gui/attachment_manager.py ---

import tkinter as tk
from tkinter import ttk, messagebox
import os

class AttachmentManager:
    def __init__(self, parent, controller):
        self.controller = controller
        self.window = tk.Toplevel(parent)
        self.window.title("Attachment Manager (Batch Edit)")
        self.window.geometry("600x400")
        
        # Table (Treeview)
        cols = ("ID", "Filename", "Scope", "Project ID")
        self.tree = ttk.Treeview(self.window, columns=cols, show='headings')
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Buttons
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill='x', pady=10)
        
        ttk.Button(btn_frame, text="Toggle Global/Project", command=self.toggle_scope).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_selected).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_list).pack(side='right', padx=10)

        self.refresh_list()

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        atts = self.controller.get_all_attachments_for_manager()
        for a in atts:
            scope = "GLOBAL" if a.is_global else "Project Specific"
            fname = os.path.basename(a.file_path)
            self.tree.insert("", "end", values=(a.id, fname, scope, a.project_id if a.project_id else "N/A"))

    def toggle_scope(self):
        selected = self.tree.selection()
        if not selected: return
        
        item = self.tree.item(selected[0])
        att_id = item['values'][0]
        scope_text = item['values'][2]
        is_global = (scope_text == "GLOBAL")
        
        self.controller.toggle_attachment_global(att_id, is_global)
        self.refresh_list()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected: return
        
        if messagebox.askyesno("Confirm", "Delete selected attachment?"):
            item = self.tree.item(selected[0])
            att_id = item['values'][0]
            self.controller.delete_attachment(att_id)
            self.refresh_list()