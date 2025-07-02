import customtkinter as ctk


class NoteEditor:
    def __init__(self, parent):
        self.parent = parent
        
        # Editor container
        editor_frame = ctk.CTkFrame(parent, fg_color="transparent")
        editor_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        # Title entry with centered text
        self.title_entry = ctk.CTkEntry(
            editor_frame,
            placeholder_text="Untitled Note",
            height=50,
            font=("Inter", 28),
            fg_color="transparent",
            border_width=0,
            placeholder_text_color=("#666666", "#888888"),
            justify="center"  # Center the text
        )
        self.title_entry.pack(fill="x", pady=(10, 20))

        # Divider
        divider = ctk.CTkFrame(
            editor_frame,
            height=1,
            fg_color=("#cdcdcd", "#404040")
        )
        divider.pack(fill="x", pady=(0, 20))

        # Content editor
        self.content_text = ctk.CTkTextbox(
            editor_frame,
            font=("Inter", 14),
            fg_color="transparent",
            border_width=0,
            wrap="word"
        )
        self.content_text.pack(fill="both", expand=True)

    def load_note_content(self, note):
        """Load the selected note into the editor."""
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, note[1])  # Note title

        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", note[2])  # Note content

    def get_note_data(self):
        """Retrieve the title and content from the editor."""
        title = self.title_entry.get()
        content = self.content_text.get("1.0", "end").strip()
        return title, content

    def clear_note(self):
        """Clear the editor for creating a new note."""
        self.title_entry.delete(0, "end")
        self.content_text.delete("1.0", "end")
