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
    font=("Rockwell", 16), 
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


# --- main.py ---

import sys
import time 
import tkinter as tk
from tkinter import ttk
# NEW: Import ThemedStyle
from ttkthemes import ThemedStyle 

from db_controller import DatabaseManager
from pm_controller import ProjectManagementController
from gui.main_window import MainWindow 


def show_splash(root):
    """Creates and displays a temporary splash screen."""
    splash = tk.Toplevel(root)
    splash.title("Loading")
    splash.overrideredirect(True) 
    
    # Use ttk.Style for splash screen, or manually set colors if preferred
    splash_label = ttk.Label(splash, 
    text="ProMan Initializing...\nSetting up Database.", 
    font=("Rockwell", 16), 
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

    # CHANGE 1: Use ThemedStyle for better theme control
    style = ThemedStyle(root) 
    
    # --- DARK MODE CONFIGURATION ---
    # The theme handles most background/foreground colors.
    DARK_BG = "#1C1C1C" # Custom very dark gray
    BRIGHT_FG = "#FFFFFF"     # White Foreground Text
    ORANGE_COLOR = "#FFA500"  # Orange accent
    # CHANGE 2: Set the theme. 'black' is a great dark theme.
    # Other dark options: 'equilux', 'ubuntu', 'arc'
    style.theme_use('black') 
    
    root.configure(bg=DARK_BG)

    style.configure(".", background=DARK_BG, foreground=BRIGHT_FG)
    style.configure("TFrame", background=DARK_BG)
    style.configure("TLabel", background=DARK_BG, foreground=BRIGHT_FG)

    # 3. Configure specific widget styles for accents
    # Note: TFrame, TButton, etc., will inherit the theme's colors,
    # so we only set custom colors like ORANGE.
    
    # 4. Define and apply the Orange Font Style for titles and accents
    style.configure("Orange.TLabel", 
                    background=DARK_BG, 
                    foreground=ORANGE_COLOR)

    # 5. Define the Bold Orange Font Style for the Project Title
    style.configure("OrangeBold.TLabel", 
                    background=DARK_BG, 
                    foreground=ORANGE_COLOR, 
                    font=("Rockwell", 18, "bold")) 

    # 6. Define the custom list frame style (which now uses the theme's DARK_BG)
    style.configure("DarkList.TFrame", background=DARK_BG)
    
    # NEW: Define a Dark Red style for the image placeholder (since tk.Label is used there)
    # The tk.Label uses 'bg'/'fg', but we ensure the parent frame color is respected.
    root.configure(bg=DARK_BG) 

    root.withdraw() # Hides the main window initially

    # 2. SHOW THE SPLASH SCREEN and LOAD DATA
    try:
        # Note: Splash screen will look default until we call mainloop, 
        # but the theme is ready.
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