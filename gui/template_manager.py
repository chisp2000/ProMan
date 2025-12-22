import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from gui.project_detail_window import AdvancedLogEditor
import json

class TemplateManager:
    def __init__(self, parent, controller):
        self.controller = controller
        self.window = tk.Toplevel(parent)
        self.window.title("Manage Log Templates")
        self.window.geometry("600x450")
        
        # --- UI STYLING ---
        self.style = ttk.Style()
        
        # Distinct Bold Heading
        self.style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
        
        # MATCHING HIGHLIGHT COLOR (from project_detail_window)
        # This maps the selection state to the specific grey color
        self.style.map("Treeview", 
            background=[('selected', '#cfcfcf')],
            foreground=[('selected', 'black')]
        )
        
        # Main Layout
        self.main_container = ttk.Frame(self.window)
        self.main_container.pack(fill='both', expand=True)

        cols = ("ID", "Template Name")
        self.tree = ttk.Treeview(self.main_container, columns=cols, show='headings')
        
        # ID Column: Centered and small
        self.tree.heading("ID", text="ID", anchor='center')
        self.tree.column("ID", anchor='center', width=60, stretch=False)
        
        # Template Name Column: Left aligned and expanding
        self.tree.heading("Template Name", text="Template Name", anchor='w')
        self.tree.column("Template Name", anchor='w', width=400, stretch=True)

        self.tree.pack(fill='both', expand=True, padx=10, pady=10)

        # --- DISCRETE ACTION BUTTONS ---
        # Side='left' keeps them from expanding to fill the row
        self.btn_frame = ttk.Frame(self.main_container)
        self.btn_frame.pack(fill='x', pady=5, padx=10)
        
        ttk.Button(self.btn_frame, text="➕ New", command=self.add_template).pack(side='left', padx=2)
        ttk.Button(self.btn_frame, text="✏️ Edit", command=self.edit_template).pack(side='left', padx=2)
        ttk.Button(self.btn_frame, text="🗑 Delete", command=self.show_delete_confirmation).pack(side='left', padx=2)

        # --- BUILT-IN CONFIRMATION STRIP ---
        self.confirm_frame = ttk.Frame(self.main_container)
        self.confirm_label = ttk.Label(self.confirm_frame, text="Are you sure?", foreground="orange")
        self.confirm_label.pack(side='left', padx=10)
        
        ttk.Button(self.confirm_frame, text="Yes, Delete", command=self.execute_delete).pack(side='left', padx=2)
        ttk.Button(self.confirm_frame, text="Cancel", command=self.hide_delete_confirmation).pack(side='left', padx=2)
        
        self.refresh()

    def refresh(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        templates = self.controller.db_controller.get_all_templates()
        for t in templates:
            self.tree.insert("", "end", values=(t['template_id'], t['name']))

    def add_template(self):
        name = simpledialog.askstring("Log Template", "Enter Template Name:")
        if name:
            editor = TemplateEditorDialog(self.window, self.controller, name)
            self.window.wait_window(editor.dialog)
            self.refresh()

    def edit_template(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selection", "Please select a template to edit.")
            return
        
        tid, name = self.tree.item(sel[0])['values']
        templates = self.controller.db_controller.get_all_templates()
        content = ""
        for t in templates:
            if t['template_id'] == tid:
                content = t['content']
                break
        
        editor = TemplateEditorDialog(self.window, self.controller, name)
        editor.editor.load_formatted_text(content) 
        self.window.wait_window(editor.dialog)
        self.refresh()

    def show_delete_confirmation(self):
        if not self.tree.selection():
            messagebox.showwarning("Selection", "Please select a template to delete.")
            return
        self.btn_frame.pack_forget()
        self.confirm_frame.pack(fill='x', pady=10, padx=10)

    def hide_delete_confirmation(self):
        self.confirm_frame.pack_forget()
        self.btn_frame.pack(fill='x', pady=5, padx=10)

    def execute_delete(self):
        sel = self.tree.selection()
        if sel:
            tid = self.tree.item(sel[0])['values'][0]
            self.controller.db_controller.delete_template(tid)
            self.refresh()
        self.hide_delete_confirmation()

class TemplateEditorDialog:
    def __init__(self, parent, controller, template_name):
        self.controller = controller
        self.template_name = template_name
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Editing Template: {template_name}")
        self.dialog.geometry("800x600")
        self.dialog.grab_set()

        self.main_f = ttk.Frame(self.dialog, padding=5)
        self.main_f.pack(fill='both', expand=True)
        
        self.status_label = ttk.Label(self.main_f, text=f"Template: {template_name}", font=("Arial", 9, "italic"))
        
        self.editor = AdvancedLogEditor(
            self.main_f, 
            controller, 
            lambda: None, 
            self.status_label, 
            lambda x: None
        )

        btn_frame = ttk.Frame(self.main_f)
        btn_frame.pack(side='bottom', fill='x', pady=5)
        self.status_label.pack(side='bottom', anchor='w', padx=5)

        ttk.Button(btn_frame, text="💾 Save Template", command=self.save_and_close).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy).pack(side='left', padx=5)

    def save_and_close(self):
        raw_text = self.editor.text_area.get("1.0", "end-1c")
        tag_data = [{"tag": t, "ranges": [str(r) for r in self.editor.text_area.tag_ranges(t)]} 
                    for t in ["bold", "italic", "underline", "strike", "code", "list"]]
        content_json = json.dumps({"text": raw_text, "tags": tag_data})
        try:
            self.controller.db_controller.save_template(self.template_name, content_json)
            self.dialog.destroy()
        except Exception as e:
            self.status_label.config(text=f"❌ Error: {e}", foreground="red")