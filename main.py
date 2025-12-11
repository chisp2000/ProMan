# --- main.py ---

import sys
import time 
import tkinter as tk
from tkinter import ttk

from db_controller import DatabaseManager
from pm_controller import ProjectManagementController
from gui.main_window import MainWindow 


def show_splash(root):
    """Creates and displays a temporary splash screen."""
    splash = tk.Toplevel(root)
    splash.title("Loading")
    splash.overrideredirect(True) 
    
    splash_label = ttk.Label(splash, 
    text="ProMan Initializing...\nSetting up Database.", 
    font=("Arial", 16), 
    padding=20)
    splash_label.pack(expand=True, fill='both')
    
    splash_width = 300
    splash_height = 150
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (splash_width // 2)
    y = (screen_height // 2) - (splash_height // 2)
    splash.geometry(f'{splash_width}x{splash_height}+{x}+{y}')
    
    root.update() 
    time.sleep(1.5) # Simulate database load time
    
    splash.destroy()


def startup_application():
    # 1. CREATE THE TKINTER ROOT OBJECT
    root = tk.Tk()

    style = ttk.Style(root)
    
    # --- DARK MODE CONFIGURATION ---
    DARK_BG = "#2E2E2E"   # Dark Gray Background
    LIGHT_FG = "#2E2E2E"  # White Foreground Text
    ORANGE_COLOR = "#FFA500" # Orange accent

    # 2. Set the overall theme background to Dark Gray
    root.configure(bg=DARK_BG)
    style.configure(".", background=DARK_BG, foreground=LIGHT_FG) # Set default style for all widgets
    
    # 3. Configure specific widget styles
    style.configure("TFrame", background=DARK_BG)
    style.configure("TLabel", background=DARK_BG, foreground=LIGHT_FG)
    style.configure("TButton", background=DARK_BG, foreground=LIGHT_FG, borderwidth=1)
    
    # 4. Define and apply the Orange Font Style
    style.configure("Orange.TLabel", background=DARK_BG, foreground=ORANGE_COLOR)

    root.withdraw() # Hides the main window initially

    # 2. SHOW THE SPLASH SCREEN and LOAD DATA
    try:
        show_splash(root) 
        db_manager = DatabaseManager(db_path='projects.db')
        
    except Exception as e:
        print(f"FATAL ERROR: Could not initialize database. {e}")
        sys.exit(1)

    # 3. INITIALIZE CONTROLLER (Logic Layer)
    pm_controller = ProjectManagementController(db_manager=db_manager)

    # 4. OPEN THE MAIN WINDOW
    root.deiconify() 
    MainWindow(root, controller=pm_controller)
    
    # 5. Start the main application event loop
    root.mainloop()

    



if __name__ == "__main__":
    startup_application()