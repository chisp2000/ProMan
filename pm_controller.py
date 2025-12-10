from db_models import Project
from db_controller import DatabaseManager

class ProjectManagementController:
    def __init__(self, db_manager: DatabaseManager):
        self.db_controller = db_manager

    def create_new_project(self, name: str, priority: int, due_date:str):
        new_project = Project(
            name=name,
            priority=priority,
            due_date=due_date
        )
        self.db_controller.save_project(new_project)
        return new_project