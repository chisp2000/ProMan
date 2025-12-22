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

# ==========================================
# CONFIGURATION / THEME VARIABLES
# ==========================================
MAIN_FONT = "Helvetica"
EDITOR_FONT = "Consolas"
HEADER_FONT_SIZE = 11
DATE_HEADER_SIZE = 12
NORMAL_FONT_SIZE = 10

# Colors
DARK_BG = "#1C1C1C"
EDITOR_BG = "#3E3E3E"
TEXT_FG = "white"
ACCENT_GREEN = "#5fff7a"
ACCENT_RED = "#ff5f5f"
ACCENT_ORANGE = "white" 
BORDER_DARK = "#222222"
BORDER_HIGHLIGHT = "#FFFFFF"
SELECT_BG = "#cfcfcf"
DATE_ROW_BG = "#252525"
# ==========================================

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
                                 bg=EDITOR_BG, fg=TEXT_FG, insertbackground=TEXT_FG,
                                 font=(EDITOR_FONT, 11), borderwidth=0, padx=10, pady=10,
                                 yscrollcommand=self.scrollbar.set, 
                                 selectbackground=SELECT_BG,
                                 selectforeground="black")
        self.text_area.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.text_area.yview)

        self.text_area.bind("<Button-1>", self._handle_click)

        self.setup_styles()
        self.create_buttons()
        self.setup_bindings()

    def _handle_click(self, event):
        self.highlight_callback("editor")
        index = self.text_area.index(f"@{event.x},{event.y}")
        tags = self.text_area.tag_names(index)
        if "ref_link" in tags:
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
        
        self.text_area.tag_configure("ref_link", foreground=ACCENT_GREEN, underline=True, font=(family, size, "bold"))
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
            self.scan_for_refs()
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
        
        self.scan_for_refs()
        self.text_area.edit_reset()

