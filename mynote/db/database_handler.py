import sqlite3
from datetime import datetime


class DatabaseHandler:
    def __init__(self):
        self.local_conn = sqlite3.connect("notes.db", check_same_thread=False)
        self.create_local_table()

    def create_local_table(self):
        cursor = self.local_conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                created_at TEXT,
                updated_at TEXT,
                deleted INTEGER DEFAULT 0
            )
        """
        )
        self.local_conn.commit()

    

    def get_local_notes(self):
        """Retrieve all non-deleted notes."""
        cursor = self.local_conn.cursor()
        cursor.execute("SELECT * FROM notes WHERE deleted=0 ORDER BY updated_at DESC")
        return cursor.fetchall()

    def get_all_local_notes(self):
        """Retrieve all notes, including deleted ones."""
        cursor = self.local_conn.cursor()
        cursor.execute("SELECT * FROM notes ORDER BY updated_at DESC")
        return cursor.fetchall()

    def get_note_by_title(self, title):
        """Retrieve a note by its title."""
        cursor = self.local_conn.cursor()
        cursor.execute("SELECT * FROM notes WHERE title=? AND deleted=0", (title,))
        return cursor.fetchone()

    def add_local_note(self, title, content):
        """Insert a new note into the local database."""
        cursor = self.local_conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO notes (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (title, content, now, now),
        )
        self.local_conn.commit()

    def update_local_note(self, note_id, title, content):
        """Update an existing note."""
        cursor = self.local_conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            "UPDATE notes SET title=?, content=?, updated_at=? WHERE id=?",
            (title, content, now, note_id),
        )
        self.local_conn.commit()

    def delete_local_note(self, note_id):
        """Mark a note as deleted."""
        cursor = self.local_conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("UPDATE notes SET deleted=1, updated_at=? WHERE id=?", (now, note_id))
        self.local_conn.commit()

    def delete_notes_permanently(self):
        """Delete all notes marked as deleted."""
        cursor = self.local_conn.cursor()
        cursor.execute("DELETE FROM notes WHERE deleted=1")
        self.local_conn.commit()
