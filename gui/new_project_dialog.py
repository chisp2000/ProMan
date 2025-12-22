import tkinter as tk
from tkinter import ttk, filedialog
from typing import Optional

class NewProjectDialog:
    def __init__(self, parent_root, controller, project_to_edit=None):
        self.controller = controller
        self.project_to_edit = project_to_edit
        
        self.dialog = tk.Toplevel(parent_root)
        self.dialog.title("Edit Project" if project_to_edit else "Create New Project")
        self.dialog.geometry("500x600") 
        self.dialog.transient(parent_root) 
        self.dialog.grab_set()
        
        # 1. Fetch the EXACT grey used by the Entry widgets from the theme
        self.style = ttk.Style()
        self.entry_bg = self.style.lookup("TEntry", "fieldbackground") or "#3E3E3E"
        # Standard black for the thin border logic
        self.border_color = "#000000" 
        self.dialog.configure(bg=self.style.lookup("TFrame", "background"))
        
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill='both', expand=True)

        row_counter = 0

        # Project Name
        ttk.Label(main_frame, text="Project Name:").grid(row=row_counter, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(main_frame, width=50)
        self.name_entry.grid(row=row_counter, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        row_counter += 1

        # Priority
        ttk.Label(main_frame, text="Priority (3/2/1):").grid(row=row_counter, column=0, sticky="w", pady=5)
        self.priority_var = tk.StringVar(value=3)
        self.priority_menu = ttk.Combobox(main_frame, textvariable=self.priority_var, values=[3, 2, 1], state="readonly", width=10)
        self.priority_menu.grid(row=row_counter, column=1, padx=10, pady=5, sticky="w")
        row_counter += 1
        
        # Due Date
        ttk.Label(main_frame, text="Due Date (YYYY-MM-DD):").grid(row=row_counter, column=0, sticky="w", pady=5)
        self.date_entry = ttk.Entry(main_frame, width=50)
        self.date_entry.grid(row=row_counter, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        row_counter += 1

        # Thumbnail Image
        ttk.Label(main_frame, text="Thumbnail Image:").grid(row=row_counter, column=0, sticky="w", pady=5)
        self.image_path_var = tk.StringVar()
        self.image_entry = ttk.Entry(main_frame, textvariable=self.image_path_var, width=35)
        self.image_entry.grid(row=row_counter, column=1, padx=(10, 0), pady=5, sticky="ew")
        ttk.Button(main_frame, text="Browse", command=self.browse_image).grid(row=row_counter, column=2, padx=(5, 10), pady=5, sticky="e")
        row_counter += 1

        # --- DESCRIPTION BOX (EXACT MATCH WITH THIN BLACK BORDER) ---
        ttk.Label(main_frame, text="Project Description:").grid(row=row_counter, column=0, sticky="nw", pady=5)
        
        self.desc_text = tk.Text(
            main_frame, 
            height=10, 
            width=40, 
            font=("Segoe UI", 9),
            wrap="word",
            bg=self.entry_bg,
            fg="white", 
            insertbackground="white",
            selectbackground="#cfcfcf",
            selectforeground="black",
            padx=5,
            pady=5,
            # BORDER STYLE LOGIC
            borderwidth=1,
            relief="flat",            # Flat relief to allow highlightthickness to act as border
            highlightthickness=1,     # Creates the thin 1px border
            highlightbackground=self.border_color, # Unfocused border color (Black)
            highlightcolor=self.border_color       # Focused border color (Black)
        )
        self.desc_text.grid(row=row_counter, column=1, columnspan=2, padx=10, pady=5, sticky="nsew")
        row_counter += 1
        
        main_frame.grid_rowconfigure(row_counter-1, weight=1) 
        main_frame.grid_columnconfigure(1, weight=1) 

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row_counter, column=0, columnspan=3, pady=15) 
        ttk.Button(button_frame, text="Save", command=self.submit_data).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side='left', padx=5)

    def browse_image(self):
        file_path = filedialog.askopenfilename(filetypes=(("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")))
        if file_path: self.image_path_var.set(file_path)

    def submit_data(self):
        name = self.name_entry.get()
        try: 
            priority = int(self.priority_var.get()) 
        except: 
            priority = 3
        due_date = self.date_entry.get()
        image_path = self.image_path_var.get() or None 
        description = self.desc_text.get("1.0", "end-1c")
        
        if name and due_date:
            if self.project_to_edit:
                # UPDATE EXISTING: Pass the original ID so we don't create a duplicate
                self.controller.update_existing_project(
                    self.project_to_edit.id, name, priority, due_date, image_path, description
                )
            else:
                # CREATE NEW
                self.controller.create_new_project(name, priority, due_date, image_path, description)
            
            self.dialog.destroy()