class FinanceEditor:
    def __init__(self, parent_frame, controller, project_id, status_label):
        self.controller = controller
        self.project_id = project_id
        self.status_label = status_label
        
        self.container = ttk.Frame(parent_frame)
        
        # --- TOOLBAR WITH BUDGET INPUT ---
        self.toolbar = ttk.Frame(self.container)
        self.toolbar.pack(side="top", fill="x", pady=2)
        
        ttk.Button(self.toolbar, text="➕ Add Row", command=self.add_row).pack(side="left", padx=2)
        ttk.Button(self.toolbar, text="➖ Remove Row", command=self.remove_row).pack(side="left", padx=2)
        
        ttk.Label(self.toolbar, text="Budget: $").pack(side="left", padx=(15, 2))
        self.budget_var = tk.StringVar(value="0.00")
        self.budget_entry = ttk.Entry(self.toolbar, textvariable=self.budget_var, width=10)
        self.budget_entry.pack(side="left")
        self.budget_entry.bind("<Return>", lambda e: self._update_grand_total())

        ttk.Button(self.toolbar, text="💾 Save", command=self.save_data).pack(side="right", padx=2)

        # Spreadsheet Style Treeview
        columns = ("id", "desc", "qty", "price", "link")
        self.tree = ttk.Treeview(self.container, columns=columns, show='headings', selectmode='browse')
        
        style = ttk.Style()
        style.configure("Treeview.Heading", font=(MAIN_FONT, HEADER_FONT_SIZE, "bold"))
        self.tree.tag_configure('date_row', background=DATE_ROW_BG, foreground=ACCENT_ORANGE, font=(MAIN_FONT, DATE_HEADER_SIZE, 'bold'))

        self.tree.heading("id", text="Item ID")
        self.tree.heading("desc", text="Item Desc.")
        self.tree.heading("qty", text="Quantity")
        self.tree.heading("price", text="Price")
        self.tree.heading("link", text="Link")
        
        self.tree.column("id", width=120, anchor="w")
        self.tree.column("qty", width=70, anchor="center")
        self.tree.column("price", width=100, anchor="e")
        
        self.tree.pack(fill='both', expand=True)
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # KEYBIND: Ctrl+S for internal save logic
        self.container.bind_all("<Control-s>", self.save_data)

        # --- GRAND TOTAL FOOTER ---
        self.footer = ttk.Frame(self.container)
        self.footer.pack(side="bottom", fill="x", pady=5)
        
        self.variance_label = ttk.Label(self.footer, text="", font=(MAIN_FONT, 10, "italic"))
        self.variance_label.pack(side="left", padx=10)

        self.total_label = ttk.Label(self.footer, text="Grand Total: $0.00", font=(MAIN_FONT, 11, "bold"))
        self.total_label.pack(side="right", padx=10)

    def _get_next_id(self):
        max_id = 0
        def check_node(node):
            nonlocal max_id
            for child in self.tree.get_children(node):
                vals = self.tree.item(child, 'values')
                if vals and str(vals[0]).isdigit():
                    max_id = max(max_id, int(vals[0]))
                check_node(child)
        for root_node in self.tree.get_children(''):
            vals = self.tree.item(root_node, 'values')
            if vals and str(vals[0]).isdigit():
                max_id = max(max_id, int(vals[0]))
            check_node(root_node)
        return max_id + 1

    def on_double_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell": return
        item_id = self.tree.identify_row(event.y)
        if 'date_row' in self.tree.item(item_id, 'tags'): return

        column = self.tree.identify_column(event.x)
        column_index = int(column[1:]) - 1
        x, y, width, height = self.tree.bbox(item_id, column)
        val = self.tree.item(item_id, 'values')[column_index]
        edit_entry = ttk.Entry(self.tree)
        edit_entry.insert(0, val)
        edit_entry.select_range(0, tk.END)
        edit_entry.focus_set()
        
        def save_edit(event=None):
            new_val = edit_entry.get()
            vals = list(self.tree.item(item_id, 'values'))
            vals[column_index] = new_val
            self.tree.item(item_id, values=vals)
            edit_entry.destroy()
            self._update_grand_total()

        edit_entry.bind("<Return>", save_edit)
        edit_entry.bind("<FocusOut>", lambda e: edit_entry.destroy())
        edit_entry.place(x=x, y=y, width=width, height=height)

    def _update_grand_total(self):
        """Calculates sum and determines Surplus/Deficit variance."""
        grand_sum = 0.0
        for parent in self.tree.get_children(''):
            for child in self.tree.get_children(parent):
                vals = self.tree.item(child, 'values')
                try:
                    q = float(vals[2])
                    p_str = str(vals[3]).replace(',', '').replace('$', '').strip()
                    p = float(p_str)
                    grand_sum += (q * p)
                except: continue
        
        budget = 0.0
        try: 
            budget_str = self.budget_var.get().replace(',', '').strip()
            budget = float(budget_str) if budget_str else 0.0
        except: pass

        self.total_label.config(text=f"Grand Total: ${grand_sum:,.2f}")
        
        if budget > 0:
            diff = budget - grand_sum
            if diff >= 0:
                self.variance_label.config(text=f"Budget Surplus: ${diff:,.2f}", foreground=ACCENT_GREEN)
                self.total_label.config(foreground=ACCENT_GREEN)
            else:
                self.variance_label.config(text=f"Budget Deficit: ${abs(diff):,.2f}", foreground=ACCENT_RED)
                self.total_label.config(foreground=ACCENT_RED)
        else:
            self.variance_label.config(text="")
            self.total_label.config(foreground=TEXT_FG)

    def load_data(self):
        """Scours logs and calculates totals, also loading saved budget."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        all_logs = self.controller.get_all_logs_for_project(self.project_id)
        # Simplified regex to match items without mandatory + - sign
        pattern = r"\$?\d+(?:\.\d{2})?\s+\"([^\"]+)\"\s+(\d+)"
        # Regex to find specifically the price string to capture the sign if it exists
        price_regex = r"([+-]?\$\d+(?:\.\d{2})?)"
        
        grouped_finances = {}
        auto_id_counter = 1

        # FETCH SAVED BUDGET
        budget_logs = self.controller.get_logs_for_project_date(self.project_id, "BUDGET_VAL")
        if budget_logs:
            self.budget_var.set(budget_logs[0].content)

        for log in all_logs:
            if log.timestamp in ["FINANCES", "BUDGET_VAL"]: continue
            content_text = ""
            try:
                data = json.loads(log.content)
                content_text = data.get("text", "")
            except: content_text = str(log.content)

            # Match items: price "Desc" qty
            matches = re.findall(r'([+-]?\$\d+(?:\.\d{2})?)\s+"([^"]+)"\s+(\d+)', content_text)
            if matches:
                date_key = log.timestamp
                if date_key not in grouped_finances:
                    grouped_finances[date_key] = []
                for m in matches:
                    grouped_finances[date_key].append(m)

        for date, items in sorted(grouped_finances.items(), reverse=True):
            day_total = 0.0
            day_qty = 0
            processed = []
            for p_str, desc, q_str in items:
                q = int(q_str)
                # Parse float, stripping sign for the absolute value per item
                p_clean = float(p_str.replace("$", "").replace("+", "").replace("-", ""))
                
                # Logic for day total: default to buying (negative) unless + sign is used
                # or keep it simple as everything scoured is an expenditure
                day_total += (p_clean * q)
                day_qty += q
                processed.append((p_clean, desc, q))

            parent_node = self.tree.insert("", "end", 
                                           values=(date, "", f"{day_qty}", f"${day_total:,.2f}", ""), 
                                           open=True, tags=('date_row',))
            
            for p, desc, q in processed:
                self.tree.insert(parent_node, "end", values=(
                    str(auto_id_counter), desc, q, f"{p:,.2f}", "Log Reference"
                ))
                auto_id_counter += 1
        
        self._update_grand_total()

    def add_row(self):
        next_id = self._get_next_id()
        self.tree.insert("", "end", values=(str(next_id), "New Item", "1", "0.00", "http://"))
        self._update_grand_total()

    def remove_row(self):
        sel = self.tree.selection()
        if sel: 
            self.tree.delete(sel)
            self._update_grand_total()

    def save_data(self, event=None):
        """Saves budget to DB and forces an immediate UI update of variance."""
        existing = self.controller.get_logs_for_project_date(self.project_id, "BUDGET_VAL")
        new_val = self.budget_var.get()
        
        if existing:
            self.controller.save_log_text(existing[0].id, new_val)
        else:
            self.controller.add_log_entry(self.project_id, "BUDGET_VAL", new_val)

        # Force UI update for surplus/deficit immediately
        self._update_grand_total()

        self.status_label.config(text="✔ Finances Saved", foreground="lightgreen")
        self.container.after(2000, lambda: self.status_label.config(text="Finances Mode", foreground="white"))
        return "break"

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
        
        self.bg_color = DARK_BG
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

        ttk.Label(main_frame, text="Log Entries", font=(MAIN_FONT, HEADER_FONT_SIZE, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(main_frame, text="Editor", font=(MAIN_FONT, HEADER_FONT_SIZE, "bold")).grid(row=0, column=1, sticky="w")
        ttk.Label(main_frame, text="Reference Media", font=(MAIN_FONT, HEADER_FONT_SIZE, "bold")).grid(row=0, column=2, sticky="w")

        # --- LEFT: Entries List ---
        self.df = tk.Frame(main_frame, bg=self.bg_color, highlightthickness=2)
        self.df.grid(row=1, column=0, sticky="nsew", padx=5)
        
        self.date_listbox = tk.Listbox(self.df, bg=self.bg_color, fg=TEXT_FG, font=(MAIN_FONT, NORMAL_FONT_SIZE), 
                                       borderwidth=0, highlightthickness=0,
                                       selectbackground=SELECT_BG, selectforeground="black")
        self.date_listbox.pack(fill='both', expand=True)
        self.date_listbox.bind('<<ListboxSelect>>', self.on_date_selected)
        
        entry_btn_frame = ttk.Frame(self.df)
        entry_btn_frame.pack(fill='x', pady=0) 
        ttk.Button(entry_btn_frame, text="➕ Add Entry", command=self.add_entry_clicked).pack(side='left', expand=True, fill='x', padx=1)
        ttk.Button(entry_btn_frame, text="➖ Remove Entry", command=self.delete_entry_clicked).pack(side='left', expand=True, fill='x', padx=1)

        self.df.bind("<Button-1>", lambda e: self.highlight_window("dates"))
        self.date_listbox.bind("<Button-1>", lambda e: self.highlight_window("dates"))

        # --- CENTER: Editor & Switcher ---
        self.lf = tk.Frame(main_frame, bg=self.bg_color, highlightthickness=2)
        self.lf.grid(row=1, column=1, sticky="nsew", padx=5)
        self.lf.bind("<Button-1>", lambda e: self.highlight_window("editor"))
        
        editor_bottom_bar = ttk.Frame(self.lf)
        editor_bottom_bar.pack(side='bottom', fill='x', pady=0)
        
        self.status_label = ttk.Label(editor_bottom_bar, text="", font=("Arial", 9, "italic"))
        self.status_label.pack(side='left', padx=10)

        self.editor = AdvancedLogEditor(self.lf, self.controller, lambda: self.current_log_id, 
                                        self.status_label, self.highlight_window, 
                                        ref_callback=self.select_tile_by_id)

        self.finance_editor = FinanceEditor(self.lf, self.controller, self.project.id, self.status_label)
        self.finance_editor.container.pack_forget()

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
        attachments = self.controller.get_attachments_for_project(self.project.id)
        target_tile = None
        for i, att in enumerate(attachments):
            if att.id == attachment_id:
                if i < len(self.media_tile_widgets):
                    target_tile = self.media_tile_widgets[i]
                    break
        if target_tile:
            self.select_tile(attachment_id, target_tile)
            self.media_canvas.update_idletasks()
            all_items = self.media_canvas.find_withtag("tile_window")
            for item in all_items:
                if self.media_canvas.itemcget(item, "window") == str(target_tile):
                    coords = self.media_canvas.coords(item)
                    scroll_bbox = self.media_canvas.bbox("all")
                    if scroll_bbox:
                        self.media_canvas.yview_moveto(coords[1] / scroll_bbox[3])
                    break

    def _unified_scroller(self, event):
        direction = int(-1 * (event.delta / 120))
        if self.active_section == "dates":
            self.date_listbox.yview_scroll(direction, "units")
        elif self.active_section == "editor":
            if self.date_listbox.get(tk.ANCHOR) != "FINANCES":
                self.editor.text_area.yview_scroll(direction, "units")
        elif self.active_section == "media":
            self.media_canvas.yview_scroll(direction, "units")

    def highlight_window(self, section):
        self.active_section = section
        self.df.config(highlightbackground=BORDER_HIGHLIGHT if section == "dates" else BORDER_DARK)
        self.lf.config(highlightbackground=BORDER_HIGHLIGHT if section == "editor" else BORDER_DARK)
        self.mfc.config(highlightbackground=BORDER_HIGHLIGHT if section == "media" else BORDER_DARK)

    def delete_entry_clicked(self):
        sel = self.date_listbox.curselection()
        if not sel: return
        val = self.date_listbox.get(sel[0])
        if val in ["DESCRIPTION", "FINANCES"]: return
        if messagebox.askyesno("Confirm", f"Delete {val}?"):
            self.controller.delete_date_logs(self.project.id, val)
            self.load_dates()

    def select_tile(self, attachment_id, target_frame):
        for tile in self.media_tile_widgets:
            tile.configure(style="Card.TFrame")
            for child in tile.winfo_children():
                if isinstance(child, tk.Label): child.configure(bg="#333333", fg=TEXT_FG)
        target_frame.configure(style="SelectedTile.TFrame")
        for child in target_frame.winfo_children():
            if isinstance(child, tk.Label): child.configure(bg="#E0E0E0", fg="black")

    def export_log_as_txt(self):
        content = self.editor.text_area.get("1.0", "end-1c")
        file_path = filedialog.asksaveasfilename(defaultextension=".txt")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f: f.write(content)

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
                content = tk.Label(tile, text=f"📄 {ext.upper()}", font=("Arial", 20), bg="#333333", fg=TEXT_FG)
            content.pack(pady=5)
            tk.Label(tile, text=os.path.basename(full_path), font=("Arial", 8), wraplength=140, bg="#333333", fg=TEXT_FG).pack()
            def bind_tree(widget, aid=att.id, t_frame=tile):
                widget.bind("<Button-1>", lambda e: self.select_tile(aid, t_frame))
                for child in widget.winfo_children(): bind_tree(child, aid, t_frame)
            bind_tree(tile)
            self.media_tile_widgets.append(tile)
        self.reformat_tiles()

    def reformat_tiles(self, event=None):
        self.media_canvas.delete("tile_window")
        w = self.media_canvas.winfo_width()
        pad, tw, th = 15, 160, 180
        cols = max(1, (w - pad) // (tw + pad))
        for i, tile in enumerate(self.media_tile_widgets):
            r, c = i // cols, i % cols
            self.media_canvas.create_window(c*(tw+pad)+pad, r*(th+pad)+pad, window=tile, anchor="nw", tags="tile_window")
        self.media_canvas.update_idletasks()
        bbox = self.media_canvas.bbox("all")
        if bbox: self.media_canvas.config(scrollregion=(0, 0, bbox[2], bbox[3]+pad))

    def add_media_clicked(self):
        f = filedialog.askopenfilename()
        if f and self.controller.add_attachment(f, self.project.id, False): self.load_media()

    def load_dates(self):
        self.date_listbox.delete(0, tk.END)
        self.date_listbox.insert(tk.END, "DESCRIPTION")
        self.date_listbox.insert(tk.END, "FINANCES")
        for d in self.controller.get_dates_for_project(self.project.id):
            if d not in ["DESCRIPTION", "FINANCES", "BUDGET_VAL"]:
                self.date_listbox.insert(tk.END, d)

    def on_date_selected(self, event):
        self.highlight_window("dates")
        sel = self.date_listbox.curselection()
        if not sel: return
        selection = self.date_listbox.get(sel[0])
        
        if selection == "FINANCES":
            self.editor.main_container.pack_forget()
            self.finance_editor.container.pack(fill='both', expand=True)
            self.finance_editor.load_data()
            self.status_label.config(text="Finances Mode", foreground=TEXT_FG)
        else:
            self.finance_editor.container.pack_forget()
            self.editor.main_container.pack(fill='both', expand=True)
            logs = self.controller.get_logs_for_project_date(self.project.id, selection)
            if logs:
                self.current_log_id = logs[0].id
                self.editor.load_formatted_text(logs[0].content)
                self.status_label.config(text=f"Editing: {selection}", foreground=TEXT_FG)

    def add_entry_clicked(self):
        dialog = NewEntryDialog(self.window, self.controller.db_controller.get_all_templates())
        self.window.wait_window(dialog.dialog)
        if dialog.result:
            self.controller.add_log_entry(self.project.id, dialog.result[0], dialog.result[1])
            self.load_dates()