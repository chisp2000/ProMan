import sqlite3

connection = sqlite3.connect('projects')

cursor = connection.cursor()

create_project =  """CREATE TABLE IF NOT EXISTS project(project_id INTEGER PRIMARY KEY, location KEY)"""

cursor.execute(create_project)