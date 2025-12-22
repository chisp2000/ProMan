import ctypes
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedStyle 

from db_controller import DatabaseManager
from pm_controller import ProjectManagementController
from gui.main_window import MainWindow 

# ==============================================================================
# GLOBAL STYLE CONFIGURATION (Edit everything here)
# ==============================================================================
# Colors
ACCENT_COLOR       = "#E7E7E7"     # The primary color
BG_COLOR           = "#1C1C1C"     # The main background color
GRID_COLOR         = "#252525"     # The background grid lines
TEXT_COLOR         = "#FFFFFF"     # Primary text color
TEXT_SECONDARY     = "#A0A0A0"     # Dimmer text for version/status
BORDER_COLOR       = "#2E2E2E"     # Border for UI elements

# Typography
BRAND_FONT_FAMILY  = "Verdana"     
BRAND_SIZE         = 42            # Increased size since animation is gone
UI_FONT_FAMILY     = "Segoe UI"    
STATUS_SIZE        = 9             
# ==============================================================================

def get_base_path():
    """Robust method to find the directory where the app is running."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

class StaticBrandingSplash:
    def __init__(self, root, on_complete):
        self.root = root
        self.on_complete = on_complete
        
        self.splash = tk.Toplevel(self.root)
        self.splash.overrideredirect(True)
        
        # Slightly more compact height now that we are just showing text
        self.width, self.height = 550, 300
        screen_w = self.splash.winfo_screenwidth()
        screen_h = self.splash.winfo_screenheight()
        x = (screen_w // 2) - (self.width // 2)
        y = (screen_h // 2) - (self.height // 2)
        self.splash.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        self.canvas = tk.Canvas(self.splash, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        self._draw_technical_elements()
        self._render_text()
        
        # Start a short delay before finishing to simulate "Loading"
        self.progress = 0
        self._update_loading_bar()

    def _draw_technical_elements(self):
        """Draws the static grid and corner brackets."""
        # Grid
        for i in range(0, self.width, 40):
            self.canvas.create_line(i, 0, i, self.height, fill=GRID_COLOR)
        for i in range(0, self.height, 40):
            self.canvas.create_line(0, i, self.width, i, fill=GRID_COLOR)
            
        m, side_len = 20, 15
        # Corner brackets
        self.canvas.create_line(m, m, m+side_len, m, fill=ACCENT_COLOR, width=1)
        self.canvas.create_line(m, m, m, m+side_len, fill=ACCENT_COLOR, width=1)
        self.canvas.create_line(self.width-m, self.height-m, self.width-m-side_len, self.height-m, fill=ACCENT_COLOR, width=1)
        self.canvas.create_line(self.width-m, self.height-m, self.width-m, self.height-m-side_len, fill=ACCENT_COLOR, width=1)

    def _render_text(self):
        """Renders the main branding text and version."""
        spaced_brand = " ".join("PROMAN") 
        # Centered branding
        self.canvas.create_text(self.width//2, self.height//2 - 10, 
                               text=spaced_brand, 
                               fill=TEXT_COLOR, 
                               font=(BRAND_FONT_FAMILY, BRAND_SIZE, "bold"))
        
        self.canvas.create_text(self.width//2, self.height//2 + 40, 
                               text="SYSTEM INITIALIZATION v0.3", 
                               fill=ACCENT_COLOR, 
                               font=(UI_FONT_FAMILY, STATUS_SIZE, "bold"))

    def _update_loading_bar(self):
        """Draws a subtle progress bar at the very bottom."""
        self.canvas.delete("loading_bar")
        self.progress += 4
        
        # Progress bar background
        bar_y = self.height - 2
        self.canvas.create_line(0, bar_y, self.width, bar_y, fill=GRID_COLOR, width=4, tags="loading_bar")
        # Active progress
        current_width = (self.progress / 100) * self.width
        self.canvas.create_line(0, bar_y, current_width, bar_y, fill=ACCENT_COLOR, width=4, tags="loading_bar")

        if self.progress < 100:
            self.splash.after(30, self._update_loading_bar)
        else:
            self.splash.after(500, self.finish)

    def finish(self):
        self.splash.destroy()
        self.on_complete()

def startup_application(db_path):
    root = tk.Tk()
    root.withdraw() 

    style = ThemedStyle(root) 
    style.theme_use('black') 
    root.configure(bg=BG_COLOR)

    def load_main_ui():
        try:
            # Sync main window styles
            style.configure(".", background=BG_COLOR, foreground=TEXT_COLOR)
            style.configure("TFrame", background=BG_COLOR)
            style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR)
            style.configure("ProjectTile.TFrame", background=BG_COLOR, borderwidth=1, relief="solid",
                            lightcolor=BORDER_COLOR, darkcolor=BORDER_COLOR, bordercolor=BORDER_COLOR)
            style.configure("DarkList.TFrame", background=BG_COLOR)
            
            style.configure("Accent.TLabel", background=BG_COLOR, foreground=ACCENT_COLOR)
            style.configure("AccentBold.TLabel", background=BG_COLOR, foreground=ACCENT_COLOR, 
                            font=(BRAND_FONT_FAMILY, 18, "bold"))

            db_manager = DatabaseManager(db_path=db_path)
            pm_controller = ProjectManagementController(db_manager=db_manager)
            root.deiconify() 
            MainWindow(root, controller=pm_controller)
        except Exception as e:
            messagebox.showerror("Fatal Error", f"Database Init Failed: {e}")
            sys.exit(1)

    StaticBrandingSplash(root, load_main_ui)
    root.mainloop()

if __name__ == "__main__":
    base_dir = get_base_path()
    db_absolute_path = os.path.join(base_dir, "projects.db")
    
    try:
        myappid = 'chisp2000.proman.projectmanager.v1' 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass
        
    startup_application(db_absolute_path)