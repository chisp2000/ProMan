import os
import tkinter as tk
from tkinter import messagebox
import uuid 
import time
import shutil
from typing import Optional
from PIL import Image # CRITICAL: Ensure Pillow is installed via 'pip install Pillow'

from db_models import Project
from db_controller import DatabaseManager 

class ProjectManagementController:
    def __init__(self, db_manager: DatabaseManager):
        self.db_controller = db_manager 
        self.main_window = None 
        self.root = None        

    def set_root(self, root):
        self.root = root

    # --- FILE & IMAGE PROCESSING UTILITY ---
    
    def process_file_attachment(self, source_path: str, is_thumbnail: bool = False) -> Optional[str]:
        """
        Handles all file types. 
        - Images: Converted to PNG and optionally resized (for thumbnails).
        - Non-Images: Copied directly to the 'media' folder.
        Returns the new relative path for database storage.
        """
        if not source_path or not os.path.exists(source_path):
            return None

        # 1. Prepare Media Directory
        save_dir = "media"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # 2. Identify File Type
        ext = os.path.splitext(source_path)[1].lower()
        image_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif']

        # 3. Generate Unique Managed Filename
        unique_id = uuid.uuid4().hex[:8]
        timestamp = int(time.time())
        prefix = "thumb" if is_thumbnail else "att"

        # 4. BRANCH: Image Processing vs. File Copying
        if ext in image_extensions:
            # --- IMAGE LOGIC: Convert/Resize using Pillow ---
            new_filename = f"{prefix}_{timestamp}_{unique_id}.png"
            destination_path = os.path.join(save_dir, new_filename)
            
            try:
                with Image.open(source_path) as img:
                    # Resize if it is intended for the Project List thumbnail
                    if is_thumbnail:
                        img.thumbnail((300, 200))
                    
                    # Handle transparency/alpha channels
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        img = img.convert('RGBA')
                    else:
                        img = img.convert('RGB')
                    
                    img.save(destination_path, "PNG")
                    print(f"Image processed and saved: {destination_path}")
                    return destination_path

            except Exception as e:
                print(f"Error processing image: {e}")
                messagebox.showerror("Image Error", f"Failed to process image:\n{e}")
                return None
        else:
            # --- NON-IMAGE LOGIC: Copy Videos, Excel, Word, etc. ---
            # We use the original extension to ensure OS file associations remain intact.
            new_filename = f"{prefix}_{timestamp}_{unique_id}{ext}"
            destination_path = os.path.join(save_dir, new_filename)
            
            try:
                # Copy the file to the local media folder to manage it internally
                shutil.copy2(source_path, destination_path)
                print(f"Non-image file managed: {destination_path}")
                return destination_path
            except Exception as e:
                print(f"Error copying file: {e}")
                messagebox.showerror("File Error", f"Failed to attach file:\n{e}")
                return None

    # --- CONTROLLER ACTIONS ---

    def create_new_project(self, name: str, priority: int, due_date: str, image_path: Optional[str] = None):
        """Creates a project and processes the thumbnail."""
        final_image_path = self.process_file_attachment(image_path, is_thumbnail=True)
        
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
        """Updates project details and processes new thumbnail if provided."""
        final_image_path = self.process_file_attachment(img, is_thumbnail=True)
        
        updated_project = Project(
            id=pid, 
            name=name, 
            priority=priority, 
            due_date=due, 
            thumbnail_path=final_image_path
        )
        self.db_controller.update_project(updated_project)
        
        if self.main_window: 
            self.main_window.refresh_project_list()

    def add_attachment(self, source_path, project_id, is_global=False):
        """Adds a reference media file (Image, Video, or Doc) to a specific project."""
        final_path = self.process_file_attachment(source_path, is_thumbnail=False)
        
        if final_path:
            self.db_controller.add_attachment(final_path, project_id, is_global)
            print(f"Attachment registered in DB for project {project_id}")

    # --- GUI LINKING & DATA PASS-THROUGHS ---

    def get_all_projects_sorted(self): 
        return self.db_controller.get_projects_sorted()
    
    def delete_project_flow(self, pid):
        self.db_controller.delete_project(pid)
        if self.main_window: 
            self.main_window.refresh_project_list()
        
    def open_new_project_dialog(self):
        from gui.new_project_dialog import NewProjectDialog
        if self.root: 
            NewProjectDialog(self.root, controller=self)
        
    def open_edit_project_dialog(self, pid):
        from gui.new_project_dialog import NewProjectDialog
        p = self.db_controller.get_project_by_id(pid)
        if p and self.root: 
            NewProjectDialog(self.root, controller=self, project_to_edit=p)
        
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
        
    def open_project_detail_window(self, project_id: int):
        """Hides main window and opens the dashboard for the selected project."""
        from gui.project_detail_window import ProjectDetailWindow
        project = self.db_controller.get_project_by_id(project_id)
        
        if project and self.root:
            self.root.withdraw()
            detail_window = ProjectDetailWindow(self.root, self, project)
            
            def on_close_detail():
                self.root.deiconify()
                if self.main_window:
                    self.main_window.refresh_project_list()
                detail_window.window.destroy()
            
            detail_window.window.protocol("WM_DELETE_WINDOW", on_close_detail)

    def open_attachment_manager(self):
        from gui.attachment_manager import AttachmentManager
        if self.root: 
            AttachmentManager(self.root, self)