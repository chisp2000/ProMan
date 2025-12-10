from db_controller import DatabaseManager
from pm_controller import ProjectManagementController
from db_models import Project

if __name__ == "__main__":
    
    # 1. INITIALIZE THE DATA LAYER (Model/Storage)
    # The file "projects.db" will be created or opened here.
    db_manager = DatabaseManager(db_path='projects.db') 

    # 2. INITIALIZE THE LOGIC LAYER (Controller)
    # Pass the database manager to the controller so it can save data.
    pm_controller = ProjectManagementController(db_manager=db_manager)

    print("-" * 30)
    print("Application Initialized.")
    
    # 3. EXECUTE A TEST FLOW (Create a Project)
    print("Attempting to create a new project via the Controller...")
    
    # The controller handles the saving process
    project_a = pm_controller.create_new_project(
        name="Build Prototype GUI",
        priority=3, # High
        due_date="2026-03-01"
    )

    project_b = pm_controller.create_new_project(
        name="Finalize Marketing Plan",
        priority=2, # Medium
        due_date="2026-04-15"
    )
    
    # 4. VERIFY RESULTS
    print("-" * 30)
    print("Project A created and saved:")
    print(project_a)
    
    print("\nProject B created and saved:")
    print(project_b)
    print("-" * 30)