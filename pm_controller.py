# --- pm_controller.py ---

from db_models import Project
from db_controller import DatabaseManager
from typing import Optional

class ProjectManagementController:
    def __init__(self, db_manager: DatabaseManager):
        self.db_controller = db_manager 
        self.main_window = None # Set by MainWindow after creation
        self.root = None        # Set by MainWindow after creation

    # CRITICAL: Stores the main Tkinter window reference
    def set_root(self, root):
        self.root = root
        
    def get_all_projects_sorted(self):
        """Fetches the sorted list directly from the DatabaseManager."""
        return self.db_controller.get_projects_sorted()

    def create_new_project(self, name: str, priority: int, due_date:str, image_path: Optional[str] = None):
        
        new_project = Project(
            name=name,
            priority=priority,
            due_date=due_date,
            thumbnail_path=image_path # Pass the file path (or None) to the model
        )
        self.db_controller.save_project(new_project)
        
        # CRITICAL: Trigger the GUI update
        if self.main_window:
            self.main_window.refresh_project_list() 
        
        return new_project
    
    def delete_project_flow(self, project_id: int):
        """Handles the request to delete a project and triggers the UI refresh."""
        
        # 1. Execute deletion in the database
        self.db_controller.delete_project(project_id)
        
        # 2. Trigger the GUI update
        if self.main_window:
            self.main_window.refresh_project_list()
            

    def open_new_project_dialog(self):
        """Opens the dialog window for new project input."""
        from gui.new_project_dialog import NewProjectDialog 
        
        if self.root:
            # Pass the stored root object as the parent window
            NewProjectDialog(self.root, controller=self)
        else:
            print("Error: Tkinter root window not set on controller.")