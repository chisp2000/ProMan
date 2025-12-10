import sqlite3
from typing import List
from db_models import Project

class DatabaseManager:
    def __init__(self, db_path: str = "projects.db"):
        self.db_path = db_path  # 2. Stored as an instance attribute
        self.initialize_database()

    def initialize_database(self):
        """Creates all necessary tables if they don't already exist."""
        # Note: Added required fields and FOREIGN KEY constraints

        create_project_sql = """
        CREATE TABLE IF NOT EXISTS project (
            project_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            priority INTEGER NOT NULL,
            due_date TEXT
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
            is_thumbnail INTEGER, -- SQLite uses INTEGER for BOOLEAN (0 or 1)
            FOREIGN KEY(log_id) REFERENCES log(log_id)
        )
        """
        self._execute_sql(create_project_sql)
        self._execute_sql(create_log_sql)
        self._execute_sql(create_attachment_sql)
        print("Database schema successfully initialized.")

    
    def _execute_sql(self, sql_command: str, params: tuple = ()):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql_command, params)
                conn.commit()
                return cursor
        except sqlite3.Error as e:
            print(f"Database Error during execution: {e}")
            raise

    def save_project(self, project:Project):
        sql = "INSERT INTO project (name, priority, due_date) VALUES (?, ?, ?)" 
        cursor = self._execute_sql(sql, (project.name, project.priority, project.due_date))

        project.id = cursor.lastrowid
        print(f"Project '{project.name}' saved with ID {project.id}")
