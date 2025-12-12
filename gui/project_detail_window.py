import tkinter as tk
from tkinter import ttk, PhotoImage, simpledialog, messagebox, filedialog
import os
import re 
import platform
import subprocess
from datetime import datetime

class ProjectDetailWindow:
    def __init__(self, parent, controller, project):
        self.controller = controller
        self.project = project
        self.image_refs = []
        
        # Map Attachment ID -> Widget Frame
        self.media_widgets = {} 
        
        self.current_log_id = None 
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"Project Dashboard: {project.name}")
        self.window.geometry("1100x700")
        
        self.style = ttk.Style()
        self.bg_color = self.style.lookup('TFrame', 'background')
        
        self.create_layout()
        self.load_dates()
        self.load_media()

    def create_layout(self):
        # Main Container
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill='both', expand=True)
        
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=3)
        main_frame.grid_columnconfigure(2, weight=2)
        main_frame.grid_rowconfigure(1, weight=1)

        # --- HEADERS ---
        ttk.Label(main_frame, text="Select Day", font=("EASVHS", 12, "bold"), foreground="#FFA500").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Label(main_frame, text="Log Entries", font=("EASVHS", 12, "bold"), foreground="#FFA500").grid(row=0, column=1, sticky="w", pady=5)
        ttk.Label(main_frame, text="Reference Media", font=("EASVHS", 12, "bold"), foreground="#FFA500").grid(row=0, column=2, sticky="w", pady=5)

        # --- COL 0: DATE LIST & CONTROLS ---
        date_frame = ttk.Frame(main_frame)
        date_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        
        self.date_listbox = tk.Listbox(date_frame, bg=self.bg_color, fg="white", font=("EASVHS", 11), borderwidth=0, highlightthickness=1)
        self.date_listbox.pack(side='top', fill='both', expand=True)
        self.date_listbox.bind('<<ListboxSelect>>', self.on_date_selected)
        
        # Buttons Frame
        btn_frame = ttk.Frame(date_frame)
        btn_frame.pack(side='bottom', fill='x', pady=5)
        
        ttk.Button(btn_frame, text="➕ Add Entry", command=self.add_entry_clicked).pack(fill='x', pady=2)
        ttk.Button(btn_frame, text="➖ Delete Entry", command=self.delete_date_clicked).pack(fill='x', pady=2)

        # --- COL 1: LOG ENTRIES ---
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 10))
        
        self.log_text_area = tk.Text(log_frame, bg="#3E3E3E", fg="white", font=("Consolas", 11), wrap="word", borderwidth=0)
        self.log_text_area.pack(side='top', fill='both', expand=True)
        
        save_area = ttk.Frame(log_frame)
        save_area.pack(side='bottom', fill='x', pady=(5, 0))
        
        save_btn = ttk.Button(save_area, text="💾 Save Changes to Text", command=self.save_text_clicked)
        save_btn.pack(side='left')
        
        self.status_label = ttk.Label(save_area, text="", font=("EASVHS", 10, "italic"), foreground="lightgreen")
        self.status_label.pack(side='left', padx=10)
        
        # --- COL 2: REFERENCE MEDIA (Scrollable) ---
        self.media_frame_container = ttk.Frame(main_frame)
        self.media_frame_container.grid(row=1, column=2, sticky="nsew")
        
        # 1. Add Media Button (Bottom)
        media_btn_frame = ttk.Frame(self.media_frame_container)
        media_btn_frame.pack(side='bottom', fill='x', pady=(5, 0))
        ttk.Button(media_btn_frame, text="➕ Add Media", command=self.add_media_clicked).pack(fill='x')
        
        # 2. Canvas Area (Top)
        canvas_area = ttk.Frame(self.media_frame_container)
        canvas_area.pack(side='top', fill='both', expand=True)
        
        self.media_canvas = tk.Canvas(canvas_area, bg=self.bg_color, borderwidth=0)
        media_scrollbar = ttk.Scrollbar(canvas_area, orient="vertical", command=self.media_canvas.yview)
        
        self.media_inner_frame = ttk.Frame(self.media_canvas)
        
        self.media_canvas.pack(side="left", fill="both", expand=True)
        media_scrollbar.pack(side="right", fill="y")
        
        self.media_canvas.configure(yscrollcommand=media_scrollbar.set)
        self.media_canvas.create_window((0, 0), window=self.media_inner_frame, anchor="nw")
        
        self.media_inner_frame.bind("<Configure>", lambda e: self.media_canvas.configure(scrollregion=self.media_canvas.bbox("all")))

        # --- SCROLLING LOGIC ---
        self.media_canvas.bind("<Button-4>", lambda e: self.on_mousewheel(e, 1))
        self.media_canvas.bind("<Button-5>", lambda e: self.on_mousewheel(e, -1))
        self.media_frame_container.bind('<Enter>', self._activate_scroll_binding)

    # --- SCROLL HANDLERS ---
    
    def _activate_scroll_binding(self, event):
        """Called when mouse enters the media container."""
        self.window.bind_all("<MouseWheel>", self._on_mousewheel_propagate)

    def _on_mousewheel_propagate(self, event):
        """Checks if the mouse is over the media container before scrolling."""
        widget_under_mouse = self.window.winfo_containing(event.x_root, event.y_root)
        
        if widget_under_mouse is None:
            return

        current_widget = widget_under_mouse
        while current_widget:
            if current_widget == self.media_frame_container:
                self.on_mousewheel(event)
                return "break"
            current_widget = current_widget.master
            if current_widget == self.window or current_widget is None:
                break

    def on_mousewheel(self, event, direction=None):
        if direction is not None:
            delta = direction * -1 
        elif event.delta:
            delta = event.delta
        else:
            return

        if abs(delta) >= 120:
            scroll_amount = -1 * (delta // abs(delta)) * 4
        else:
            scroll_amount = -1 * delta * 0.5 
        
        self.media_canvas.yview_scroll(int(scroll_amount), "units")

    # --- FUNCTIONALITY ---

    def add_media_clicked(self):
        from tkinter import filedialog
        # UPDATED FILTER: Allow all common inputs. 
        # The controller will convert them to PNG.
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"), 
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            is_global = messagebox.askyesno("Scope", "Make this attachment GLOBAL (visible to all projects)?\n\nYes = Global\nNo = Project Specific")
            
            # The controller now handles the conversion to PNG
            self.controller.add_attachment(file_path, self.project.id, is_global)
            
            # Reload to show the new PNG
            self.load_media()

    def load_dates(self):
        dates = self.controller.get_dates_for_project(self.project.id)
        self.date_listbox.delete(0, tk.END)
        for d in dates:
            self.date_listbox.insert(tk.END, d)
        
        if not dates:
            self.log_text_area.delete("1.0", tk.END)
            self.current_log_id = None

    def on_date_selected(self, event):
        selection = self.date_listbox.curselection()
        if not selection: return
        
        date_str = self.date_listbox.get(selection[0])
        logs = self.controller.get_logs_for_project_date(self.project.id, date_str)
        
        self.log_text_area.delete("1.0", tk.END)
        self.current_log_id = None 
        self.status_label.config(text="") 
        
        if logs:
            latest_log = logs[0]
            self.current_log_id = latest_log.id
            self.insert_text_with_links(latest_log.content)

    def insert_text_with_links(self, content):
        pattern = re.compile(r'\[ref:(\d+)\]')
        start_idx = 0
        for match in pattern.finditer(content):
            pre_text = content[start_idx:match.start()]
            self.log_text_area.insert(tk.END, pre_text)
            
            ref_id = match.group(1)
            tag_name = f"ref_{ref_id}"
            link_text = f"[ref:{ref_id}]"
            
            self.log_text_area.insert(tk.END, link_text, tag_name)
            self.log_text_area.tag_config(tag_name, foreground="#4da6ff", underline=True)
            self.log_text_area.tag_bind(tag_name, "<Button-1>", lambda e, rid=ref_id: self.highlight_media(rid))
            self.log_text_area.tag_bind(tag_name, "<Enter>", lambda e: self.log_text_area.config(cursor="hand2"))
            self.log_text_area.tag_bind(tag_name, "<Leave>", lambda e: self.log_text_area.config(cursor="arrow"))
            
            start_idx = match.end()
        self.log_text_area.insert(tk.END, content[start_idx:])

    # --- UPDATED: HIGHLIGHT & JUMP LOGIC ---
    def highlight_media(self, attachment_id):
        """Finds the media widget, Highlights it, and JUMPS (scrolls) to it."""
        try:
            att_id = int(attachment_id)
            if att_id in self.media_widgets:
                target_frame = self.media_widgets[att_id]
                
                # 1. Reset all frames
                for fid, frame in self.media_widgets.items():
                    frame.config(style="DarkList.TFrame") 
                
                # 2. Highlight Target
                self.style.configure("Highlight.TFrame", background="#555500", borderwidth=2, relief="solid")
                target_frame.config(style="Highlight.TFrame")
                
                # 3. JUMP TO WIDGET (The Scroll Fix)
                self.window.update_idletasks() # Ensure sizes are calculated
                
                # Calculate Y position of the widget inside the inner_frame
                y_coord = target_frame.winfo_y()
                canvas_height = self.media_inner_frame.winfo_height()
                visible_height = self.media_canvas.winfo_height()
                
                # Calculate the scroll fraction (0.0 to 1.0)
                if canvas_height > visible_height:
                    fraction = y_coord / canvas_height
                    self.media_canvas.yview_moveto(fraction)
                
                # 4. Remove highlight after 2 seconds
                self.window.after(2000, lambda: target_frame.config(style="DarkList.TFrame"))
                
        except ValueError:
            pass

    # --- NEW: OPEN IMAGE LOGIC ---
    def open_image_file(self, file_path):
        """Opens the image using the default OS viewer."""
        if os.path.exists(file_path):
            try:
                if platform.system() == 'Darwin':       # macOS
                    subprocess.call(('open', file_path))
                elif platform.system() == 'Windows':    # Windows
                    os.startfile(file_path)
                else:                                   # linux variants
                    subprocess.call(('xdg-open', file_path))
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {e}")
        else:
            messagebox.showwarning("File Missing", "The image file could not be found.")

    def save_text_clicked(self):
        if self.current_log_id is not None:
            content = self.log_text_area.get("1.0", "end-1c")
            self.controller.save_log_text(self.current_log_id, content)
            self.status_label.config(text="Changes saved successfully!", foreground="#00FF00")
            self.window.after(3000, lambda: self.status_label.config(text=""))
        else:
            self.status_label.config(text="Error: No log entry selected", foreground="red")
            self.window.after(3000, lambda: self.status_label.config(text=""))

    def add_entry_clicked(self):
        today = datetime.now().strftime("%Y-%m-%d")
        date_str = simpledialog.askstring("New Entry", "Enter Date (YYYY-MM-DD):", initialvalue=today, parent=self.window)
        if not date_str: return 
        
        content = simpledialog.askstring("New Entry", "Enter Log Content:", parent=self.window)
        if content:
            self.controller.add_log_entry(self.project.id, date_str, content)
            self.load_dates()

    def delete_date_clicked(self):
        selection = self.date_listbox.curselection()
        if not selection:
            messagebox.showwarning("Select Date", "Please select a date to delete.")
            return
            
        date_str = self.date_listbox.get(selection[0])
        if messagebox.askyesno("Confirm Delete", f"Delete ALL logs for {date_str}?"):
            self.controller.delete_date_logs(self.project.id, date_str)
            self.load_dates()
            self.log_text_area.delete("1.0", tk.END)
            self.current_log_id = None
            self.status_label.config(text="Date deleted.", foreground="orange")

    def load_media(self):
        attachments = self.controller.get_attachments_for_project(self.project.id)
        
        for widget in self.media_inner_frame.winfo_children():
            widget.destroy()
        
        self.media_widgets = {} 

        for att in attachments:
            if os.path.exists(att.file_path):
                # Use a Frame to hold the Image and Label
                item_frame = ttk.Frame(self.media_inner_frame, padding=5, style="DarkList.TFrame")
                item_frame.pack(fill='x', pady=5)
                
                self.media_widgets[att.id] = item_frame
                
                # ID Label
                ttk.Label(item_frame, text=f"ID: {att.id}", font=("EASVHS", 9, "bold"), foreground="gray").pack(anchor='w')
                
                # Image Label
                img_lbl = ttk.Label(item_frame)
                img_lbl.pack()
                
                # NEW: Bind click on the image to open the file
                # Use cursor="hand2" to indicate clickability
                img_lbl.bind("<Button-1>", lambda e, path=att.file_path: self.open_image_file(path))
                img_lbl.bind("<Enter>", lambda e: img_lbl.config(cursor="hand2"))
                img_lbl.bind("<Leave>", lambda e: img_lbl.config(cursor="arrow"))

                try:
                    photo = PhotoImage(file=att.file_path)
                    if photo.width() > 200:
                        photo = photo.subsample(photo.width() // 200)
                    img_lbl.config(image=photo)
                    img_lbl.image = photo 
                    self.image_refs.append(photo)
                except:
                    img_lbl.config(text="[Image Error]", foreground="red")
                
                # Filename Label (also clickable optionally)
                name_lbl = ttk.Label(item_frame, text=os.path.basename(att.file_path), font=("EASVHS", 8))
                name_lbl.pack()
                name_lbl.bind("<Button-1>", lambda e, path=att.file_path: self.open_image_file(path))