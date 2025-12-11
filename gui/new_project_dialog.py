# --- gui/new_project_dialog.py ---

import tkinter as tk
from tkinter import ttk, filedialog
from typing import Optional

class NewProjectDialog:
    def __init__(self, parent_root, controller):
        self.controller = controller
        
        self.dialog = tk.Toplevel(parent_root)
        self.dialog.title("Create New Project")
        self.dialog.transient(parent_root) 
        self.dialog.grab_set()
        
        self.create_widgets()
        
    def create_widgets(self):
        
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill='both', expand=True)

        # Initialize current row counter
        row_counter = 0

        # 1. Project Name (Span column 1 and 2)
        ttk.Label(main_frame, text="Project Name:").grid(row=row_counter, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(main_frame, width=50)
        self.name_entry.grid(row=row_counter, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        row_counter += 1

        # 2. Priority
        ttk.Label(main_frame, text="Priority (3/2/1):").grid(row=row_counter, column=0, sticky="w", pady=5)
        self.priority_var = tk.StringVar(value=3)
        self.priority_menu = ttk.Combobox(
            main_frame, 
            textvariable=self.priority_var, 
            values=[3, 2, 1],
            state="readonly",
            width=10
        )
        self.priority_menu.grid(row=row_counter, column=1, padx=10, pady=5, sticky="w")
        row_counter += 1
        
        # 3. Due Date (Span column 1 and 2)
        ttk.Label(main_frame, text="Due Date (YYYY-MM-DD):").grid(row=row_counter, column=0, sticky="w", pady=5)
        self.date_entry = ttk.Entry(main_frame, width=50)
        self.date_entry.insert(0, '')
        self.date_entry.grid(row=row_counter, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        row_counter += 1
        
        # 4. Thumbnail Image Input (Needs precise control)
        ttk.Label(main_frame, text="Thumbnail Image (Path Only):").grid(row=row_counter, column=0, sticky="w", pady=5)
        
        self.image_path_var = tk.StringVar()
        self.image_entry = ttk.Entry(main_frame, textvariable=self.image_path_var, width=35)
        self.image_entry.grid(row=row_counter, column=1, padx=(10, 0), pady=5, sticky="ew")

        browse_btn = ttk.Button(main_frame, text="Browse", command=self.browse_image)
        browse_btn.grid(row=row_counter, column=2, padx=(5, 10), pady=5, sticky="e")
        row_counter += 1
        
        # 5. IMAGE SIZE INSTRUCTION (NEW ADDITION)
        self.size_label = ttk.Label(
            main_frame, 
            text="Desired Size: 300x200px (GIF/PPM only)",
            font=("Arial", 9, "italic"),
            foreground="darkred"
        )
        # Span all three columns to place it neatly below the inputs
        self.size_label.grid(row=row_counter, column=0, columnspan=3, sticky="w", padx=10)
        row_counter += 1
        
        # Configure column weights to ensure column 1 expands when the window is resized
        main_frame.grid_columnconfigure(1, weight=1) 
        
        # 6. Control Buttons (Cleaned up and placed on the final row)
        button_frame = ttk.Frame(main_frame)
        # Place on the current row and span all columns
        button_frame.grid(row=row_counter, column=0, columnspan=3, pady=15) 

        # Add buttons to the button_frame using pack for horizontal alignment
        ttk.Button(button_frame, text="Create", command=self.submit_data).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side='left', padx=5)
        
    def browse_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Project Thumbnail Image",
            filetypes=(("Image files", "*.gif *.ppm"), ("All files", "*.*")) # Only allow displayable formats
        )
        if file_path:
            self.image_path_var.set(file_path)

    def submit_data(self):
        name = self.name_entry.get()
        priority = int(self.priority_var.get()) 
        due_date = self.date_entry.get()
        image_path: Optional[str] = self.image_path_var.get() or None 
        
        if name and due_date:
            self.controller.create_new_project(name, priority, due_date, image_path)
            self.dialog.destroy()
        else:
            print("Error: Name and Due Date are required.")