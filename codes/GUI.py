import customtkinter as ctk
import tkinter as tk
import tkinter.messagebox
from tkinter import ttk
from tkcalendar import DateEntry
import json
from typing import Optional, Tuple, Dict, Any, List

# Import database functions
from database_operations import (
    add_product_db, get_product_info_db, get_all_products_db,
    update_product_db, delete_product_db, create_tables,
    save_sale_db, get_all_sales_db, get_sale_details_db,
    get_product_based_report_db
)


class CanteenInterface:
    """
    The main GUI class for the Canteen Application.
    Handles all user interactions, window management, and interfacing with the database.
    """
    def __init__(self, master: ctk.CTk) -> None:
        """
        Initialize the main application window.

        Args:
            master (ctk.CTk): The root window object.
        """
        self.master = master
        master.title("Canteen Application")
        self.columns: Tuple[str, ...] = ("Barcode", "Product Name", "Price (TL)", "Stock")

        # A main frame to hold the buttons
        main_frame = ctk.CTkFrame(master)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Buttons
        self.btn_add_product = ctk.CTkButton(main_frame, text="Add / Manage Products",
                                             command=self.list_products_interface,
                                             height=40)
        self.btn_add_product.pack(pady=10, padx=10, fill="x")

        self.btn_sell_product = ctk.CTkButton(main_frame, text="POS Screen", command=self.pos_interface,
                                              height=50, fg_color="#4CAF50", hover_color="#45a049")
        self.btn_sell_product.pack(pady=10, padx=10, fill="x")

        self.btn_view_sales = ctk.CTkButton(main_frame, text="Sales Reports",
                                            command=self.view_sales_interface, height=40)
        self.btn_view_sales.pack(pady=10, padx=10, fill="x")

        self.btn_exit = ctk.CTkButton(main_frame, text="Exit", command=master.quit, height=40, fg_color="#D32F2F",
                                      hover_color="#B71C1C")
        self.btn_exit.pack(pady=10, padx=10, fill="x")

    def view_sales_interface(self) -> None:
        """
        Opens the Sales Reports window.
        Allows users to view past sales receipts and generate product-based performance reports.
        """
        sales_window = ctk.CTkToplevel(self.master)
        sales_window.title("Sales Reports")
        sales_window.geometry("1024x768")
        sales_window.transient(self.master)
        sales_window.grab_set()

        tabview = ctk.CTkTabview(sales_window, width=250)
        tabview.pack(padx=20, pady=20, fill="both", expand=True)
        tabview.add("Sales by Receipt")
        tabview.add("Product-Based Report")

        # --- STYLING THE TREEVIEW ---
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2a2d2e", foreground="white", fieldbackground="#343638", borderwidth=0)
        style.map('Treeview', background=[('selected', '#22559b')])
        style.configure("Treeview.Heading", background="#565b5e", foreground="white", relief="flat",
                        font=('Calibri', 10, 'bold'))
        style.map("Treeview.Heading", background=[('active', '#3484F0')])

        # --- Tab 1: Sales by Receipt ---
        tab1 = tabview.tab("Sales by Receipt")
        main_frame_s1 = ctk.CTkFrame(tab1, fg_color="transparent")
        main_frame_s1.pack(fill='both', expand=True)

        left_frame = ctk.CTkFrame(main_frame_s1)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5), pady=5)
        ctk.CTkLabel(left_frame, text="Sales List", font=('Arial', 16, 'bold')).pack(pady=10)
        sales_tree = ttk.Treeview(left_frame, columns=('ID', 'Date', 'Total Amount'), show='headings')
        sales_tree.pack(fill='both', expand=True, padx=5, pady=5)

        right_frame = ctk.CTkFrame(main_frame_s1)
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0), pady=5)
        ctk.CTkLabel(right_frame, text="Details of Selected Sale", font=('Arial', 16, 'bold')).pack(pady=10)
        details_tree = ttk.Treeview(right_frame, columns=('Product', 'Quantity', 'Price'), show='headings')
        details_tree.pack(fill='both', expand=True, padx=5, pady=5)

        for col, text, width in [('ID', 'ID', 50), ('Date', 'Date', 120), ('Total Amount', 'Total (TL)', 120)]:
            sales_tree.heading(col, text=text)
            sales_tree.column(col, width=width)
        for col, text, width in [('Product', 'Product Name', 150), ('Quantity', 'Qty', 60),
                                 ('Price', 'Sale Price (TL)', 100)]:
            details_tree.heading(col, text=text)
            details_tree.column(col, width=width)

        def load_sales() -> None:
            """Fetches all sales from DB and populates the sales treeview."""
            for i in sales_tree.get_children(): sales_tree.delete(i)
            for sale_id, date, total in get_all_sales_db():
                sales_tree.insert('', 'end', values=(sale_id, date, f"{total:.2f}"))

        def show_sale_details(event: tk.Event) -> None:
            """
            Event handler for selecting a sale from the list.
            Displays the details (products) of the selected sale in the details treeview.
            """
            for i in details_tree.get_children(): details_tree.delete(i)
            selected_items = sales_tree.selection()
            if not selected_items: return
            selected_sale_id = sales_tree.item(selected_items[0])['values'][0]
            cart_json = get_sale_details_db(selected_sale_id)
            if cart_json:
                for barcode, details in json.loads(cart_json).items():
                    details_tree.insert('', 'end', values=(details['isim'], details['adet'], f"{details['fiyat']:.2f}"))

        sales_tree.bind('<<TreeviewSelect>>', show_sale_details)
        load_sales()

        # --- Tab 2: Product-Based Report ---
        tab2 = tabview.tab("Product-Based Report")
        top_frame_s2 = ctk.CTkFrame(tab2, fg_color="transparent")
        top_frame_s2.pack(pady=10, padx=10, fill='x')

        ctk.CTkLabel(top_frame_s2, text="Start:").pack(side='left')
        cal_start = DateEntry(top_frame_s2, width=12, date_pattern='dd.mm.yyyy')
        cal_start.pack(side='left', padx=(5, 20))
        ctk.CTkLabel(top_frame_s2, text="End:").pack(side='left')
        cal_end = DateEntry(top_frame_s2, width=12, date_pattern='dd.mm.yyyy')
        cal_end.pack(side='left', padx=5)

        report_tree = ttk.Treeview(tab2, columns=('Product', 'Quantity', 'Revenue'), show='headings')
        report_tree.heading('Product', text='Product Name')
        report_tree.heading('Quantity', text='Total Quantity Sold')
        report_tree.heading('Revenue', text='Total Revenue (TL)')
        report_tree.pack(pady=10, padx=10, fill='both', expand=True)

        lbl_grand_total = ctk.CTkLabel(tab2, text="Grand Total Revenue: 0.00 TL", font=('Arial', 16, 'bold'))
        lbl_grand_total.pack(pady=10)

        def get_product_report() -> None:
            """
            Generates and displays a report of sold products within the selected date range.
            """
            for i in report_tree.get_children(): report_tree.delete(i)
            start_date = cal_start.get_date().strftime('%Y-%m-%d')
            end_date = cal_end.get_date().strftime('%Y-%m-%d')
            results = get_product_based_report_db(start_date, end_date)

            if isinstance(results, str) and results.startswith("HATA"):  # "HATA" is Turkish, changing to "ERROR"
                tkinter.messagebox.showerror("Database Error",
                                             f"Could not retrieve report.\n\nDetails: {results}\n\nPlease ensure your SQLite version is up-to-date.")
                return

            grand_total = 0
            for product_name, total_qty, total_revenue in results:
                report_tree.insert('', 'end', values=(product_name, total_qty, f"{total_revenue:.2f}"))
                if total_revenue: grand_total += total_revenue

            lbl_grand_total.configure(text=f"Grand Total Revenue: {grand_total:.2f} TL")

        btn_get_report = ctk.CTkButton(top_frame_s2, text="Get Report", command=get_product_report)
        btn_get_report.pack(side='left', padx=20)

    def add_product_interface(self) -> None:
        """
        Opens the dialog window to add a new product to the inventory.
        """
        add_product_window = ctk.CTkToplevel(self.master)
        add_product_window.title("Add New Product")
        add_product_window.geometry("600x400")
        add_product_window.transient(self.master)
        add_product_window.grab_set()
        add_product_window.grid_columnconfigure(1, weight=1)

        lbl_font = ("Arial", 14)

        ctk.CTkLabel(add_product_window, text="Barcode:", font=lbl_font).grid(row=0, column=0, padx=20, pady=10,
                                                                              sticky="w")
        ent_barcode = ctk.CTkEntry(add_product_window, font=lbl_font, height=35)
        ent_barcode.grid(row=0, column=1, padx=20, pady=10, sticky='ew')

        add_product_window.after(100, lambda: ent_barcode.focus_set())

        ctk.CTkLabel(add_product_window, text="Product Name:", font=lbl_font).grid(row=1, column=0, padx=20, pady=10,
                                                                                   sticky="w")
        ent_product_name = ctk.CTkEntry(add_product_window, font=lbl_font, height=35)
        ent_product_name.grid(row=1, column=1, padx=20, pady=10, sticky='ew')

        ctk.CTkLabel(add_product_window, text="Price (TL):", font=lbl_font).grid(row=2, column=0, padx=20, pady=10,
                                                                                 sticky="w")
        ent_price = ctk.CTkEntry(add_product_window, font=lbl_font, height=35)
        ent_price.grid(row=2, column=1, padx=20, pady=10, sticky='ew')

        ctk.CTkLabel(add_product_window, text="Stock Quantity:", font=lbl_font).grid(row=3, column=0, padx=20, pady=10,
                                                                                     sticky="w")
        ent_stock = ctk.CTkEntry(add_product_window, font=lbl_font, height=35)
        ent_stock.insert(0, "0")
        ent_stock.grid(row=3, column=1, padx=20, pady=10, sticky='ew')

        def process_add_product(event: Optional[tk.Event] = None) -> None:
            """Validates input and saves the new product to the database."""
            barcode, product_name = ent_barcode.get(), ent_product_name.get()
            if not barcode or not product_name:
                tkinter.messagebox.showerror("Error", "Barcode and Product Name fields cannot be empty.")
                return
            try:
                price, stock = float(ent_price.get()), int(ent_stock.get())
                if add_product_db(barcode, product_name, price, stock):
                    add_product_window.destroy()
                    self.refresh_product_list()
                else:
                    tkinter.messagebox.showerror("Error", "A product with this barcode already exists.")
            except ValueError:
                tkinter.messagebox.showerror("Error", "Please enter valid numbers for Price and Stock.")

        btn_add = ctk.CTkButton(add_product_window, text="Save Product", command=process_add_product, height=40)
        btn_add.grid(row=4, column=0, columnspan=2, padx=20, pady=20, sticky='ew')
        add_product_window.bind("<Return>", process_add_product)

    def pos_interface(self) -> None:
        """
        Opens the Point of Sale (POS) window.
        Handles checking out items, managing the cart, and detecting barcodes.
        """
        pos_window = ctk.CTkToplevel(self.master)
        pos_window.transient(self.master)
        pos_window.grab_set()
        pos_window.title("Point of Sale")
        pos_window.geometry("700x700")

        top_frame = ctk.CTkFrame(pos_window, fg_color="transparent")
        top_frame.pack(fill='x', padx=20, pady=10)
        ctk.CTkLabel(top_frame, text="Scan Barcode:", font=("Arial", 14)).pack(side='left')

        self.barcode_var = ctk.StringVar()
        self.ent_barcode = ctk.CTkEntry(top_frame, height=40, font=("Arial", 16), textvariable=self.barcode_var)
        self.ent_barcode.pack(side='left', fill='x', expand=True, padx=10)

        pos_window.after(100, lambda: self.ent_barcode.focus_set())

        pos_window.after(100, lambda: self.ent_barcode.focus_set())

        # Cart structure: {barcode: {"isim": str, "fiyat": float, "adet": int}}
        self.cart: Dict[str, Dict[str, Any]] = {}
        self.lbl_cart_total = ctk.CTkLabel(pos_window, text="Cart Total: 0.00 TL", font=("Arial", 22, "bold"))
        self.lbl_cart_total.pack(pady=10)

        self.cart_listbox = tk.Listbox(pos_window, bg="#2B2B2B", fg="white", selectbackground="#1F6AA5",
                                       font=("Arial", 14), borderwidth=0, highlightthickness=0)
        self.cart_listbox.pack(padx=20, pady=10, fill='both', expand=True)

        bottom_frame = ctk.CTkFrame(pos_window, fg_color="transparent")
        bottom_frame.pack(fill='x', padx=20, pady=20)

        btn_reduce_qty = ctk.CTkButton(bottom_frame, text="Reduce Quantity", command=self.remove_from_cart, height=40,
                                       fg_color="#D32F2F", hover_color="#B71C1C")
        btn_reduce_qty.pack(side=tk.LEFT, padx=10)
        btn_confirm = ctk.CTkButton(bottom_frame, text="Confirm Sale", command=self.confirm_sale, height=40,
                                    fg_color="#4CAF50", hover_color="#45a049")
        btn_confirm.pack(side=tk.RIGHT, padx=10)

        self.barcode_var.trace_add("write", self.on_barcode_change)
        self.ent_barcode.bind("<space>", self.add_to_cart)
        pos_window.bind("<Return>", self.confirm_sale)

    def on_barcode_change(self, *args: Any) -> None:
        """Listener for barcode entry updates. Auto-adds product if 13 digits detected."""
        current_barcode = self.barcode_var.get()
        if len(current_barcode) == 13:
            print(f"13-digit barcode detected: {current_barcode}. Adding automatically...")
            self.add_to_cart(event=None)

    def add_to_cart(self, event: Optional[tk.Event] = None) -> None:
        """
        Adds a product to the cart based on the entered barcode.
        Checks stock availability before adding.
        """
        barcode = self.ent_barcode.get()
        self.ent_barcode.delete(0, ctk.END)
        if not barcode: return
        product = get_product_info_db(barcode)
        if product:
            barcode, product_name, price, stock = product
            qty_in_cart = self.cart.get(barcode, {}).get("adet", 0)
            if stock <= qty_in_cart:
                tkinter.messagebox.showwarning("Out of Stock", f"No more stock available for '{product_name}'!")
                return
            if barcode in self.cart:
                self.cart[barcode]["adet"] += 1
            else:
                self.cart[barcode] = {"isim": product_name, "fiyat": price, "adet": 1}
            self.refresh_cart()
        else:
            tkinter.messagebox.showerror("Error", "Product with this barcode not found.")

    def remove_from_cart(self) -> None:
        """
        Removes the selected item from the shopping cart.
        Decrements quantity if > 1, otherwise removes the item completely.
        """
        try:
            selected_index = self.cart_listbox.curselection()[0]
        except IndexError:
            tkinter.messagebox.showwarning("Warning", "Please select a product from the cart to remove.")
            return

        selected_text = self.cart_listbox.get(selected_index)
        barcode_to_remove = None
        for barcode, details in self.cart.items():
            listbox_text = f"{details['isim']} - Adet: {details['adet']} - Fiyat: {details['fiyat']:.2f} TL"
            if listbox_text == selected_text:
                barcode_to_remove = barcode
                break

        if barcode_to_remove:
            if self.cart[barcode_to_remove]['adet'] > 1:
                self.cart[barcode_to_remove]['adet'] -= 1
            else:
                del self.cart[barcode_to_remove]
            self.refresh_cart()

    def refresh_cart(self) -> None:
        """Updates the cart listbox and total price label."""
        self.cart_listbox.delete(0, tk.END)
        total_price = 0
        for item in self.cart.values():
            total_price += item["fiyat"] * item["adet"]
            self.cart_listbox.insert(tk.END, f"{item['isim']} - Adet: {item['adet']} - Fiyat: {item['fiyat']:.2f} TL")
        self.lbl_cart_total.configure(text=f"Cart Total: {total_price:.2f} TL")

    def confirm_sale(self, event: Optional[tk.Event] = None) -> None:
        """
        Finalizes the sale.
        Updates stock in the database and records the sale transaction.
        """
        if not self.cart:
            tkinter.messagebox.showerror("Error", "Cart is empty.")
            return

        total_price = sum(item['fiyat'] * item['adet'] for item in self.cart.values())

        for barcode, details in self.cart.items():
            product_db = get_product_info_db(barcode)
            if not product_db or product_db[3] < details['adet']:
                tkinter.messagebox.showerror("Stock Error", f"Not enough stock for '{details['isim']}! Sale canceled.")
                return

        for barcode, details in self.cart.items():
            product_db = get_product_info_db(barcode)
            new_stock = product_db[3] - details['adet']
            update_product_db(barcode, stock=new_stock)

        if save_sale_db(self.cart, total_price):
            print("Sale successfully saved to 'sales' table.")
        else:
            tkinter.messagebox.showwarning("Save Error",
                                           "Stock was updated, but there was an issue saving the sale record.")

        self.cart.clear()
        self.refresh_cart()
        self.ent_barcode.focus_set()

    def list_products_interface(self) -> None:
        """
        Opens the Inventory Management window.
        Lists all products and allows editing or deleting them.
        """
        product_list_window = ctk.CTkToplevel(self.master)
        product_list_window.title("Inventory Management")
        product_list_window.geometry("1024x768")
        product_list_window.transient(self.master)
        product_list_window.grab_set()

        top_frame = ctk.CTkFrame(product_list_window, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=10)

        btn_new_product = ctk.CTkButton(top_frame, text="Add New Product", command=self.add_product_interface)
        btn_new_product.pack(side="left")

        self.product_table = ttk.Treeview(product_list_window, columns=self.columns, show='headings')
        self.product_table.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        for col in self.columns:
            self.product_table.heading(col, text=col)

        self.refresh_product_list()

        self.product_table.bind("<Double-1>", self.edit_cell)
        self.editing_cell, self.edit_entry = None, None

        bottom_frame = ctk.CTkFrame(product_list_window, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=10, pady=10)
        btn_delete = ctk.CTkButton(bottom_frame, text="Delete Selected Product", command=self.delete_selected_product,fg_color="#D32F2F", hover_color="#B71C1C")
        btn_delete.pack(pady=10)

    def refresh_product_list(self) -> None:
        """Refreshes the product treeview with the latest data from the database."""
        for i in self.product_table.get_children(): self.product_table.delete(i)
        products = get_all_products_db()
        if products:
            for barcode, product_name, price, stock in products:
                self.product_table.insert("", tk.END, values=(barcode, product_name, f"{price:.2f}", stock))

    def delete_selected_product(self) -> None:
        """Deletes the selected product from the database after confirmation."""
        selected_items = self.product_table.selection()
        if not selected_items:
            tkinter.messagebox.showwarning("Warning", "Please select a product to delete.")
            return

        selected_id = selected_items[0]
        product_info = self.product_table.item(selected_id, 'values')
        barcode, product_name = product_info[0], product_info[1]

        are_you_sure = tkinter.messagebox.askyesno("Confirm Deletion", f"Are you sure?\n\nThe product '{product_name}' (Barcode: {barcode}) will be permanently deleted.")
        if are_you_sure:
            if delete_product_db(barcode):
                self.product_table.delete(selected_id)
                tkinter.messagebox.showinfo("Success", f"Product '{product_name}' has been successfully deleted.")
            else:
                tkinter.messagebox.showerror("Error", "A database error occurred while deleting the product.")

    def edit_cell(self, event: tk.Event) -> None:
        """
        Initiates inline editing of a product cell (Name, Price, or Stock).
        Triggered by a double-click event on the treeview.
        """
        if self.edit_entry:
            self.cancel_edit()

        row_id = self.product_table.identify_row(event.y)
        col_id = self.product_table.identify_column(event.x)

        if not row_id or col_id == '#1':
            return

        x, y, width, height = self.product_table.bbox(row_id, col_id)
        current_value = self.product_table.set(row_id, col_id)

        self.edit_entry = ctk.CTkEntry(self.product_table.master, width=width, height=height, border_width=0,corner_radius=0)
        self.edit_entry.place(x=x, y=y)
        self.edit_entry.insert(0, current_value)
        self.edit_entry.focus_set()

        column_index = int(col_id.replace('#', '')) - 1
        self.editing_cell = (row_id, col_id, column_index)

        self.edit_entry.bind("<Return>", self.save_edit)
        self.edit_entry.bind("<FocusOut>", self.cancel_edit)
        self.edit_entry.bind("<Escape>", self.cancel_edit)

    def save_edit(self, event: tk.Event) -> None:
        """
        Saves the edited cell value to the database.
        Validates the input before updating.
        """
        if not self.editing_cell: return

        row_id, col_id, column_index = self.editing_cell
        column_name = self.columns[column_index]
        new_value = self.edit_entry.get()
        barcode = self.product_table.set(row_id, '#1')

        update_successful = False
        try:
            if column_name == "Product Name":
                if new_value:
                    update_successful = update_product_db(barcode, product_name=new_value)
            elif column_name == "Price (TL)":
                clean_value = float(new_value.replace("TL", "").strip())
                update_successful = update_product_db(barcode, price=clean_value)
                new_value = f"{clean_value:.2f}"
            elif column_name == "Stock":
                update_successful = update_product_db(barcode, stock=int(new_value))
        except ValueError:
            tkinter.messagebox.showerror("Error", f"Invalid value entered for '{column_name}': {new_value}")
            self.cancel_edit()
            return

        if update_successful:
            self.product_table.set(row_id, col_id, new_value)
            print(f"Product with barcode '{barcode}' updated: {column_name} -> {new_value}")
        else:
            print("Database update failed or no change was made.")

        self.cancel_edit()

    def cancel_edit(self, event: Optional[tk.Event] = None) -> None:
        """Cancels the current editing operation and removes the entry widget."""
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None
            self.editing_cell = None