import sqlite3
from typing import List
from db_models import Project, LogEntry # Import models

class DatabaseManager:
    def __init__(self, db_path: str = "projects.db"):
        self.db_path = db_path
        self.initialize_database()

    def delete_project(self, project_id: int):
        """
        Deletes a project, its logs, and its attachments based on project_id.
        Deletion must be done in reverse dependency order.
        """
        
        try:
            # 1. CRITICAL: Delete related attachments (Requires a SELECT lookup on logs first)
            # This handles the case where attachment is linked to a log.
            self._execute_sql(
                "DELETE FROM attachment WHERE log_id IN (SELECT log_id FROM log WHERE project_id = ?)", 
                (project_id,)
            )

            # 2. Delete Logs associated with the project
            self._execute_sql("DELETE FROM log WHERE project_id = ?", (project_id,))

            # 3. Delete the main Project record
            self._execute_sql("DELETE FROM project WHERE project_id = ?", (project_id,))
            
            print(f"Project ID {project_id} and all related data deleted successfully.")

        except sqlite3.Error as e:
            print(f"Database Error during deletion: {e}")
            raise

    def _execute_sql(self, sql_command: str, params: tuple = ()):
        """Utility to connect, execute a command, and commit (for INSERT/CREATE/UPDATE)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql_command, params)
                conn.commit()
                return cursor
        except sqlite3.Error as e:
            print(f"Database Error during execution: {e}")
            raise 

    def _execute_query(self, sql_command: str, params: tuple = ()):
        """Utility for SELECT queries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row 
                cursor = conn.cursor()
                cursor.execute(sql_command, params)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Database Query Error: {e}")
            return []

    def initialize_database(self):
        """Creates all necessary tables if they don't already exist."""
        create_project_sql = """
        CREATE TABLE IF NOT EXISTS project (
            project_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            priority INTEGER NOT NULL,
            due_date TEXT,
            thumbnail_path TEXT 
        )
        """
        create_log_sql = """
        CREATE TABLE IF NOT EXISTS log (
            log_id INTEGER PRIMARY KEY,
            project_id INTEGER,
            timestamp TEXT,
            content TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES project(project_id)
        )
        """
        create_attachment_sql = """
        CREATE TABLE IF NOT EXISTS attachment (
            attachment_id INTEGER PRIMARY KEY,
            log_id INTEGER,
            file_path TEXT NOT NULL,
            is_thumbnail INTEGER, 
            FOREIGN KEY(log_id) REFERENCES log(log_id)
        )
        """
        self._execute_sql(create_project_sql)
        self._execute_sql(create_log_sql)
        self._execute_sql(create_attachment_sql)
        print("Database schema successfully initialized.")
        
    def save_project(self, project: Project):
        """Saves a new project to the database and updates the object with its new ID."""
        sql = "INSERT INTO project (name, priority, due_date, thumbnail_path) VALUES (?, ?, ?, ?)"
        
        params = (project.name, project.priority, project.due_date, project.thumbnail_path)
        
        cursor = self._execute_sql(sql, params)
        project.id = cursor.lastrowid
        print(f"Project '{project.name}' saved with ID {project.id}")

    def get_projects_sorted(self) -> List[Project]:
        """Retrieves all projects, sorted by priority (DESC) and date (ASC)."""
        sql = """
        SELECT project_id, name, priority, due_date, thumbnail_path
        FROM project 
        ORDER BY priority DESC, due_date ASC
        """
        
        rows = self._execute_query(sql)
        
        projects = []
        for row in rows:
            projects.append(Project(
                id=row['project_id'],
                name=row['name'],
                priority=row['priority'],
                due_date=row['due_date'],
                thumbnail_path=row['thumbnail_path']
            ))
        return projects