import customtkinter as ctk
from db.database_handler import DatabaseHandler
from ui.main_ui import MainUI


class NoteTakingApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db = DatabaseHandler()
        self.title("Modern Notes")
        self.geometry("1200x800")
        self.resizable(True, True)
        
        # Set modern appearance
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        # Configure grid weight
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        MainUI(self, self.db)


if __name__ == "__main__":
    app = NoteTakingApp()
    app.mainloop()
