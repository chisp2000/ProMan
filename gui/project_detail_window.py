import tkinter as tk
from tkinter import ttk, PhotoImage, simpledialog, messagebox, filedialog
from tkinter import font as tkfont
import os
import re 
import platform
import subprocess
from datetime import datetime

class AdvancedLogEditor:
    def __init__(self, parent_frame, controller, get_log_id_func):
        self.controller = controller
        self.get_log_id = get_log_id_func
        
        # 1. Toolbar
        self.toolbar = ttk.Frame(parent_frame)
        self.toolbar.pack(side="top", fill="x")

        # 2. Text Area (Enabled Undo/Redo)
        self.text_area = tk.Text(parent_frame, undo=True, wrap="word", 
                                 bg="#3E3E3E", fg="white", insertbackground="white",
                                 font=("Consolas", 11), borderwidth=0, padx=10, pady=10)
        self.text_area.pack(side="top", fill="both", expand=True)

        self.setup_styles()
        self.create_buttons()
        self.setup_bindings()

    def setup_styles(self):
        f = tkfont.Font(font=self.text_area['font'])
        family, size = f.actual("family"), f.actual("size")

        self.text_area.tag_configure("bold", font=(family, size, "bold"))
        self.text_area.tag_configure("italic", font=(family, size, "italic"))
        self.text_area.tag_configure("underline", underline=True)
        self.text_area.tag_configure("strike", overstrike=True)
        self.text_area.tag_configure("code", font=("Courier New", size), background="#252525", foreground="#dcdcaa")
        self.text_area.tag_configure("list", lmargin1=20, lmargin2=40)

    def create_buttons(self):
        btn_opts = {"width": 3}
        ttk.Button(self.toolbar, text="B", command=self.toggle_bold, **btn_opts).pack(side="left")
        ttk.Button(self.toolbar, text="I", command=self.toggle_italic, **btn_opts).pack(side="left")
        ttk.Button(self.toolbar, text="U", command=self.toggle_underline, **btn_opts).pack(side="left")
        ttk.Button(self.toolbar, text="S", command=self.toggle_strike, **btn_opts).pack(side="left")
        ttk.Button(self.toolbar, text="{ }", command=self.toggle_code, **btn_opts).pack(side="left", padx=(10, 0))
        ttk.Button(self.toolbar, text="•", command=self.add_bullet, **btn_opts).pack(side="left")

    def setup_bindings(self):
        # Formatting
        self.text_area.bind("<Control-b>", lambda e: self.toggle_bold())
        self.text_area.bind("<Control-i>", lambda e: self.toggle_italic())
        self.text_area.bind("<Control-u>", lambda e: self.toggle_underline())
        
        # Save Logic
        self.text_area.bind("<Control-s>", lambda e: self.db_save())
        self.text_area.bind("<Control-S>", lambda e: self.file_save_as()) # Ctrl+Shift+S

    def _apply_tag(self, tag):
        try:
            if self.text_area.tag_ranges("sel"):
                if tag in self.text_area.tag_names("sel.first"):
                    self.text_area.tag_remove(tag, "sel.first", "sel.last")
                else:
                    self.text_area.tag_add(tag, "sel.first", "sel.last")
        except tk.TclError: pass
        return "break"

    def toggle_bold(self): return self._apply_tag("bold")
    def toggle_italic(self): return self._apply_tag("italic")
    def toggle_underline(self): return self._apply_tag("underline")
    def toggle_strike(self): return self._apply_tag("strike")
    def toggle_code(self): return self._apply_tag("code")
    
    def add_bullet(self):
        self.text_area.insert("insert", " • ", "list")
        return "break"

    def db_save(self):
        log_id = self.get_log_id()
        if log_id:
            content = self.text_area.get("1.0", "end-1c")
            self.controller.save_log_text(log_id, content)
            messagebox.showinfo("Saved", "Log saved to database.")
        return "break"

    def file_save_as(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
            filetypes=[("Text Documents", "*.txt"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.text_area.get("1.0", tk.END))
        return "break"

class ProjectDetailWindow:
    def __init__(self, parent, controller, project):
        self.controller = controller
        self.project = project
        self.image_refs = []
        self.media_widgets = {} 
        self.last_selected_id = None
        self.current_log_id = None 
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"Project Dashboard: {project.name}")
        self.window.geometry("1100x700")
        
        self.style = ttk.Style()
        self.bg_color = self.style.lookup('TFrame', 'background')
        self.style.configure("SelectedMedia.TFrame", background="#005a9e", relief="solid", borderwidth=1)
        
        self.create_layout()
        self.load_dates()
        self.load_media()

    def create_layout(self):
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill='both', expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=3)
        main_frame.grid_columnconfigure(2, weight=2)
        main_frame.grid_rowconfigure(1, weight=1)

        # HEADERS
        ttk.Label(main_frame, text="Select Day", font=("EASVHS", 12, "bold"), foreground="#FFA500").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Label(main_frame, text="Log Entries", font=("EASVHS", 12, "bold"), foreground="#FFA500").grid(row=0, column=1, sticky="w", pady=5)
        ttk.Label(main_frame, text="Reference Media", font=("EASVHS", 12, "bold"), foreground="#FFA500").grid(row=0, column=2, sticky="w", pady=5)

        # COL 0: DATE LIST
        date_frame = ttk.Frame(main_frame)
        date_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self.date_listbox = tk.Listbox(date_frame, bg=self.bg_color, fg="white", font=("EASVHS", 11), borderwidth=0, highlightthickness=1)
        self.date_listbox.pack(side='top', fill='both', expand=True)
        self.date_listbox.bind('<<ListboxSelect>>', self.on_date_selected)
        
        btn_frame = ttk.Frame(date_frame)
        btn_frame.pack(side='bottom', fill='x', pady=5)
        ttk.Button(btn_frame, text="➕ Add Entry", command=self.add_entry_clicked).pack(fill='x', pady=2)
        ttk.Button(btn_frame, text="➖ Delete Entry", command=self.delete_date_clicked).pack(fill='x', pady=2)

        # COL 1: LOG ENTRIES (INTEGRATED ADVANCED EDITOR)
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 10))
        
        # Instantiate Advanced Editor
        self.editor = AdvancedLogEditor(log_frame, self.controller, lambda: self.current_log_id)
        self.log_text_area = self.editor.text_area # Map for existing logic compatibility

        save_area = ttk.Frame(log_frame)
        save_area.pack(side='bottom', fill='x', pady=(5, 0))
        ttk.Button(save_area, text="💾 Save to DB (Ctrl+S)", command=self.editor.db_save).pack(side='left')
        self.status_label = ttk.Label(save_area, text="", font=("EASVHS", 10, "italic"), foreground="lightgreen")
        self.status_label.pack(side='left', padx=10)
        
        # COL 2: MEDIA
        self.media_frame_container = ttk.Frame(main_frame)
        self.media_frame_container.grid(row=1, column=2, sticky="nsew")
        media_btn_frame = ttk.Frame(self.media_frame_container)
        media_btn_frame.pack(side='bottom', fill='x', pady=(5, 0))
        ttk.Button(media_btn_frame, text="➕ Add Files (Img/Vid/Doc)", command=self.add_media_clicked).pack(fill='x')
        
        canvas_area = ttk.Frame(self.media_frame_container)
        canvas_area.pack(side='top', fill='both', expand=True)
        self.media_canvas = tk.Canvas(canvas_area, bg=self.bg_color, borderwidth=0, highlightthickness=0)
        media_scrollbar = ttk.Scrollbar(canvas_area, orient="vertical", command=self.media_canvas.yview)
        self.media_inner_frame = ttk.Frame(self.media_canvas)
        self.media_canvas.pack(side="left", fill="both", expand=True)
        media_scrollbar.pack(side="right", fill="y")
        self.media_canvas.configure(yscrollcommand=media_scrollbar.set)
        self.media_canvas.create_window((0, 0), window=self.media_inner_frame, anchor="nw")
        self.media_inner_frame.bind("<Configure>", lambda e: self.media_canvas.configure(scrollregion=self.media_canvas.bbox("all")))

        self.media_canvas.bind("<Button-4>", lambda e: self.on_mousewheel(e, 1))
        self.media_canvas.bind("<Button-5>", lambda e: self.on_mousewheel(e, -1))
        self.media_frame_container.bind('<Enter>', self._activate_scroll_binding)

    def select_media_item(self, attachment_id):
        for att_id, frame in self.media_widgets.items():
            frame.config(style="DarkList.TFrame")
            for child in frame.winfo_children():
                if isinstance(child, (ttk.Label, tk.Label)): child.configure(background=self.bg_color)

        if attachment_id in self.media_widgets:
            target_frame = self.media_widgets[attachment_id]
            target_frame.config(style="SelectedMedia.TFrame")
            for child in target_frame.winfo_children():
                if isinstance(child, (ttk.Label, tk.Label)): child.configure(background="#005a9e")
            self.last_selected_id = attachment_id

    def open_any_file(self, file_path):
        if not os.path.exists(file_path):
            messagebox.showwarning("File Missing", "The file could not be found.")
            return
        curr_os = platform.system()
        try:
            if curr_os == 'Darwin': subprocess.call(('open', file_path))
            elif curr_os == 'Windows': os.startfile(file_path)
            else: subprocess.call(('xdg-open', file_path))
        except Exception as e: messagebox.showerror("Error", f"Could not open file: {e}")

    def load_media(self):
        attachments = self.controller.get_attachments_for_project(self.project.id)
        for widget in self.media_inner_frame.winfo_children(): widget.destroy()
        self.media_widgets, self.image_refs = {}, []

        for att in attachments:
            if not os.path.exists(att.file_path): continue
            item_frame = ttk.Frame(self.media_inner_frame, padding=5, style="DarkList.TFrame")
            item_frame.pack(fill='x', pady=2, padx=5)
            self.media_widgets[att.id] = item_frame
            ext = os.path.splitext(att.file_path)[1].lower()

            if ext in ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif']:
                display_label = tk.Label(item_frame, bg=self.bg_color)
                try:
                    photo = PhotoImage(file=att.file_path)
                    if photo.width() > 180: photo = photo.subsample(photo.width() // 180)
                    display_label.config(image=photo); display_label.image = photo; self.image_refs.append(photo)
                except: display_label.config(text="[Image Error]", fg="red")
            else:
                icon = "📄"
                if ext in ['.mp4', '.avi', '.mov']: icon = "🎥"
                elif ext in ['.xlsx', '.xls', '.csv']: icon = "📊"
                elif ext in ['.docx', '.doc', '.pdf']: icon = "📝"
                display_label = tk.Label(item_frame, text=f"{icon}\n{ext.upper()}", font=("Consolas", 14, "bold"), bg=self.bg_color, fg="white", pady=10)
            
            display_label.pack(pady=5)
            tk.Label(item_frame, text=f"ID: {att.id}", font=("EASVHS", 8), bg=self.bg_color, fg="gray").pack()
            tk.Label(item_frame, text=os.path.basename(att.file_path), font=("EASVHS", 9), bg=self.bg_color, fg="white", wraplength=180).pack()

            def bind_item(widget, aid=att.id, path=att.file_path):
                widget.bind("<Button-1>", lambda e: self.select_media_item(aid))
                widget.bind("<Double-Button-1>", lambda e: (self.open_any_file(path), "break")[1])
                for child in widget.winfo_children(): bind_item(child, aid, path)
            bind_item(item_frame)

        self.media_inner_frame.update_idletasks()
        self.media_canvas.config(scrollregion=self.media_canvas.bbox("all"))

    def _activate_scroll_binding(self, event): self.window.bind_all("<MouseWheel>", self._on_mousewheel_propagate)

    def _on_mousewheel_propagate(self, event):
        widget = self.window.winfo_containing(event.x_root, event.y_root)
        while widget:
            if widget == self.media_frame_container: self.on_mousewheel(event); return "break"
            widget = widget.master

    def on_mousewheel(self, event, direction=None):
        if direction: delta = direction * -1
        elif event.delta: delta = event.delta
        else: return
        amt = -1 * (delta // abs(delta)) * 4 if abs(delta) >= 120 else -1 * delta * 0.5
        self.media_canvas.yview_scroll(int(amt), "units")

    def add_media_clicked(self):
        file_path = filedialog.askopenfilename(filetypes=[("All Supported", "*.png *.jpg *.jpeg *.mp4 *.avi *.docx *.xlsx *.ppt *.mp3 *.wav"), ("All Files", "*.*")])
        if file_path:
            is_global = messagebox.askyesno("Scope", "Make this attachment GLOBAL?")
            self.controller.add_attachment(file_path, self.project.id, is_global)
            self.load_media()

    def highlight_media(self, attachment_id):
        try:
            aid = int(attachment_id)
            if aid in self.media_widgets:
                self.select_media_item(aid)
                y = self.media_widgets[aid].winfo_y()
                h = self.media_inner_frame.winfo_height()
                if h > self.media_canvas.winfo_height(): self.media_canvas.yview_moveto(y/h)
        except: pass

    def load_dates(self):
        dates = self.controller.get_dates_for_project(self.project.id)
        self.date_listbox.delete(0, tk.END)
        for d in dates: self.date_listbox.insert(tk.END, d)

    def on_date_selected(self, event):
        sel = self.date_listbox.curselection()
        if not sel: return
        date_str = self.date_listbox.get(sel[0])
        logs = self.controller.get_logs_for_project_date(self.project.id, date_str)
        self.log_text_area.delete("1.0", tk.END)
        if logs:
            self.current_log_id = logs[0].id
            self.insert_text_with_links(logs[0].content)

    def insert_text_with_links(self, content):
        pattern = re.compile(r'\[ref:(\d+)\]')
        start_idx = 0
        for match in pattern.finditer(content):
            self.log_text_area.insert(tk.END, content[start_idx:match.start()])
            tag = f"ref_{match.group(1)}"
            self.log_text_area.insert(tk.END, f"[ref:{match.group(1)}]", tag)
            self.log_text_area.tag_config(tag, foreground="#4da6ff", underline=True)
            self.log_text_area.tag_bind(tag, "<Button-1>", lambda e, rid=match.group(1): self.highlight_media(rid))
            start_idx = match.end()
        self.log_text_area.insert(tk.END, content[start_idx:])

    def save_text_clicked(self): self.editor.db_save()

    def add_entry_clicked(self):
        date_str = simpledialog.askstring("New Entry", "Date (YYYY-MM-DD):", initialvalue=datetime.now().strftime("%Y-%m-%d"))
        if date_str:
            content = simpledialog.askstring("New Entry", "Log Content:")
            if content: self.controller.add_log_entry(self.project.id, date_str, content); self.load_dates()

    def delete_date_clicked(self):
        sel = self.date_listbox.curselection()
        if sel:
            date_str = self.date_listbox.get(sel[0])
            if messagebox.askyesno("Confirm", f"Delete logs for {date_str}?"):
                self.controller.delete_date_logs(self.project.id, date_str); self.load_dates()