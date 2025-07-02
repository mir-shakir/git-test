import customtkinter as ctk
from tkinter import ttk, messagebox


class NoteList(ctk.CTkScrollableFrame):
    def __init__(self, parent, db, on_note_select):
        super().__init__(
            parent,
            fg_color="transparent",
            corner_radius=0
        )
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.db = db
        self.on_note_select = on_note_select
        self.all_notes = []  # Store all notes for filtering

        # Configure Treeview style
        style = ttk.Style()
        style.configure(
            "Minimal.Treeview",
            background="#262626",
            foreground="#ffffff",
            fieldbackground="#262626",
            font=("Inter", 12),
            rowheight=36,
            borderwidth=0
        )
        style.map(
            "Minimal.Treeview",
            background=[("selected", "#404040")],
            foreground=[("selected", "#ffffff")]
        )

        # Create Treeview with better column configuration
        self.treeview = ttk.Treeview(
            self,
            style="Minimal.Treeview",
            columns=("title",),
            show="tree",
            selectmode="browse"
        )
        self.treeview.pack(fill="both", expand=True)
        
        # Configure column to expand with window
        self.treeview.column("#0", width=0, stretch=False)  # Hide the first column
        self.treeview.column("title", width=200, stretch=True)  # Make title column expandable
        
        # Bind selection event
        self.treeview.bind("<<TreeviewSelect>>", self._on_tree_select)
        
        self.refresh()

    def refresh(self):
        """Refresh the note list."""
        self.treeview.delete(*self.treeview.get_children())
        self.all_notes = self.db.get_local_notes()
        self._populate_treeview(self.all_notes)

    def filter_notes(self, search_text):
        """Filter notes based on search text."""
        self.treeview.delete(*self.treeview.get_children())
        
        if not search_text:
            # If search is empty, show all notes
            self._populate_treeview(self.all_notes)
        else:
            # Filter notes based on search text
            filtered_notes = [
                note for note in self.all_notes
                if search_text in note[1].lower()  # Search in title
                or (note[2] and search_text in note[2].lower())  # Search in content
            ]
            self._populate_treeview(filtered_notes)

    def _populate_treeview(self, notes):
        """Helper method to populate the treeview with given notes."""
        for note in notes:
            self.treeview.insert("", "end", values=(note[1],))

    def _on_tree_select(self, event):
        """Handle note selection."""
        selection = self.treeview.selection()
        if selection:
            item = selection[0]
            title = self.treeview.item(item)['values'][0]
            # Find the corresponding note from all_notes
            selected_note = next(
                (note for note in self.all_notes if note[1] == title),
                None
            )
            if selected_note:
                self.on_note_select(selected_note)
