import tkinter as tk
from tkinter import ttk, PhotoImage, simpledialog, messagebox, filedialog
from tkinter import font as tkfont
import os
import re 
import platform
import subprocess
import json
from datetime import datetime
from PIL import Image, ImageTk

mainFont = "Helvetica"

# --- HOVER TIP CLASS ---
class HoverTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text: return
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=self.text, justify='left', background="#ffffe0", 
                 relief='solid', borderwidth=1, font=("tahoma", "8", "normal")).pack(ipadx=1)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

# --- NEW ENTRY DIALOG ---
class NewEntryDialog:
    def __init__(self, parent, templates):
        self.result = None
        self.templates = templates
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add New Entry")
        self.dialog.geometry("350x250")
        self.dialog.grab_set()
        main_f = ttk.Frame(self.dialog, padding=20)
        main_f.pack(fill='both', expand=True)
        ttk.Label(main_f, text="Date (YYYY-MM-DD):").pack(anchor='w')
        self.date_entry = ttk.Entry(main_f)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.pack(fill='x', pady=(0, 15))
        ttk.Label(main_f, text="Select Template:").pack(anchor='w')
        template_names = ["None"] + [t['name'] for t in templates]
        self.combo = ttk.Combobox(main_f, values=template_names, state="readonly")
        self.combo.current(0)
        self.combo.pack(fill='x', pady=(0, 20))
        btn_f = ttk.Frame(main_f)
        btn_f.pack(fill='x')
        ttk.Button(btn_f, text="Confirm", command=self.on_confirm).pack(side='left', expand=True, fill='x', padx=2)
        ttk.Button(btn_f, text="Cancel", command=self.dialog.destroy).pack(side='left', expand=True, fill='x', padx=2)

    def on_confirm(self):
        date = self.date_entry.get()
        sel_name = self.combo.get()
        content = ""
        if sel_name != "None":
            for t in self.templates:
                if t['name'] == sel_name:
                    content = t['content']
                    break
        self.result = (date, content)
        self.dialog.destroy()

