import os
import tkinter as tk
from tkinter import messagebox
import uuid 
import time
import shutil
from typing import Optional
from PIL import Image 
from datetime import datetime

from db_models import Project
from db_controller import DatabaseManager 

class ProjectManagementController:
    def __init__(self, db_manager: DatabaseManager):
        self.db_controller = db_manager 
        self.main_window = None 
        self.root = None        

    def set_root(self, root):
        self.root = root

    def process_file_attachment(self, source_path: str, is_thumbnail: bool = False) -> Optional[str]:
        """Resizes images to thumbnails or copies files to the internal media directory."""
        if not source_path or not os.path.exists(source_path):
            return None

        save_dir = "media"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        ext = os.path.splitext(source_path)[1].lower()
        image_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif']
        unique_id = uuid.uuid4().hex[:8]
        timestamp = int(time.time())
        prefix = "thumb" if is_thumbnail else "att"

        if ext in image_extensions:
            new_filename = f"{prefix}_{timestamp}_{unique_id}.png"
            destination_path = os.path.normpath(os.path.join(save_dir, new_filename))
            
            try:
                with Image.open(source_path) as img:
                    # IMPLEMENTATION: Resize if requested
                    if is_thumbnail:
                        img.thumbnail((300, 200))
                    
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        img = img.convert('RGBA')
                    else:
                        img = img.convert('RGB')
                    
                    img.save(destination_path, "PNG")
                    return destination_path 
            except Exception as e:
                messagebox.showerror("Image Error", f"Failed to process image:\n{e}")
                return None
        else:
            new_filename = f"{prefix}_{timestamp}_{unique_id}{ext}"
            destination_path = os.path.normpath(os.path.join(save_dir, new_filename))
            try:
                shutil.copy2(source_path, destination_path)
                return destination_path
            except Exception as e:
                messagebox.showerror("File Error", f"Failed to attach file:\n{e}")
                return None

    def create_new_project(self, name, priority, due_date, thumbnail_path, description):
        """Creates project after processing the thumbnail."""
        from db_models import Project
        import json
        
        # IMPLEMENTATION: Process the thumbnail through the scaler
        final_thumb = self.process_file_attachment(thumbnail_path, is_thumbnail=True)
        
        # 1. Create the project record with the resized path
        new_project = Project(name=name, priority=priority, due_date=due_date, thumbnail_path=final_thumb)
        self.db_controller.save_project(new_project)
        
        # 2. Automatically create the DESCRIPTION entry
        if description.strip():
            content_json = json.dumps({"text": f"{description}", "tags": []})
            self.db_controller.create_log(new_project.id, content_json, "DESCRIPTION")
        
        self.main_window.refresh_project_list()

    def update_existing_project(self, project_id, name, priority, due_date, thumbnail_path, description):
        """Updates project, processing thumbnail ONLY if a new path is provided."""
        from db_models import Project
        import json
        
        # IMPLEMENTATION: Check if thumbnail_path is a new file or an existing media file
        final_thumb = thumbnail_path
        if thumbnail_path and not thumbnail_path.startswith("media"):
            final_thumb = self.process_file_attachment(thumbnail_path, is_thumbnail=True)
        
        # 1. Update the project record
        updated_project = Project(id=project_id, name=name, priority=priority, due_date=due_date, thumbnail_path=final_thumb)
        self.db_controller.update_project(updated_project)
        
        # 2. Update or Create the DESCRIPTION log
        logs = self.db_controller.get_logs_by_date(project_id, "DESCRIPTION")
        content_json = json.dumps({"text": description, "tags": []})
        
        if logs:
            self.db_controller.update_log_content(logs[0].id, content_json)
        elif description.strip():
            self.db_controller.create_log(project_id, content_json, "DESCRIPTION")
        
        self.main_window.refresh_project_list()

    def add_attachment(self, source_path, project_id, is_global=False):
        final_path = self.process_file_attachment(source_path, is_thumbnail=False)
        if final_path:
            self.db_controller.add_attachment(final_path, project_id, is_global)
            return True
        return False

    def get_all_projects_sorted(self): 
        return self.db_controller.get_projects_sorted()
    
    def delete_project_flow(self, pid):
        self.db_controller.delete_project(pid)
        if self.main_window: self.main_window.refresh_project_list()

    def get_all_attachments_for_manager(self): 
        return self.db_controller.get_all_attachments()

    def toggle_attachment_global(self, att_id, current_is_global): 
        self.db_controller.update_attachment_scope(att_id, not current_is_global)
        
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
    
    def open_project_detail_window(self, project_id: int):
        from gui.project_detail_window import ProjectDetailWindow
        project = self.db_controller.get_project_by_id(project_id)
        if project and self.root:
            self.root.withdraw()
            detail_window = ProjectDetailWindow(self.root, self, project)
            detail_window.window.protocol("WM_DELETE_WINDOW", lambda: [self.root.deiconify(), self.main_window.refresh_project_list(), detail_window.window.destroy()])

    def open_new_project_dialog(self):
        from gui.new_project_dialog import NewProjectDialog
        if self.root: NewProjectDialog(self.root, controller=self)
        
    def open_edit_project_dialog(self, pid):
        from gui.new_project_dialog import NewProjectDialog
        project = self.db_controller.get_project_by_id(pid)
        if project and self.root: NewProjectDialog(self.root, controller=self, project_to_edit=project)

    def open_attachment_manager(self):
        from gui.attachment_manager import AttachmentManager
        if self.root: AttachmentManager(self.root, self)

    def get_all_logs_for_project(self, project_id):
        return self.db_controller.get_logs_for_project(project_id)