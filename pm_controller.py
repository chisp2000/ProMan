# --- pm_controller.py ---

import os
import tkinter as tk
from tkinter import messagebox
from db_models import Project
from db_controller import DatabaseManager
from typing import Optional

class ProjectManagementController:
    def __init__(self, db_manager: DatabaseManager):
        self.db_controller = db_manager 
        self.main_window = None 
        self.root = None        

    def set_root(self, root):
        self.root = root

    # --- NEW: IMAGE CONVERSION UTILITY ---
    
    def process_image(self, file_path: str) -> Optional[str]:
        """
        Validates, converts (PNG->PPM), and RESIZES images to ~300x200px.
        Returns the path to the usable PPM file.
        """
        if not file_path or not os.path.exists(file_path):
            return None
            
        filename, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # We process PNGs AND existing PPM/GIFs to ensure they are resized
        if ext in ['.png', '.gif', '.ppm']:
            try:
                # 1. Prepare Directory
                convert_dir = "converted_images"
                if not os.path.exists(convert_dir):
                    os.makedirs(convert_dir)
                
                # Create a unique filename to avoid overwrites
                base_name = os.path.basename(filename)
                # Strip extension and add .ppm
                clean_name = os.path.splitext(base_name)[0]
                new_path = os.path.join(convert_dir, f"{clean_name}_thumb.ppm")
                
                # 2. Load Image into Tkinter
                # Note: We need a root window for PhotoImage, which we have (self.root)
                original_img = tk.PhotoImage(file=file_path)
                
                # 3. CALCULATE RESIZING (Integer Math)
                old_w = original_img.width()
                old_h = original_img.height()
                
                target_w = 300
                target_h = 200
                
                # Calculate how much we need to shrink (e.g., 600px / 300px = 2)
                # We use int() to drop decimals
                scale_x = int(old_w / target_w)
                scale_y = int(old_h / target_h)
                
                # We only resize if the image is actually larger than target
                if scale_x > 1 or scale_y > 1:
                    # Prevent division by zero if one dimension is already small
                    scale_x = 1 if scale_x < 1 else scale_x
                    scale_y = 1 if scale_y < 1 else scale_y
                    
                    # Apply the resizing (Subsample drops pixels)
                    # NOTE: Using different scales for X and Y will distort the image to fit 300x200
                    # If you want to keep aspect ratio, change both to 'max(scale_x, scale_y)'
                    resized_img = original_img.subsample(scale_x, scale_y)
                    
                    print(f"Resizing: {old_w}x{old_h} -> {resized_img.width()}x{resized_img.height()}")
                    
                    # Save the NEW, smaller image
                    resized_img.write(new_path, format="ppm")
                    return new_path
                    
                else:
                    # Image is already small enough, just convert/copy it
                    original_img.write(new_path, format="ppm")
                    return new_path
                
            except Exception as e:
                print(f"Image Processing Failed: {e}")
                # Fallback: Return original path if it was already PPM/GIF, else None
                if ext in ['.ppm', '.gif']: return file_path
                return None
        
        # JPG Warning
        if ext in ['.jpg', '.jpeg']:
            messagebox.showwarning("Format Not Supported", 
                                   "Standard Python cannot read JPG files without 'Pillow'.\nPlease use PNG or PPM.")
            return None
            
        return None

    # --- UPDATED METHODS TO USE CONVERSION ---

    def create_new_project(self, name: str, priority: int, due_date:str, image_path: Optional[str] = None):
        # PROCESS IMAGE FIRST
        final_image_path = self.process_image(image_path)
        
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
        # PROCESS IMAGE FIRST
        final_image_path = self.process_image(img)
        
        self.db_controller.update_project(Project(id=pid, name=name, priority=priority, due_date=due, thumbnail_path=final_image_path))
        if self.main_window: self.main_window.refresh_project_list()

    def add_attachment(self, file_path, project_id, is_global):
        # PROCESS IMAGE FIRST
        final_image_path = self.process_image(file_path)
        
        if final_image_path:
            self.db_controller.add_attachment(final_image_path, project_id=project_id, is_global=is_global)
        else:
            print("Attachment cancelled due to invalid image.")

    # ... (Rest of the controller methods remain exactly the same) ...
    def get_all_projects_sorted(self): return self.db_controller.get_projects_sorted()
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
    def get_dates_for_project(self, pid): return self.db_controller.get_log_dates(pid)
    def get_logs_for_project_date(self, pid, date): return self.db_controller.get_logs_by_date(pid, date)
    def add_log_entry(self, pid, date, content): self.db_controller.create_log(pid, content, date)
    def save_log_text(self, log_id, text): self.db_controller.update_log_content(log_id, text)
    def delete_date_logs(self, pid, date): self.db_controller.delete_logs_for_date(pid, date)
    def get_attachments_for_project(self, pid): return self.db_controller.get_viewable_attachments(pid)
    def get_all_attachments_for_manager(self): return self.db_controller.get_all_attachments()
    def toggle_attachment_global(self, att_id, current_state): self.db_controller.update_attachment_scope(att_id, not current_state)
    def delete_attachment(self, att_id): self.db_controller.delete_attachment(att_id)
    def open_project_detail_window(self, project_id: int):
        from gui.project_detail_window import ProjectDetailWindow
        project = self.db_controller.get_project_by_id(project_id)
        if project and self.root: ProjectDetailWindow(self.root, self, project)
    def open_attachment_manager(self):
        from gui.attachment_manager import AttachmentManager
        if self.root: AttachmentManager(self.root, self)