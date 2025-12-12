import os
import tkinter as tk
from tkinter import messagebox
import uuid 
import time
from typing import Optional
from PIL import Image # CRITICAL: Ensure Pillow is imported

from db_models import Project
from db_controller import DatabaseManager 

class ProjectManagementController:
    def __init__(self, db_manager: DatabaseManager):
        self.db_controller = db_manager 
        self.main_window = None 
        self.root = None        

    def set_root(self, root):
        self.root = root

    # --- IMAGE CONVERSION UTILITY ---
    
    def save_image_as_png(self, source_path: str, is_thumbnail: bool = False) -> Optional[str]:
        """
        Takes a source image, converts it to PNG, optionally resizes it,
        saves it to the 'media' folder, and returns the new file path.
        """
        if not source_path or not os.path.exists(source_path):
            return None

        # 1. Prepare Directory
        save_dir = "media"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # 2. Generate Unique Filename
        unique_id = uuid.uuid4().hex[:8]
        timestamp = int(time.time())
        prefix = "thumb" if is_thumbnail else "ref"
        new_filename = f"{prefix}_{timestamp}_{unique_id}.png"
        destination_path = os.path.join(save_dir, new_filename)

        try:
            with Image.open(source_path) as img:
                # 3. Resize if it is a Project Thumbnail
                if is_thumbnail:
                    img.thumbnail((300, 200))
                
                # 4. Convert and Save as PNG
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
                
                img.save(destination_path, "PNG")
                print(f"Image converted and saved to: {destination_path}")
                return destination_path

        except Exception as e:
            print(f"Error converting image: {e}")
            messagebox.showerror("Image Error", f"Failed to process image:\n{e}")
            return None

    # --- CONTROLLER ACTIONS ---

    def create_new_project(self, name: str, priority: int, due_date:str, image_path: Optional[str] = None):
        final_image_path = self.save_image_as_png(image_path, is_thumbnail=True)
        
        new_project = Project(
            name=name,
            priority=priority,
            due_date=due_date,
            thumbnail_path=final_image_path 
        )
        self.db_controller.save_project(new_project)
        
        if self.main_window:
            self.main_window.refresh_project_list() 
        return new_project

    def update_existing_project(self, pid, name, priority, due, img):
        final_image_path = self.save_image_as_png(img, is_thumbnail=True)
        
        self.db_controller.update_project(Project(id=pid, name=name, priority=priority, due_date=due, thumbnail_path=final_image_path))
        if self.main_window: self.main_window.refresh_project_list()

    def add_attachment(self, source_path, project_id, is_global=False):
        final_path = self.save_image_as_png(source_path, is_thumbnail=False)
        
        if final_path:
            self.db_controller.add_attachment(final_path, project_id, is_global)
            print(f"Attachment added for project {project_id}")

    # --- GUI LINKING & PASS-THROUGHS ---

    def get_all_projects_sorted(self): 
        return self.db_controller.get_projects_sorted()
    
    def delete_project_flow(self, pid):
        self.db_controller.delete_project(pid)
        if self.main_window: self.main_window.refresh_project_list()
        
    def open_new_project_dialog(self):
        from gui.new_project_dialog import NewProjectDialog
        if self.root: NewProjectDialog(self.root, controller=self)
        
    def open_edit_project_dialog(self, pid):
        from gui.new_project_dialog import NewProjectDialog
        p = self.db_controller.get_project_by_id(pid)
        if p and self.root: NewProjectDialog(self.root, controller=self, project_to_edit=p)
        
    def get_dates_for_project(self, pid): 
        return self.db_controller.get_log_dates(pid)
    
    def get_logs_for_project_date(self, pid, date): 
        return self.db_controller.get_logs_by_date(pid, date)
    
    def add_log_entry(self, pid, date, content): 
        self.db_controller.create_log(pid, content, date)
    
    def save_log_text(self, log_id, text): 
        self.db_controller.update_log_content(log_id, text)
    
    def delete_date_logs(self, pid, date): 
        self.db_controller.delete_logs_for_date(pid, date)
    
    def get_attachments_for_project(self, pid): 
        return self.db_controller.get_viewable_attachments(pid)
    
    def get_all_attachments_for_manager(self): 
        return self.db_controller.get_all_attachments()
    
    def toggle_attachment_global(self, att_id, current_state): 
        self.db_controller.update_attachment_scope(att_id, not current_state)
    
    def delete_attachment(self, att_id): 
        self.db_controller.delete_attachment(att_id)
        
    # --- UPDATED: OPEN PROJECT DETAIL WINDOW ---
    def open_project_detail_window(self, project_id: int):
        from gui.project_detail_window import ProjectDetailWindow
        project = self.db_controller.get_project_by_id(project_id)
        
        if project and self.root:
            # 1. HIDE the Main Window
            self.root.withdraw()
            
            # 2. Create the Detail Window
            detail_window = ProjectDetailWindow(self.root, self, project)
            
            # 3. Define the "On Close" behavior
            def on_close_detail():
                self.root.deiconify()  # Show the main window again
                if self.main_window:
                    self.main_window.refresh_project_list() # Refresh list in case data changed
                detail_window.window.destroy() # Actually destroy the detail window
            
            # 4. Override the "X" button (Window Manager Delete Window)
            detail_window.window.protocol("WM_DELETE_WINDOW", on_close_detail)

    def open_attachment_manager(self):
        from gui.attachment_manager import AttachmentManager
        if self.root: AttachmentManager(self.root, self)