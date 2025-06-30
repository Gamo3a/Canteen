import customtkinter as ctk
from GUI import CanteenInterface
from database_operations import create_tables

if __name__ == "__main__":
    create_tables()
    root = ctk.CTk()
    root.geometry("400x500")
    Interface = CanteenInterface(root)
    root.mainloop()