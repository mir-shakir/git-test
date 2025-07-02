import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timezone


load_dotenv()


class SyncUtils:
    def __init__(self, db):
        self.db = db
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials missing in .env")
        self.supabase = create_client(supabase_url, supabase_key)

    def sync_with_remote(self):
        try:
            print("Sync started...")

            # Test Supabase connection
            response = self.supabase.table("notes").select("*", count="exact").execute()
            if not response or not hasattr(response, "data"):
                raise Exception("Failed to verify Supabase connection")

            print("Supabase connection verified.")

            # Push local changes to remote
            local_notes = self.db.get_all_local_notes()
            for note in local_notes:
                data = {
                    "id": note[0],
                    "title": note[1],
                    "content": note[2],
                    "created_at": note[3],
                    "updated_at": note[4],
                    "deleted": note[5],
                }
                response = self.supabase.table("notes").upsert(data).execute()
                if not response or not hasattr(response, "data"):
                    raise Exception(f"Supabase upsert error: {response}")

            print("Local changes pushed to remote.")

            # Fetch remote notes and sync locally
            response = self.supabase.table("notes").select("*").execute()
            if not response or not hasattr(response, "data"):
                raise Exception("Error fetching remote notes.")

            remote_notes = response.data
            for r_note in remote_notes:
                local_note = self.db.local_conn.execute(
                    "SELECT * FROM notes WHERE id=?", (r_note["id"],)
                ).fetchone()

                remote_updated = datetime.fromisoformat(r_note["updated_at"]).replace(
                    tzinfo=timezone.utc
                )
                if local_note:
                    local_updated = datetime.fromisoformat(local_note[4]).replace(
                        tzinfo=timezone.utc
                    )

                    if remote_updated > local_updated:
                        # Update local note if remote is newer
                        self.db.local_conn.execute(
                            """
                            UPDATE notes 
                            SET title=?, content=?, updated_at=?, deleted=? 
                            WHERE id=?
                        """,
                            (
                                r_note["title"],
                                r_note["content"],
                                r_note["updated_at"],
                                r_note["deleted"],
                                r_note["id"],
                            ),
                        )
                else:
                    # Insert new note locally if it doesn't exist
                    self.db.local_conn.execute(
                        """
                        INSERT INTO notes (id, title, content, created_at, updated_at, deleted)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            r_note["id"],
                            r_note["title"],
                            r_note["content"],
                            r_note["created_at"],
                            r_note["updated_at"],
                            r_note["deleted"],
                        ),
                    )

            # Clean up deleted notes locally
            self.db.local_conn.execute("DELETE FROM notes WHERE deleted=1")
            self.db.local_conn.commit()

            print("Sync completed successfully.")
            return True

        except Exception as e:
            print(f"Sync error: {e}")
            self.db.local_conn.rollback()
            raise
