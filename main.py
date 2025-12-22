import ctypes
import sys
import os
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedStyle 

from db_controller import DatabaseManager
from pm_controller import ProjectManagementController
from gui.main_window import MainWindow 

mainFont = "Helvetica"

def get_base_path():
    # If the code is 'frozen' (compiled to EXE), use the EXE's folder
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # If running as a .py script, use the script's folder
    return os.path.dirname(os.path.abspath(__file__))

# Create the absolute path to the database
base_path = get_base_path()
db_absolute_path = os.path.join(base_path, "projects.db")

try:
    myappid = 'chisp2000.proman.projectmanager.v1' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

class BlueprintTraceSplash:
    """Animated Blueprint Trace Splash Screen."""
    def __init__(self, root, on_complete):
        self.root = root
        self.on_complete = on_complete
        
        # 1. Setup Splash Window (No borders, centered)
        self.splash = tk.Toplevel(self.root)
        self.splash.overrideredirect(True)
        
        self.width, self.height = 450, 250
        screen_w = self.splash.winfo_screenwidth()
        screen_h = self.splash.winfo_screenheight()
        x = (screen_w // 2) - (self.width // 2)
        y = (screen_h // 2) - (self.height // 2)
        self.splash.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        # 2. Canvas with dark engineering background
        self.canvas = tk.Canvas(self.splash, bg="#1A1A1A", highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        # Draw a technical grid
        for i in range(0, self.width, 209):
            self.canvas.create_line(i, 0, i, self.height, fill="#252525")
        for i in range(0, self.height, 20):
            self.canvas.create_line(0, i, self.width, i, fill="#252525")

        # 3. Define the "Blueprint" lines to trace (Logo/Initials shape)
        self.trace_color = "#005a9e"
        self.lines = [
            (50, 180, 400, 180),  # Bottom base line
            (100, 180, 225, 80),  # Left angled support
            (225, 80, 350, 180),  # Right angled support
            (100, 180, 100, 140), # Left vertical pillar
            (350, 180, 350, 140), # Right vertical pillar
            (100, 140, 350, 140), # Top horizontal deck
            (100, 140, 225, 180), # Cross brace 1
            (350, 140, 225, 180)  # Cross brace 2
        ]
        self.current_line_idx = 0
        self.progress = 0

        self.animate_trace()

    def animate_trace(self):
        """Draws lines segment by segment for a drafting effect."""
        if self.current_line_idx < len(self.lines):
            x1, y1, x2, y2 = self.lines[self.current_line_idx]
            
            step = 15  # Drawing speed
            self.progress += step
            
            # Math to find the current point of the growing line
            curr_x = x1 + (x2 - x1) * (self.progress / 100)
            curr_y = y1 + (y2 - y1) * (self.progress / 100)
            
            self.canvas.create_line(x1, y1, curr_x, curr_y, 
                                    fill=self.trace_color, width=5)
            
            if self.progress >= 100:
                self.progress = 0
                self.current_line_idx += 1
            
            self.splash.after(20, self.animate_trace)
        else:
            # Animation complete
            self.canvas.create_text(self.width//2, self.height-30, 
                                   text="ProMan v0.3", 
                                   fill="white", font=(mainFont, 16, "bold"))
            self.splash.after(800, self.finish)

    def finish(self):
        self.splash.destroy()
        self.on_complete()

def startup_application():
    root = tk.Tk()
    root.withdraw() 

    # Set Window Icon
    icon_path = "proman_icon.ico" 
    if os.path.exists(icon_path):
        try: root.iconbitmap(icon_path)
        except Exception: pass

    # Theme Configuration
    style = ThemedStyle(root) 
    DARK_BG = "#1C1C1C"
    BRIGHT_FG = "#FFFFFF"
    ORANGE_COLOR = "#FFA500"
    DARK_BORDER_COLOR = "#2E2E2E"
    
    style.theme_use('black') 
    root.configure(bg=DARK_BG)

    # Global Styles
    style.configure(".", background=DARK_BG, foreground=BRIGHT_FG)
    style.configure("TButton", font=(mainFont, 10))
    style.configure("TFrame", background=DARK_BG)
    style.configure("ProjectTile.TFrame", background=DARK_BG, borderwidth=1, relief="solid",
                    lightcolor=DARK_BORDER_COLOR, darkcolor=DARK_BORDER_COLOR, bordercolor=DARK_BORDER_COLOR)
    style.configure("DarkList.TFrame", background=DARK_BG)
    style.configure("TLabel", background=DARK_BG, foreground=BRIGHT_FG)
    style.configure("Orange.TLabel", background=DARK_BG, foreground=ORANGE_COLOR)
    style.configure("OrangeBold.TLabel", background=DARK_BG, foreground=ORANGE_COLOR, font=(mainFont, 18)) 

    # The function that runs AFTER the splash is done
    def load_main_ui():
        try:
            db_manager = DatabaseManager(db_path=db_absolute_path)
            pm_controller = ProjectManagementController(db_manager=db_manager)
            root.deiconify() 
            MainWindow(root, controller=pm_controller)
        except Exception as e:
            messagebox.showerror("Fatal Error", f"Could not initialize database at {db_absolute_path}\nError: {e}")
            sys.exit(1)

    # Start Splash (Passes load_main_ui as a callback)
    BlueprintTraceSplash(root, load_main_ui)
    
    root.mainloop()

if __name__ == "__main__":
    startup_application()