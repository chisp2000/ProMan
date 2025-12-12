import ctypes
import sys
import os
import time 
import tkinter as tk
from tkinter import ttk
# Import ThemedStyle
from ttkthemes import ThemedStyle 

from db_controller import DatabaseManager
from pm_controller import ProjectManagementController
from gui.main_window import MainWindow 

# 1. TELL WINDOWS THIS IS A UNIQUE APP (Fixes Taskbar Icon)
# This code block must run before the root window is created
try:
    # The ID can be anything, but it must be a unique string
    myappid = 'chisp2000.proman.projectmanager.v1' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

def show_splash(root):
    """Creates and displays a temporary splash screen."""
    splash = tk.Toplevel(root)
    splash.title("Loading")
    splash.overrideredirect(True) 
    
    # Use ttk.Style for splash screen, or manually set colors if preferred
    splash_label = ttk.Label(splash, 
    text="ProMan Initializing...\nSetting up Database.", 
    font=("EASVHS", 16), 
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
    # 2. CREATE THE TKINTER ROOT OBJECT
    root = tk.Tk()

    root.withdraw() # Hides the main window initially


    # 3. SET THE WINDOW ICON (Fixes Top-Left Window Icon)
    icon_path = "proman_icon.ico" 
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Icon error: {e}")

    # Use ThemedStyle for better theme control
    style = ThemedStyle(root) 
    
    # --- DARK MODE CONFIGURATION ---
    DARK_BG = "#1C1C1C" # Custom very dark gray
    BRIGHT_FG = "#FFFFFF"     # White Foreground Text
    ORANGE_COLOR = "#FFA500"  # Orange accent
    DARK_BORDER_COLOR = "#2E2E2E" # Use a dark gray that complements the background
    
    # Set the theme. 'black' is a great dark theme.
    style.theme_use('black') 
    
    root.configure(bg=DARK_BG)

    style.configure("TButton", font=("EASVHS", 10))

    style.configure(".", background=DARK_BG, foreground=BRIGHT_FG)
    style.configure("TFrame", background=DARK_BG)
    
    # --------------------------------------------
    # --- PROJECT TILE BORDER FIX (new style) ---
    # --------------------------------------------
    # Define the style for the Project Tile Border. 
    # Setting lightcolor/darkcolor to a dark value forces the border to be dark.
    style.configure("ProjectTile.TFrame", 
                background=DARK_BG, 
                lightcolor=DARK_BORDER_COLOR,  # For 'solid' relief color override
                darkcolor=DARK_BORDER_COLOR,   # For 'solid' relief color override
                bordercolor=DARK_BORDER_COLOR, # General border color
                borderwidth=1, 
                relief="solid")

    # Define the custom list frame style (used by the canvas inner frame)
    style.configure("DarkList.TFrame", background=DARK_BG)
    
    style.configure("TLabel", background=DARK_BG, foreground=BRIGHT_FG)

    # Configure specific widget styles for accents
    
    # Define and apply the Orange Font Style for titles and accents
    style.configure("Orange.TLabel", 
                    background=DARK_BG, 
                    foreground=ORANGE_COLOR)

    # Define the Bold Orange Font Style for the Project Title
    style.configure("OrangeBold.TLabel", 
                    background=DARK_BG, 
                    foreground=ORANGE_COLOR, 
                    font=("EASVHS", 18, )) 
    
    # 4. SHOW THE SPLASH SCREEN and LOAD DATA
    try:
        show_splash(root) 
        db_manager = DatabaseManager(db_path='projects.db')
        
    except Exception as e:
        print(f"FATAL ERROR: Could not initialize database. {e}")
        sys.exit(1)

    # 5. INITIALIZE CONTROLLER (Logic Layer)
    pm_controller = ProjectManagementController(db_manager=db_manager)

    # 6. OPEN THE MAIN WINDOW
    root.deiconify() 
    MainWindow(root, controller=pm_controller)
    
    # 7. Start the main application event loop
    root.mainloop()

if __name__ == "__main__":
    startup_application()