import sqlite3
from typing import List
from db_models import Project, LogEntry, Attachment # Import models

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

    def create_log(self, project_id: int, content: str, timestamp: str):
        """Creates a new log entry, effectively adding a 'Day' to the list."""
        sql = "INSERT INTO log (project_id, content, timestamp) VALUES (?, ?, ?)"
        self._execute_sql(sql, (project_id, content, timestamp))
        print(f"Log added for project {project_id} on {timestamp}")

    def delete_logs_for_date(self, project_id: int, date_str: str):
        """Deletes ALL logs (and their attachments) for a specific date."""
        try:
            # 1. Delete attachments linked to logs on this date
            self._execute_sql(
                """
                DELETE FROM attachment 
                WHERE log_id IN (
                    SELECT log_id FROM log WHERE project_id = ? AND timestamp = ?
                )
                """, 
                (project_id, date_str)
            )

            # 2. Delete the logs themselves
            self._execute_sql(
                "DELETE FROM log WHERE project_id = ? AND timestamp = ?", 
                (project_id, date_str)
            )
            print(f"All logs for {date_str} deleted.")
            
        except sqlite3.Error as e:
            print(f"Error deleting logs for date: {e}")
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

    def update_log_content(self, log_id: int, new_content: str):
        """Updates the text content of a specific log entry."""
        sql = "UPDATE log SET content = ? WHERE log_id = ?"
        self._execute_sql(sql, (new_content, log_id))
        print(f"Log {log_id} updated.")

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
            project_id INTEGER,
            file_path TEXT NOT NULL,
            is_global INTEGER DEFAULT 0,
            is_thumbnail INTEGER DEFAULT 0,
            FOREIGN KEY(log_id) REFERENCES log(log_id),
            FOREIGN KEY(project_id) REFERENCES project(project_id)
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
    
    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """Fetches a single project by ID."""
        sql = "SELECT project_id, name, priority, due_date, thumbnail_path FROM project WHERE project_id = ?"
        rows = self._execute_query(sql, (project_id,))
        
        if rows:
            row = rows[0]
            return Project(
                id=row['project_id'],
                name=row['name'],
                priority=row['priority'],
                due_date=row['due_date'],
                thumbnail_path=row['thumbnail_path']
            )
        return None

    def update_project(self, project: Project):
        """Updates an existing project record."""
        sql = """
        UPDATE project 
        SET name = ?, priority = ?, due_date = ?, thumbnail_path = ?
        WHERE project_id = ?
        """
        params = (project.name, project.priority, project.due_date, project.thumbnail_path, project.id)
        self._execute_sql(sql, params)
        print(f"Project ID {project.id} updated successfully.")

    def get_log_dates(self, project_id: int) -> List[str]:
        """Fetches distinct dates where logs exist for a project."""
        sql = """
        SELECT DISTINCT timestamp 
        FROM log 
        WHERE project_id = ? 
        ORDER BY timestamp DESC
        """
        rows = self._execute_query(sql, (project_id,))
        return [row['timestamp'] for row in rows]

    def get_logs_by_date(self, project_id: int, date_str: str) -> List[LogEntry]:
        """Fetches logs for a specific project and date."""
        sql = "SELECT * FROM log WHERE project_id = ? AND timestamp = ? ORDER BY log_id DESC"
        rows = self._execute_query(sql, (project_id, date_str))
        return [LogEntry(id=r['log_id'], project_id=r['project_id'], timestamp=r['timestamp'], content=r['content']) for r in rows]

    def get_project_attachments(self, project_id: int) -> List[Attachment]:
        """Fetches all attachments linked to a project (via logs)."""
        # Complex join to get attachments linked to any log of this project
        sql = """
        SELECT a.* FROM attachment a
        JOIN log l ON a.log_id = l.log_id
        WHERE l.project_id = ?
        """
        rows = self._execute_query(sql, (project_id,))
        return [Attachment(id=r['attachment_id'], log_id=r['log_id'], file_path=r['file_path'], is_thumbnail=r['is_thumbnail']) for r in rows]
    
    def add_attachment(self, file_path: str, project_id: int = None, is_global: bool = False):
        """Adds a new attachment record."""
        sql = "INSERT INTO attachment (file_path, project_id, is_global) VALUES (?, ?, ?)"
        self._execute_sql(sql, (file_path, project_id, 1 if is_global else 0))

    def get_viewable_attachments(self, project_id: int) -> List[Attachment]:
        """Fetches attachments that match the project ID OR are marked global."""
        sql = """
        SELECT * FROM attachment 
        WHERE project_id = ? OR is_global = 1
        """
        rows = self._execute_query(sql, (project_id,))
        return [Attachment(id=r['attachment_id'], file_path=r['file_path'], project_id=r['project_id'], is_global=bool(r['is_global'])) for r in rows]

    def get_all_attachments(self) -> List[Attachment]:
        """Fetches ALL attachments for the batch manager."""
        rows = self._execute_query("SELECT * FROM attachment")
        return [Attachment(id=r['attachment_id'], file_path=r['file_path'], project_id=r['project_id'], is_global=bool(r['is_global'])) for r in rows]

    def update_attachment_scope(self, attachment_id: int, is_global: bool):
        """Toggles the global status of an attachment."""
        self._execute_sql("UPDATE attachment SET is_global = ? WHERE attachment_id = ?", (1 if is_global else 0, attachment_id))

    def delete_attachment(self, attachment_id: int):
        self._execute_sql("DELETE FROM attachment WHERE attachment_id = ?", (attachment_id,))