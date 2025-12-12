import sqlite3
from typing import List, Optional
from db_models import Project, LogEntry, Attachment 

class DatabaseManager:
    def __init__(self, db_path: str = "projects.db"):
        self.db_path = db_path
        self.initialize_database()

    def _execute_sql(self, sql_command: str, params: tuple = ()):
        """Utility to connect, execute a command, and commit."""
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
        """Creates all necessary tables."""
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

    # --- PROJECT METHODS ---

    def save_project(self, project: Project):
        sql = "INSERT INTO project (name, priority, due_date, thumbnail_path) VALUES (?, ?, ?, ?)"
        params = (project.name, project.priority, project.due_date, project.thumbnail_path)
        cursor = self._execute_sql(sql, params)
        project.id = cursor.lastrowid

    def get_projects_sorted(self) -> List[Project]:
        sql = "SELECT * FROM project ORDER BY priority DESC, due_date ASC"
        rows = self._execute_query(sql)
        return [Project(id=r['project_id'], name=r['name'], priority=r['priority'], due_date=r['due_date'], thumbnail_path=r['thumbnail_path']) for r in rows]
    
    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        sql = "SELECT * FROM project WHERE project_id = ?"
        rows = self._execute_query(sql, (project_id,))
        if rows:
            r = rows[0]
            return Project(id=r['project_id'], name=r['name'], priority=r['priority'], due_date=r['due_date'], thumbnail_path=r['thumbnail_path'])
        return None

    def update_project(self, project: Project):
        sql = "UPDATE project SET name = ?, priority = ?, due_date = ?, thumbnail_path = ? WHERE project_id = ?"
        params = (project.name, project.priority, project.due_date, project.thumbnail_path, project.id)
        self._execute_sql(sql, params)

    def delete_project(self, project_id: int):
        # 1. Delete attachments linked to logs of this project
        self._execute_sql("DELETE FROM attachment WHERE log_id IN (SELECT log_id FROM log WHERE project_id = ?)", (project_id,))
        # 2. Delete project attachments (direct links)
        self._execute_sql("DELETE FROM attachment WHERE project_id = ?", (project_id,))
        # 3. Delete Logs
        self._execute_sql("DELETE FROM log WHERE project_id = ?", (project_id,))
        # 4. Delete Project
        self._execute_sql("DELETE FROM project WHERE project_id = ?", (project_id,))

    # --- LOG METHODS ---

    def create_log(self, project_id: int, content: str, timestamp: str):
        sql = "INSERT INTO log (project_id, content, timestamp) VALUES (?, ?, ?)"
        self._execute_sql(sql, (project_id, content, timestamp))

    def get_log_dates(self, project_id: int) -> List[str]:
        sql = "SELECT DISTINCT timestamp FROM log WHERE project_id = ? ORDER BY timestamp DESC"
        rows = self._execute_query(sql, (project_id,))
        return [row['timestamp'] for row in rows]

    def get_logs_by_date(self, project_id: int, date_str: str) -> List[LogEntry]:
        sql = "SELECT * FROM log WHERE project_id = ? AND timestamp = ? ORDER BY log_id DESC"
        rows = self._execute_query(sql, (project_id, date_str))
        return [LogEntry(id=r['log_id'], project_id=r['project_id'], timestamp=r['timestamp'], content=r['content']) for r in rows]

    def update_log_content(self, log_id: int, new_content: str):
        self._execute_sql("UPDATE log SET content = ? WHERE log_id = ?", (new_content, log_id))

    def delete_logs_for_date(self, project_id: int, date_str: str):
        # Delete attachments linked to these logs first
        self._execute_sql("DELETE FROM attachment WHERE log_id IN (SELECT log_id FROM log WHERE project_id = ? AND timestamp = ?)", (project_id, date_str))
        self._execute_sql("DELETE FROM log WHERE project_id = ? AND timestamp = ?", (project_id, date_str))

    # --- ATTACHMENT METHODS ---

    def add_attachment(self, file_path: str, project_id: int = None, is_global: bool = False):
        sql = "INSERT INTO attachment (file_path, project_id, is_global) VALUES (?, ?, ?)"
        self._execute_sql(sql, (file_path, project_id, 1 if is_global else 0))

    def get_viewable_attachments(self, project_id: int) -> List[Attachment]:
        sql = "SELECT * FROM attachment WHERE project_id = ? OR is_global = 1"
        rows = self._execute_query(sql, (project_id,))
        return [Attachment(id=r['attachment_id'], file_path=r['file_path'], project_id=r['project_id'], is_global=bool(r['is_global'])) for r in rows]

    def get_all_attachments(self) -> List[Attachment]:
        rows = self._execute_query("SELECT * FROM attachment")
        return [Attachment(id=r['attachment_id'], file_path=r['file_path'], project_id=r['project_id'], is_global=bool(r['is_global'])) for r in rows]

    def update_attachment_scope(self, attachment_id: int, is_global: bool):
        self._execute_sql("UPDATE attachment SET is_global = ? WHERE attachment_id = ?", (1 if is_global else 0, attachment_id))

    def delete_attachment(self, attachment_id: int):
        self._execute_sql("DELETE FROM attachment WHERE attachment_id = ?", (attachment_id,))