class AdvancedLogEditor:
    def __init__(self, parent_frame, controller, get_log_id_func, status_label, highlight_callback, ref_callback=None):
        self.controller = controller
        self.get_log_id = get_log_id_func
        self.status_label = status_label
        self.highlight_callback = highlight_callback
        self.ref_callback = ref_callback
        
        self.main_container = ttk.Frame(parent_frame)
        self.main_container.pack(fill='both', expand=True)
        
        self.toolbar = ttk.Frame(self.main_container)
        self.toolbar.pack(side="top", fill="x")

        self.text_frame = ttk.Frame(self.main_container)
        self.text_frame.pack(side="top", fill="both", expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.text_frame, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")

        self.text_area = tk.Text(self.text_frame, undo=True, wrap="word", 
                                 bg="#3E3E3E", fg="white", insertbackground="white",
                                 font=("Consolas", 11), borderwidth=0, padx=10, pady=10,
                                 yscrollcommand=self.scrollbar.set, 
                                 selectbackground="#cfcfcf",
                                 selectforeground="black")
        self.text_area.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.text_area.yview)

        # Updated bind to handle both section highlighting and link clicking
        self.text_area.bind("<Button-1>", self._handle_click)

        self.setup_styles()
        self.create_buttons()
        self.setup_bindings()

    def _handle_click(self, event):
        self.highlight_callback("editor")
        # Check for [ref:x] tags at click location
        index = self.text_area.index(f"@{event.x},{event.y}")
        tags = self.text_area.tag_names(index)
        if "ref_link" in tags:
            # Find the full range of this specific tag
            ranges = self.text_area.tag_prevrange("ref_link", index + " + 1c")
            if ranges:
                text = self.text_area.get(*ranges)
                match = re.search(r"ref:(\d+)", text)
                if match and self.ref_callback:
                    self.ref_callback(int(match.group(1)))

    def setup_styles(self):
        f = tkfont.Font(font=self.text_area['font'])
        family, size = f.actual("family"), f.actual("size")
        self.text_area.tag_configure("bold", font=(family, size, "bold"))
        self.text_area.tag_configure("italic", font=(family, size, "italic"))
        self.text_area.tag_configure("underline", underline=True)
        self.text_area.tag_configure("strike", overstrike=True)
        self.text_area.tag_configure("code", font=("Courier New", size), background="#252525", foreground="#dcdcaa")
        self.text_area.tag_configure("list", lmargin1=20, lmargin2=40)
        
        # Style for references: matches listbox selection grey instead of standard blue
        self.text_area.tag_configure("ref_link", foreground="#5fff7a", underline=True, font=(family, size, "bold"))
        self.text_area.tag_bind("ref_link", "<Enter>", lambda e: self.text_area.config(cursor="hand2"))
        self.text_area.tag_bind("ref_link", "<Leave>", lambda e: self.text_area.config(cursor="xterm"))

    def scan_for_refs(self):
        self.text_area.tag_remove("ref_link", "1.0", tk.END)
        content = self.text_area.get("1.0", tk.END)
        for match in re.finditer(r"\[ref:\d+\]", content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.text_area.tag_add("ref_link", start, end)

    def create_buttons(self):
        btn_opts = {"width": 3}
        for tag, txt, tip in [("bold", "B", "Bold (Ctrl+B)"), ("italic", "I", "Italic (Ctrl+I)"), 
                             ("underline", "U", "Underline (Ctrl+U)"), ("strike", "S", "Strike")]:
            btn = ttk.Button(self.toolbar, text=txt, command=lambda t=tag: self._apply_tag(t), **btn_opts)
            btn.pack(side="left"); HoverTip(btn, tip)
        c = ttk.Button(self.toolbar, text="{ }", command=lambda: self._apply_tag("code"), **btn_opts)
        c.pack(side="left", padx=(10,0)); HoverTip(c, "Code Block")
        l = ttk.Button(self.toolbar, text="•", command=self.add_bullet, **btn_opts)
        l.pack(side="left"); HoverTip(l, "Bullet Point")

    def setup_bindings(self):
        self.text_area.bind("<Control-b>", lambda e: self._apply_tag("bold"))
        self.text_area.bind("<Control-i>", lambda e: self._apply_tag("italic"))
        self.text_area.bind("<Control-u>", lambda e: self._apply_tag("underline"))
        self.text_area.bind("<Control-s>", lambda e: self.db_save())

    def _apply_tag(self, tag):
        self.highlight_callback("editor")
        try:
            if self.text_area.tag_ranges("sel"):
                if tag in self.text_area.tag_names("sel.first"):
                    self.text_area.tag_remove(tag, "sel.first", "sel.last")
                else:
                    self.text_area.tag_add(tag, "sel.first", "sel.last")
            self.scan_for_refs() # Rescan to ensure links aren't broken by styling
        except tk.TclError: pass
        return "break"

    def add_bullet(self):
        self.highlight_callback("editor")
        self.text_area.insert("insert", " • ", "list")
        return "break"

    def db_save(self):
        log_id = self.get_log_id()
        if log_id:
            raw_text = self.text_area.get("1.0", "end-1c")
            tag_data = [{"tag": t, "ranges": [str(r) for r in self.text_area.tag_ranges(t)]} 
                        for t in ["bold", "italic", "underline", "strike", "code", "list"]]
            self.controller.save_log_text(log_id, json.dumps({"text": raw_text, "tags": tag_data}))
            
            old_status = self.status_label.cget("text")
            self.status_label.config(text="✔ Saved to Database", foreground="lightgreen")
            self.status_label.after(2000, lambda: self.status_label.config(text=old_status, foreground="white"))
        return "break"

    def load_formatted_text(self, content):
        self.text_area.delete("1.0", tk.END)
        if not content: return
        try:
            data = json.loads(content)
            self.text_area.insert("1.0", data["text"])
            for item in data["tags"]:
                for i in range(0, len(item["ranges"]), 2): 
                    self.text_area.tag_add(item["tag"], item["ranges"][i], item["ranges"][i+1])
        except (json.JSONDecodeError, TypeError, KeyError):
            self.text_area.insert("1.0", str(content))
        
        self.scan_for_refs() # Detect links on load
        self.text_area.edit_reset()

class ProjectDetailWindow:
    def __init__(self, parent, controller, project):
        self.controller, self.project = controller, project
        self.persistent_image_cache = [] 
        self.media_tile_widgets = []
        self.current_log_id = None
        self.active_section = "editor" 
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"Dashboard: {project.name}")
        self.window.geometry("1150x750")
        
        self.bg_color = ttk.Style().lookup('TFrame', 'background')
        self.create_layout()
        self.load_dates()
        self.load_media()

    def create_layout(self):
        self.style = ttk.Style()
        self.style.configure("SelectedTile.TFrame", background="#E0E0E0")
        self.style.configure("Card.TFrame", background="#333333")

        main_frame = ttk.Frame(self.window, padding=5)
        main_frame.pack(fill='both', expand=True)
        
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=3)
        main_frame.grid_columnconfigure(2, weight=4) 
        main_frame.grid_rowconfigure(1, weight=1)

        ttk.Label(main_frame, text="Log Entries", font=(mainFont, 11, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(main_frame, text="Editor", font=(mainFont, 11, "bold")).grid(row=0, column=1, sticky="w")
        ttk.Label(main_frame, text="Reference Media", font=(mainFont, 11, "bold")).grid(row=0, column=2, sticky="w")

        # --- LEFT: Entries List ---
        self.df = tk.Frame(main_frame, bg=self.bg_color, highlightthickness=2)
        self.df.grid(row=1, column=0, sticky="nsew", padx=5)
        
        self.date_listbox = tk.Listbox(self.df, bg=self.bg_color, fg="white", font=(mainFont, 10), 
                                       borderwidth=0, highlightthickness=0,
                                       selectbackground="#cfcfcf", selectforeground="black")
        self.date_listbox.pack(fill='both', expand=True)
        self.date_listbox.bind('<<ListboxSelect>>', self.on_date_selected)
        
        entry_btn_frame = ttk.Frame(self.df)
        entry_btn_frame.pack(fill='x', pady=0) 
        ttk.Button(entry_btn_frame, text="➕ Add Entry", command=self.add_entry_clicked).pack(side='left', expand=True, fill='x', padx=1)
        ttk.Button(entry_btn_frame, text="➖ Remove Entry", command=self.delete_entry_clicked).pack(side='left', expand=True, fill='x', padx=1)

        self.df.bind("<Button-1>", lambda e: self.highlight_window("dates"))
        self.date_listbox.bind("<Button-1>", lambda e: self.highlight_window("dates"))

        # --- CENTER: Editor ---
        self.lf = tk.Frame(main_frame, bg=self.bg_color, highlightthickness=2)
        self.lf.grid(row=1, column=1, sticky="nsew", padx=5)
        self.lf.bind("<Button-1>", lambda e: self.highlight_window("editor"))
        
        editor_bottom_bar = ttk.Frame(self.lf)
        editor_bottom_bar.pack(side='bottom', fill='x', pady=0)
        
        self.save_btn = ttk.Button(editor_bottom_bar, text="💾 Save Log", command=lambda: self.editor.db_save())
        self.save_btn.pack(side='left') 

        self.export_btn = ttk.Button(editor_bottom_bar, text="📤 Export Log", command=self.export_log_as_txt)
        self.export_btn.pack(side='left', padx=(5, 0))

        self.status_label = ttk.Label(editor_bottom_bar, text="", font=("Arial", 9, "italic"))
        self.status_label.pack(side='left', padx=10)

        # Passed select_tile_by_id as the ref_callback
        self.editor = AdvancedLogEditor(self.lf, self.controller, lambda: self.current_log_id, 
                                        self.status_label, self.highlight_window, 
                                        ref_callback=self.select_tile_by_id)

        # --- RIGHT: Media ---
        self.mfc = tk.Frame(main_frame, bg=self.bg_color, highlightthickness=2)
        self.mfc.grid(row=1, column=2, sticky="nsew", padx=5)
        self.mfc.bind("<Button-1>", lambda e: self.highlight_window("media"))
        
        media_btn_container = ttk.Frame(self.mfc, padding=0)
        media_btn_container.pack(side='bottom', fill='x', pady=0)
        ttk.Button(media_btn_container, text="➕ Add Media Files", command=self.add_media_clicked).pack(side='left', fill='x', expand=True) 

        canvas_group = tk.Frame(self.mfc, bg=self.bg_color)
        canvas_group.pack(side='top', fill='both', expand=True)
        self.media_canvas = tk.Canvas(canvas_group, bg=self.bg_color, highlightthickness=0)
        self.media_scrollbar = ttk.Scrollbar(canvas_group, orient="vertical", command=self.media_canvas.yview)
        self.media_scrollbar.pack(side="right", fill="y")
        self.media_canvas.pack(side="left", fill="both", expand=True)
        self.media_canvas.configure(yscrollcommand=self.media_scrollbar.set)
        
        self.media_canvas.bind("<Button-1>", lambda e: self.highlight_window("media"))
        self.media_canvas.bind("<Configure>", self.reformat_tiles)

        self.window.bind_all("<MouseWheel>", self._unified_scroller)

    def select_tile_by_id(self, attachment_id):
        """Finds, highlights, and jumps the scroll view to the matching tile."""
        attachments = self.controller.get_attachments_for_project(self.project.id)
        target_tile = None
        
        # 1. Identify the tile widget
        for i, att in enumerate(attachments):
            if att.id == attachment_id:
                if i < len(self.media_tile_widgets):
                    target_tile = self.media_tile_widgets[i]
                    break
        
        if target_tile:
            # 2. Apply the highlight
            self.select_tile(attachment_id, target_tile)
            
            # 3. Force the jump (Scroll)
            self.media_canvas.update_idletasks()
            
            # Get the position of the tile relative to the entire scrollable area
            # 'tile_window' is the tag we used in reformat_tiles
            all_items = self.media_canvas.find_withtag("tile_window")
            for item in all_items:
                if self.media_canvas.itemcget(item, "window") == str(target_tile):
                    # Get the coordinates (x1, y1, x2, y2) of this window item in the canvas
                    coords = self.media_canvas.coords(item)
                    y_position = coords[1] # This is the top Y coordinate
                    
                    # Get total scrollable height
                    scroll_bbox = self.media_canvas.bbox("all")
                    if scroll_bbox:
                        total_height = scroll_bbox[3]
                        # Move view so the tile is at the top of the visible area
                        fraction = y_position / total_height
                        self.media_canvas.yview_moveto(fraction)
                    break

    def _unified_scroller(self, event):
        direction = int(-1 * (event.delta / 120))
        if self.active_section == "dates":
            self.date_listbox.yview_scroll(direction, "units")
        elif self.active_section == "editor":
            self.editor.text_area.yview_scroll(direction, "units")
        elif self.active_section == "media":
            curr = self.media_canvas.yview()
            if curr[0] <= 0 and direction < 0: return "break"
            self.media_canvas.yview_scroll(direction, "units")

    def highlight_window(self, section):
        self.active_section = section
        self.df.config(highlightbackground="#FFFFFF" if section == "dates" else "#222222")
        self.lf.config(highlightbackground="#FFFFFF" if section == "editor" else "#222222")
        self.mfc.config(highlightbackground="#FFFFFF" if section == "media" else "#222222")
        if section == "dates": self.date_listbox.focus_set()
        elif section == "editor": self.editor.text_area.focus_set()
        elif section == "media": self.media_canvas.focus_set()

    def delete_entry_clicked(self):
        self.highlight_window("dates")
        sel = self.date_listbox.curselection()
        if not sel:
            messagebox.showwarning("Selection", "Choose an entry to remove first.")
            return
        entry_val = self.date_listbox.get(sel[0])
        if messagebox.askyesno("Confirm", f"Permanently delete entry: {entry_val}?"):
            self.controller.delete_date_logs(self.project.id, entry_val)
            self.editor.text_area.delete("1.0", tk.END)
            self.current_log_id = None
            self.status_label.config(text="")
            self.load_dates()

    def select_tile(self, attachment_id, target_frame):
        self.highlight_window("media") 
        for tile in self.media_tile_widgets:
            tile.configure(style="Card.TFrame")
            for child in tile.winfo_children():
                if isinstance(child, tk.Label): child.configure(bg="#333333", fg="white")
        target_frame.configure(style="SelectedTile.TFrame")
        for child in target_frame.winfo_children():
            if isinstance(child, tk.Label): child.configure(bg="#E0E0E0", fg="black")

    def export_log_as_txt(self):
        content = self.editor.text_area.get("1.0", "end-1c")
        if not content.strip():
            self.status_label.config(text="⚠ Export Failed: No content", foreground="orange")
            return

        sel = self.date_listbox.curselection()
        date_str = self.date_listbox.get(sel[0]) if sel else "export"
        default_name = f"Log_{date_str}.txt"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default_name,
            title="Export Log as Text"
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.status_label.config(text=f"✔ Exported to {os.path.basename(file_path)}", foreground="lightgreen")
                self.window.after(3000, lambda: self.status_label.config(
                    text=f"Editing: {date_str}" if sel else "", 
                    foreground="white"))
            except Exception as e:
                self.status_label.config(text=f"❌ Export Error: {str(e)[:20]}...", foreground="red")

    def load_media(self):
        self.media_tile_widgets, self.persistent_image_cache = [], []
        attachments = self.controller.get_attachments_for_project(self.project.id)
        for att in attachments:
            full_path = os.path.abspath(att.file_path)
            if not os.path.exists(full_path): continue
            tile = ttk.Frame(self.media_canvas, padding=2, style="Card.TFrame", width=160, height=180)
            tile.pack_propagate(False) 
            ext = os.path.splitext(full_path)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg', '.webp']:
                try:
                    img = Image.open(full_path); img.thumbnail((140, 120))
                    photo = ImageTk.PhotoImage(img); self.persistent_image_cache.append(photo)
                    content = tk.Label(tile, image=photo, bg="#333333")
                except: content = tk.Label(tile, text="[Error]", fg="red", bg="#333333")
            else:
                content = tk.Label(tile, text=f"📄 {ext.upper()}", font=("Arial", 20), bg="#333333", fg="white")
            content.pack(pady=5)
            tk.Label(tile, text=os.path.basename(full_path), font=("Arial", 8), wraplength=140, bg="#333333", fg="white").pack()

            def bind_tree(widget, aid=att.id, path=full_path, t_frame=tile):
                widget.bind("<Button-1>", lambda e: self.select_tile(aid, t_frame))
                widget.bind("<Double-Button-1>", lambda e: self.open_any_file(path))
                for child in widget.winfo_children(): bind_tree(child, aid, path, t_frame)
            bind_tree(tile)
            self.media_tile_widgets.append(tile)
        self.reformat_tiles()

    def reformat_tiles(self, event=None):
        self.media_canvas.delete("tile_window")
        w = self.media_canvas.winfo_width()
        if w < 50: return 
        self.media_canvas.yview_moveto(0)
        pad, tw, th = 15, 160, 180
        cols = max(1, (w - pad) // (tw + pad))
        for i, tile in enumerate(self.media_tile_widgets):
            r, c = i // cols, i % cols
            self.media_canvas.create_window(c*(tw+pad)+pad, r*(th+pad)+pad, window=tile, anchor="nw", tags="tile_window")
        self.media_canvas.update_idletasks()
        bbox = self.media_canvas.bbox("all")
        self.media_canvas.config(scrollregion=(0, 0, bbox[2], bbox[3]+pad) if bbox else (0,0,0,0))

    def add_media_clicked(self):
        f = filedialog.askopenfilename()
        if f and self.controller.add_attachment(f, self.project.id, False): self.load_media()

    def open_any_file(self, path):
        if not os.path.exists(path): return
        if platform.system() == 'Windows': os.startfile(path)
        else: subprocess.call(('open' if platform.system() == 'Darwin' else 'xdg-open', path))

    def load_dates(self):
        self.date_listbox.delete(0, tk.END)
        for d in self.controller.get_dates_for_project(self.project.id): self.date_listbox.insert(tk.END, d)

    def on_date_selected(self, event):
        self.highlight_window("dates")
        sel = self.date_listbox.curselection()
        if not sel: return
        date_str = self.date_listbox.get(sel[0])
        logs = self.controller.get_logs_for_project_date(self.project.id, date_str)
        if logs:
            self.current_log_id = logs[0].id
            self.editor.load_formatted_text(logs[0].content)
            self.status_label.config(text=f"Editing: {date_str}", foreground="white")
        else:
            self.current_log_id = None
            self.editor.text_area.delete("1.0", tk.END)
            self.status_label.config(text="No log found", foreground="gray")

    def add_entry_clicked(self):
        dialog = NewEntryDialog(self.window, self.controller.db_controller.get_all_templates())
        self.window.wait_window(dialog.dialog)
        if dialog.result:
            self.controller.add_log_entry(self.project.id, dialog.result[0], dialog.result[1])
            self.load_dates()