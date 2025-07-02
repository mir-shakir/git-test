import customtkinter as ctk
from tkinter import messagebox
import sqlite3
from supabase import create_client
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseHandler:

    def __init__(self):
        self.local_conn = sqlite3.connect('notes.db')
        self.create_local_table()

        # Verify Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("Missing Supabase credentials in .env file")

        self.supabase = create_client(supabase_url, supabase_key)

    def create_local_table(self):
        cursor = self.local_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')
        self.local_conn.commit()

    def get_local_notes(self):
        cursor = self.local_conn.cursor()
        cursor.execute("SELECT * FROM notes ORDER BY updated_at DESC")
        return cursor.fetchall()

    def add_local_note(self, title, content):
        cursor = self.local_conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("INSERT INTO notes (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
                      (title, content, now, now))
        self.local_conn.commit()
        return cursor.lastrowid

    def update_local_note(self, note_id, title, content):
        cursor = self.local_conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("UPDATE notes SET title=?, content=?, updated_at=? WHERE id=?",
                      (title, content, now, note_id))
        self.local_conn.commit()

    def delete_local_note(self, note_id):
        cursor = self.local_conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id=?", (note_id,))
        self.local_conn.commit()

    def sync_with_remote(self):
        try:
            print("hello sync started")

            response = self.supabase.table("notes").select("count", count="exact").execute()
            if not response or not hasattr(response, "data"):
                raise Exception(f"Failed to verify Supabase connection: {response}")

            print("first checkpoint passed")

            # Push local changes
            local_notes = self.get_local_notes()
            for note in local_notes:
                data = {
                    "id": note[0],
                    "title": note[1],
                    "content": note[2],
                    "created_at": note[3],
                    "updated_at": note[4]
                }
                response = self.supabase.table("notes").upsert(data).execute()
                if not response or not hasattr(response, "data"):
                    raise Exception(f"Supabase error during upsert: {response}")

            # Pull remote changes
            response = self.supabase.table("notes").select("*").execute()
            if not response or not hasattr(response, "data"):
                raise Exception(f"Supabase error during fetch: {response}")

            remote_notes = response.data
            # Merge remote changes into local database
            for r_note in remote_notes:
                cursor = self.local_conn.cursor()
                cursor.execute("SELECT * FROM notes WHERE id=?", (r_note['id'],))
                local_note = cursor.fetchone()

                if not local_note:
                    cursor.execute('''
                        INSERT INTO notes (id, title, content, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        r_note['id'],
                        r_note['title'],
                        r_note['content'],
                        r_note['created_at'],
                        r_note['updated_at']
                    ))
                else:
                    remote_updated = datetime.fromisoformat(r_note['updated_at'])
                    if remote_updated.tzinfo is None:
                        remote_updated = remote_updated.replace(tzinfo=timezone.utc)
                    local_updated = datetime.fromisoformat(local_note[4])
                    if local_updated.tzinfo is None:
                        local_updated = local_updated.replace(tzinfo=timezone.utc)
                    if remote_updated > local_updated:
                        cursor.execute('''
                            UPDATE notes 
                            SET title=?, content=?, updated_at=?
                            WHERE id=?
                        ''', (
                            r_note['title'],
                            r_note['content'],
                            r_note['updated_at'],
                            r_note['id']
                        ))

            self.local_conn.commit()
            print("Sync completed successfully.")
            return True
        except Exception as e:
            print(f"Sync error: {e}")
            self.local_conn.rollback()
            raise


class NoteTakingApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.db = DatabaseHandler()
        self.current_note = None

        self.title("Modern Notes")
        self.geometry("900x600")
        ctk.set_appearance_mode("System")  # Options: "Light", "Dark", "System"
        ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"

        # Create UI elements
        self.create_widgets()
        self.load_notes()

    def create_widgets(self):
        # Left panel - Note List
        left_panel = ctk.CTkFrame(self, width=300)
        left_panel.pack(side="left", fill="y", padx=10, pady=10)

        self.note_list = ctk.CTkScrollableFrame(left_panel)
        self.note_list.pack(fill="both", expand=True)

        # Right panel
        right_panel = ctk.CTkFrame(self)
        right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.title_entry = ctk.CTkEntry(right_panel, placeholder_text="Title")
        self.title_entry.pack(fill="x", padx=10, pady=10)

        self.content_text = ctk.CTkTextbox(right_panel, height=300)
        self.content_text.pack(fill="both", expand=True, padx=10, pady=10)

        button_frame = ctk.CTkFrame(right_panel)
        button_frame.pack(fill="x", pady=10)

        self.new_btn = ctk.CTkButton(button_frame, text="New", command=self.new_note)
        self.new_btn.pack(side="left", padx=5)

        self.save_btn = ctk.CTkButton(button_frame, text="Save", command=self.save_note)
        self.save_btn.pack(side="left", padx=5)

        self.delete_btn = ctk.CTkButton(button_frame, text="Delete", command=self.delete_note)
        self.delete_btn.pack(side="left", padx=5)

        self.sync_btn = ctk.CTkButton(button_frame, text="Sync", command=self.sync_notes)
        self.sync_btn.pack(side="right", padx=5)

    def load_notes(self):
        for widget in self.note_list.winfo_children():
            widget.destroy()

        notes = self.db.get_local_notes()
        for note in notes:
            note_button = ctk.CTkButton(
                self.note_list, text=note[1],
                command=lambda n=note: self.load_note_content(n),
                anchor="w"
            )
            note_button.pack(fill="x", padx=5, pady=2)

    def new_note(self):
        self.current_note = None
        self.title_entry.delete(0, "end")
        self.content_text.delete("1.0", "end")

    def save_note(self):
        title = self.title_entry.get()
        content = self.content_text.get("1.0", "end").strip()

        if not title:
            messagebox.showerror("Error", "Title is required")
            return

        if self.current_note:
            self.db.update_local_note(self.current_note[0], title, content)
        else:
            self.db.add_local_note(title, content)

        self.load_notes()
        self.new_note()

    def delete_note(self):
        if self.current_note:
            self.db.delete_local_note(self.current_note[0])
            self.load_notes()
            self.new_note()

    def load_note_content(self, note):
        self.current_note = note
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, note[1])
        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", note[2])

    def sync_notes(self):
        try:
            if self.db.sync_with_remote():
                messagebox.showinfo("Sync Complete", "Notes synchronized successfully")
                self.load_notes()
            else:
                messagebox.showerror("Sync Failed", "Could not sync with cloud storage")
        except Exception as e:
            messagebox.showerror("Sync Error", str(e))


if __name__ == "__main__":
    app = NoteTakingApp()
    app.mainloop()
