import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import PhotoImage
import os 
# Assuming ttkthemes is available, but using standard ttk.Style commands
from ttkthemes import ThemedStyle 

class MainWindow:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        
        self.controller.set_root(root) 
        self.controller.main_window = self 
        
        self.selected_project_id = None 
        self.last_selected_frame = None
        self.project_image_references = []
        
        self.root.title("ProMan - Project Selector")
        self.root.geometry("1000x600") 

        # --- STYLE DEFINITION ---
        style = ttk.Style(self.root)
        # Get the background color defined in main.py (e.g., #2E2E2E)
        LIST_BG_COLOR = style.lookup('TFrame', 'background') 
        
        # Define a custom style for the inner frame background
        style.configure("DarkList.TFrame", background=LIST_BG_COLOR)
        
        # --- DEFINITIVE FIX: Custom Left-Anchored Button Style with Padding Override ---
        # This fixes the left-spacing issue by reducing the theme's internal button padding.
        style.configure("LeftAnchor.TButton", anchor="w", padding=[1, 1, 1, 1])
        # ------------------------

        # --- Main Layout Setup (Two Columns: List left, Buttons right) ---
        outer_frame = ttk.Frame(self.root, padding="3")
        outer_frame.pack(fill='both', expand=True)

        # --- FIX: Adjust Column Weights ---
        outer_frame.grid_columnconfigure(0, weight=1) 
        outer_frame.grid_columnconfigure(1, weight=0) 
        outer_frame.grid_rowconfigure(0, weight=1) 
        # ------------------------------------

        # --- LEFT SIDE: Project List ---
        # CRITICAL: We save self.left_frame so we can identify it in the scroll handler
        self.left_frame = ttk.Frame(outer_frame)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 0)) 
        self.left_frame.grid_rowconfigure(1, weight=1) 
        self.left_frame.grid_columnconfigure(0, weight=1) 
        
        ttk.Label(self.left_frame, text="Your Projects (Click to Select):").grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        # Scrollable Canvas setup (self.canvas is created here!)
        self.canvas = tk.Canvas(self.left_frame, borderwidth=0, bg=LIST_BG_COLOR)
        self.scrollbar = ttk.Scrollbar(self.left_frame, orient="vertical", command=self.canvas.yview)
        self.project_display_frame = ttk.Frame(self.canvas, style="DarkList.TFrame")
        
        self.canvas.grid(row=1, column=0, sticky="nsew") 
        self.scrollbar.grid(row=1, column=1, sticky="ns")
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas_window = self.canvas.create_window((0, 0), 
                                                        window=self.project_display_frame, 
                                                        anchor="nw"
                                                        )
        self.canvas.bind('<Configure>', self.on_canvas_resize)
        
        # --- SCROLL WHEEL/TRACKPAD FIX: Global Binding with Container Check ---
        
        # 1. Bind X11 scroll events (Linux/older systems) directly to the canvas
        self.canvas.bind("<Button-4>", lambda e: self.on_mousewheel(e, 1))
        self.canvas.bind("<Button-5>", lambda e: self.on_mousewheel(e, -1))
        
        # 2. GLOBAL BINDING: Catch the MouseWheel event anywhere in the app
        #    The handler '_on_mousewheel_propagate' will check if the mouse is over 'self.left_frame'
        self.root.bind_all("<MouseWheel>", self._on_mousewheel_propagate)
        
        # ------------------------------------------------------------
        
        # --- RIGHT SIDE: Control Buttons ---
        
        buttons_container = ttk.Frame(outer_frame)
        buttons_container.grid(row=0, column=1, sticky="nw", padx=2, pady=(25, 0)) 

        # 1. Open Project Button
        self.open_project_btn = ttk.Button(
            buttons_container, 
            text="📂 Open Project", 
            command=self.open_project_clicked,
            state="disabled",
            style="LeftAnchor.TButton" 
        )
        self.open_project_btn.pack(fill='x', pady=(0, 5), padx=10)

        # 2. Batch Edit Attachments
        ttk.Button(
            buttons_container, 
            text="📂 Batch Edit Attachments", 
            command=self.controller.open_attachment_manager, 
            style="LeftAnchor.TButton" 
        ).pack(fill='x', pady=(0, 5), padx=10)
        
        # 3. Create New Project Button
        new_project_btn = ttk.Button(
            buttons_container, 
            text="➕ Create New Project", 
            command=self.controller.open_new_project_dialog,
            style="LeftAnchor.TButton" 
        )
        new_project_btn.pack(fill='x', pady=(0, 5), padx=10) 

        # 4. Edit Project Button
        self.edit_project_btn = ttk.Button(
            buttons_container, 
            text="✏️ Edit Selected Project", 
            command=self.edit_project_clicked,
            state="disabled",
            style="LeftAnchor.TButton" 
        )
        self.edit_project_btn.pack(fill='x', pady=(0, 5), padx=10)

        # 5. Delete Project Button
        self.delete_project_btn = ttk.Button(
            buttons_container, 
            text="\u232B Delete Selected Project", 
            command=self.delete_project_clicked,
            state="disabled",
            style="LeftAnchor.TButton" 
        )
        self.delete_project_btn.pack(fill='x', pady=(0, 5), padx=10)

        self.refresh_project_list() 

    # --- Button Handlers ---

    def open_project_clicked(self):
        if self.selected_project_id:
            self.controller.open_project_detail_window(self.selected_project_id)

    def edit_project_clicked(self):
        if self.selected_project_id:
            self.controller.open_edit_project_dialog(self.selected_project_id)
        else:
            messagebox.showwarning("No Selection", "Please select a project tile to edit.")

    # --- Layout and Selection Logic ---

    def on_canvas_resize(self, event):
        """
        Resizes the inner frame (self.project_display_frame) to match the 
        canvas width, ensuring the project tiles expand correctly.
        """
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width - 5)
        self.project_display_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    # --- UPDATED: Mouse Wheel Propagation Handler ---
    def _on_mousewheel_propagate(self, event):
        """
        Intercepts global MouseWheel events.
        It checks if the mouse is currently over the 'left_frame' (the list container).
        If so, it triggers scrolling.
        """
        # 1. Identify which widget is under the mouse cursor
        widget_under_mouse = self.root.winfo_containing(event.x_root, event.y_root)
        
        if widget_under_mouse is None:
            return

        # 2. Traverse up the widget hierarchy to see if we are inside self.left_frame
        current_widget = widget_under_mouse
        while current_widget:
            # If we find our list container in the ancestry, we should scroll
            if current_widget == self.left_frame:
                self.on_mousewheel(event)
                return "break" # Stop event from bubbling up to root
            
            # Move up to the parent widget
            current_widget = current_widget.master
            
            # Stop if we hit the root window
            if current_widget == self.root:
                break

    # --- UPDATED: Mouse Wheel Handler for Trackpads ---
    def on_mousewheel(self, event, direction=None):
        """
        Handles mouse wheel and trackpad scroll events for the canvas.
        """
        # Determine the scroll delta/direction
        if direction is not None:
            # This handles Button-4/Button-5 (X11 systems)
            delta = direction * -1 
        elif event.delta:
            # Windows/macOS MouseWheel
            delta = event.delta
        else:
            return

        # Normalization Logic:
        # Standard mouse wheel scrolls in large jumps (e.g., +/- 120).
        # Trackpads scroll in small increments.
        
        if abs(delta) >= 120:
            # Normalize large scrolls (standard wheel click) to 1 unit * 4
            scroll_amount = -1 * (delta // abs(delta)) * 4
        else:
            # For trackpads (small delta values), use delta directly for smooth scrolling
            scroll_amount = -1 * delta * 0.5 
        
        self.canvas.yview_scroll(int(scroll_amount), "units")

    def select_project(self, project_id: int, frame_widget):
        """Sets the selected project ID and updates the GUI appearance."""
        
        if self.last_selected_frame:
            self.last_selected_frame.config(relief="solid") 
            
        frame_widget.config(relief="sunken") 
        self.selected_project_id = project_id
        self.last_selected_frame = frame_widget
        
        # Enable Buttons
        self.delete_project_btn.config(state="normal")

        if hasattr(self, 'open_project_btn'):
              self.open_project_btn.config(state="normal")
              
        if hasattr(self, 'edit_project_btn'):
              self.edit_project_btn.config(state="normal")

        print(f"Project ID {project_id} selected.")

    def delete_project_clicked(self):
        """Prompts for confirmation and calls the delete flow."""
        if self.selected_project_id is not None:
            
            if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to permanently delete Project ID {self.selected_project_id} and ALL related data?"):
                self.controller.delete_project_flow(self.selected_project_id)
        else:
            messagebox.showwarning("No Selection", "Please select a project tile to delete first.")


    # --- Data Retrieval and Rendering ---

    def refresh_project_list(self):
        
        # 1. Clear existing frames and reset state
        for widget in self.project_display_frame.winfo_children():
            widget.destroy()
        self.project_image_references = [] 
        self.selected_project_id = None 
        self.last_selected_frame = None
        
        # Disable Buttons
        self.delete_project_btn.config(state="disabled")

        if hasattr(self, 'open_project_btn'):
            self.open_project_btn.config(state="disabled")
            
        if hasattr(self, 'edit_project_btn'):
            self.edit_project_btn.config(state="disabled")
        
        projects = self.controller.get_all_projects_sorted()
        
        # 2. Draw a frame for each project
        for p in projects:
            # Main container for the project tile
            project_frame = ttk.Frame(self.project_display_frame, 
                                      style="ProjectTile.TFrame") 
            project_frame.pack(fill='x', padx=5, pady=5)
            
            # --- Image Display (Packed Right) ---
            image_label = tk.Label(project_frame) 
            image_loaded = False 
            
            if p.thumbnail_path and os.path.exists(p.thumbnail_path):
                try:
                    # **CRITICAL: Load the image, then store the reference defensively**
                    photo_obj = PhotoImage(file=p.thumbnail_path)
                    
                    # Store the reference on the widget itself
                    image_label.image = photo_obj 
                    image_label.config(image=photo_obj)
                    
                    # Store a redundant reference in the master list
                    self.project_image_references.append(photo_obj) 
                    
                    image_loaded = True
                    
                except tk.TclError as e:
                    print(f"FATAL IMAGE LOAD ERROR (ID {p.id}): {e}")
                    pass 

            if not image_loaded:
                image_label.config(
                    text="[Image Error/Missing]", 
                    width=20, 
                    height=8, 
                    bg="red", 
                    fg="white"
                ) 
            
            # Pack the image to the right (must happen before the text frame)
            image_label.pack(side='right', padx=10, pady=5)
            
            # --- Text Container (Packs to the Left, Taking Remaining Space) ---
            text_frame = ttk.Frame(project_frame, style="DarkList.TFrame")
            text_frame.pack(side='left', fill='both', expand=True, padx=10, pady=5) 
            
            # Configure grid within the text_frame for vertical centering
            text_frame.grid_columnconfigure(0, weight=1) 
            text_frame.grid_rowconfigure(0, weight=1) 
            text_frame.grid_rowconfigure(3, weight=1) 
            
            # --- Text Details (Centered inside the Text Container) ---
            priority_text = {3: 'HIGH', 2: 'MEDIUM', 1: 'LOW'}.get(p.priority, 'N/A')
            
            # Project Name (Row 1)
            name_label = ttk.Label(text_frame, 
                                   text=p.name, 
                                   font=("EASVHS", 20), 
                                   style="OrangeBold.TLabel",
                                   anchor="center")
            name_label.grid(row=1, column=0, sticky="n", pady=(5, 2)) 

            # --- UPDATED: Details (Row 2) Composite Approach ---
            # Instead of one label, we use a Frame to hold multiple labels with mixed fonts
            detail_frame = ttk.Frame(text_frame, style="DarkList.TFrame")
            detail_frame.grid(row=2, column=0, sticky="n", pady=(0, 5))
            
            pixel_font = ("EASVHS", 14)
            safe_font = ("Arial", 12) # Fallback font for symbols

            # Helper to add parts and bind click event to them so selection works
            def add_detail_part(text_str, font_to_use):
                lbl = ttk.Label(detail_frame, text=text_str, font=font_to_use, style="Orange.TLabel")
                lbl.pack(side="left")
                # Bind click to select project
                lbl.bind("<Button-1>", lambda e, pid=p.id, frame=project_frame: self.select_project(pid, frame))

            # Build the line: "Priority: HIGH | Due: YYYY-MM-DD"
            add_detail_part("Priority", pixel_font)
            add_detail_part(": ", safe_font)      # Safe font for colon
            add_detail_part(priority_text, pixel_font)
            add_detail_part(" | ", safe_font)      # Safe font for pipe
            add_detail_part("Due", pixel_font)
            add_detail_part(": ", safe_font)      # Safe font for colon
            add_detail_part(p.due_date, pixel_font)
            # ---------------------------------------------------
            
            # CRITICAL: Bind selection logic (must be bound to all widgets)
            project_frame.bind("<Button-1>", lambda e, pid=p.id, frame=project_frame: self.select_project(pid, frame))
            image_label.bind("<Button-1>", lambda e, pid=p.id, frame=project_frame: self.select_project(pid, frame))
            text_frame.bind("<Button-1>", lambda e, pid=p.id, frame=project_frame: self.select_project(pid, frame))
            
            # Also bind any direct children of text_frame (like name_label and detail_frame)
            for child in text_frame.winfo_children():
                child.bind("<Button-1>", lambda e, pid=p.id, frame=project_frame: self.select_project(pid, frame))

        # 3. Update the scroll region
        self.project_display_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))