import customtkinter as ctk
from tkinter import messagebox, TclError
from ui.note_list import NoteList
from ui.note_editor import NoteEditor
from utils.sync_utils import SyncUtils

class MainUI:
    def __init__(self, root, db):
        self.root = root
        self.db = db
        self.current_note = None
        self.sync_utils = SyncUtils(self.db)

        # Set dark theme by default
        ctk.set_appearance_mode("Dark")
        
        # Create main container
        self.main_container = ctk.CTkFrame(root, fg_color=("#ffffff", "#1e1e1e"))
        self.main_container.pack(fill="both", expand=True)

        # Create a fixed-width container for sidebar and toggle
        self.sidebar_container = ctk.CTkFrame(
            self.main_container,
            width=285,  # 280 + 5 for resizer
            fg_color="transparent"
        )
        self.sidebar_container.pack(side="left", fill="y")
        self.sidebar_container.pack_propagate(False)

        # Left sidebar (Note List)
        self.left_panel = ctk.CTkFrame(
            self.sidebar_container,
            width=280,
            fg_color=("#ebebeb", "#262626"),
            corner_radius=0
        )
        self.left_panel.pack(side="left", fill="y")
        self.left_panel.pack_propagate(False)

        # Minimal toggle button at the edge
        self.toggle_btn = ctk.CTkButton(
            self.sidebar_container,
            text="◀",  # Left arrow
            width=20,
            height=60,
            corner_radius=0,
            font=("Inter", 12),
            fg_color=("#cdcdcd", "#404040"),
            hover_color=("#b0b0b0", "#505050"),
            text_color=("#1e1e1e", "#ffffff"),
            command=self.toggle_sidebar
        )
        self.toggle_btn.place(relx=1, rely=0.5, anchor="e")

        # Sidebar toolbar
        sidebar_toolbar = ctk.CTkFrame(
            self.left_panel,
            fg_color="transparent",
            height=40
        )
        sidebar_toolbar.pack(fill="x", padx=10, pady=(10, 0))

        # Search box in sidebar
        self.search_entry = ctk.CTkEntry(
            sidebar_toolbar,
            placeholder_text="Search notes...",
            height=32,
            corner_radius=6,
            border_width=1,
            fg_color=("#f0f0f0", "#363636")
        )
        self.search_entry.pack(fill="x", expand=True)
        self.search_entry.bind('<KeyRelease>', self.search_notes)

        # Notes list
        self.note_list = NoteList(self.left_panel, self.db, self.load_note_content)

        # Fixed-width editor container
        editor_container = ctk.CTkFrame(
            self.main_container,
            fg_color=("#ffffff", "#1e1e1e"),
            corner_radius=0
        )
        editor_container.pack(side="left", fill="both", expand=True, padx=20)

        # Top toolbar with fixed width
        toolbar = ctk.CTkFrame(
            editor_container,
            fg_color="transparent",
            height=50
        )
        toolbar.pack(fill="x", pady=(10, 0))

        # Button container for fixed positioning - left side
        left_button_container = ctk.CTkFrame(toolbar, fg_color="transparent")
        left_button_container.pack(side="left", padx=20)

        # Button container for right side
        right_button_container = ctk.CTkFrame(toolbar, fg_color="transparent")
        right_button_container.pack(side="right", padx=20)

        # Modern button style
        button_style = {
            "corner_radius": 6,
            "height": 32,
            "font": ("Inter", 12),
            "text_color": ("#ffffff", "#ffffff"),
            "width": 75,
            "border_spacing": 8
        }

        # New and Save buttons (left side)
        ctk.CTkButton(
            left_button_container,
            text="New",
            command=self.new_note,
            fg_color=("#2d63b5", "#2d63b5"),
            hover_color=("#245091", "#245091"),
            **button_style
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            left_button_container,
            text="Save",
            command=self.save_note,
            fg_color=("#2d63b5", "#2d63b5"),
            hover_color=("#245091", "#245091"),
            **button_style
        ).pack(side="left")

        # Sync button with status indicator (right side)
        self.sync_frame = ctk.CTkFrame(right_button_container, fg_color="transparent")
        self.sync_frame.pack(side="left", padx=(0, 6))
        
        self.sync_status = ctk.CTkLabel(
            self.sync_frame,
            text="●",  # Dot indicator
            font=("Inter", 12),
            text_color="#45a049",  # Green for synced
            width=8
        )
        self.sync_status.pack(side="left", padx=(0, 2))

        self.sync_button = ctk.CTkButton(
            self.sync_frame,
            text="Sync",
            command=self.sync_notes,
            fg_color=("#45a049", "#45a049"),
            hover_color=("#3d8b40", "#3d8b40"),
            **button_style
        )
        self.sync_button.pack(side="left")

        # Delete button (right side)
        ctk.CTkButton(
            right_button_container,
            text="Delete",
            command=self.delete_note,
            fg_color=("#dc3545", "#dc3545"),
            hover_color=("#c82333", "#c82333"),
            **button_style
        ).pack(side="left")

        # Editor frame with title and content
        self.note_editor = NoteEditor(editor_container)

    def load_note_content(self, note):
        """Load a note into the editor when selected."""
        self.current_note = note
        self.note_editor.load_note_content(note)

    def save_note(self):
        """Save a new or updated note."""
        title, content = self.note_editor.get_note_data()

        if not title:
            return messagebox.showerror("Error", "Title is required!")

        if self.current_note:  # Update an existing note
            self.db.update_local_note(self.current_note[0], title, content)
        else:  # Create a new note
            self.db.add_local_note(title, content)

        self.note_list.refresh()
        self.note_editor.clear_note()
        self.current_note = None

    def new_note(self):
        """Clear the editor for a new note."""
        self.current_note = None
        self.note_editor.clear_note()

    def delete_note(self):
        """Delete the currently selected note."""
        if self.current_note:
            self.db.delete_local_note(self.current_note[0])
            self.note_list.refresh()
            self.note_editor.clear_note()
            self.current_note = None
        else:
            messagebox.showerror("Error", "No note selected!")

    def sync_notes(self):
        """Synchronize notes with the remote server."""
        try:
            # Update status to syncing
            self.sync_status.configure(text="◌", text_color="#ffa500")  # Orange for syncing
            self.sync_button.configure(state="disabled")
            self.root.update()

            # Perform sync
            self.sync_utils.sync_with_remote()
            
            # Update UI
            self.note_list.refresh()
            
            # Show success status
            self.sync_status.configure(text="●", text_color="#45a049")  # Green for success
            
        except Exception as e:
            # Show error status
            self.sync_status.configure(text="●", text_color="#ff4444")  # Red for error
            
        finally:
            self.sync_button.configure(state="normal")

    def search_notes(self, event=None):
        """Filter notes based on search text"""
        search_text = self.search_entry.get().strip().lower()
        self.note_list.filter_notes(search_text)

    def resize_sidebar(self, event):
        """Handle sidebar resizing."""
        try:
            new_width = event.x_root - self.left_panel.winfo_rootx()
            if 200 <= new_width <= 500:
                self.left_panel.configure(width=new_width)
                self.sidebar_container.configure(width=new_width + 20)  # Add toggle width
                self.left_panel.pack_propagate(False)
                self.sidebar_container.pack_propagate(False)
        except TclError:
            pass

    def toggle_sidebar(self):
        """Toggle the sidebar visibility."""
        if self.left_panel.winfo_viewable():
            self.left_panel.pack_forget()
            self.toggle_btn.configure(text="▶")  # Right arrow when collapsed
        else:
            self.left_panel.pack(side="left", fill="y")
            self.toggle_btn.configure(text="◀")  # Left arrow when expanded
