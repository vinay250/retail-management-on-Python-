import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import urllib.request

DB_NAME = 'retail_management.db'

# Database Functions
def create_database():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                quantity_sold INTEGER,
                total_price REAL,
                date TEXT,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        conn.commit()

def add_product(name, price, quantity):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO products (name, price, quantity)
                VALUES (?, ?, ?)
            ''', (name, price, quantity))
            conn.commit()
        return True, "Product added successfully."
    except sqlite3.IntegrityError:
        return False, "Product name already exists!"
    except Exception as e:
        return False, str(e)

def delete_product(product_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()

def get_all_products():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, price, quantity FROM products')
        return cursor.fetchall()

def update_product_quantity(product_id, new_quantity):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE products 
            SET quantity = ? 
            WHERE id = ?
        ''', (new_quantity, product_id))
        conn.commit()

def process_sale(product_id, quantity_sold):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT price, quantity 
                FROM products 
                WHERE id = ?
            ''', (product_id,))
            product = cursor.fetchone()
            
            if not product:
                return False, 'Product not found.'
                
            price, current_quantity = product
            if current_quantity < quantity_sold:
                return False, 'Insufficient stock.'
                
            total_price = price * quantity_sold
            cursor.execute('''
                UPDATE products 
                SET quantity = quantity - ? 
                WHERE id = ?
            ''', (quantity_sold, product_id))
            
            cursor.execute('''
                INSERT INTO sales (product_id, quantity_sold, total_price, date)
                VALUES (?, ?, ?, DATE("now"))
            ''', (product_id, quantity_sold, total_price))
            conn.commit()
            
        return True, f'Sale processed! Total: ${total_price:.2f}'
    except Exception as e:
        return False, str(e)

def get_all_sales():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.id, p.name, s.quantity_sold, s.total_price, s.date
            FROM sales s
            JOIN products p ON s.product_id = p.id
            ORDER BY s.date DESC
        ''')
        return cursor.fetchall()

# GUI Application
class RetailManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Narayana Stores - Retail Management System")
        self.root.geometry("1280x800")
        self.root.configure(bg='#f5f6fa')
        self.style = ttk.Style()
        
        # Initialize icons first
        self.icons = {}
        self.download_icons()
        
        self.configure_styles()
        self.create_widgets()
        create_database()

    def configure_styles(self):
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#f5f6fa')
        self.style.configure('TLabel', background='#f5f6fa', font=('Arial', 10))
        self.style.configure('TButton', font=('Arial', 10, 'bold'), padding=6)
        self.style.map('TButton',
            background=[('active', '#2c3e50'), ('!disabled', '#34495e')],
            foreground=[('!disabled', 'white')]
        )
        self.style.configure('Treeview', font=('Arial', 10), rowheight=25)
        self.style.configure('Treeview.Heading', font=('Arial', 10, 'bold'))

    def download_icons(self):
        icon_data = {
            'add': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/4.7.0/icons/plus-circle.png',
            'delete': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/4.7.0/icons/times-circle.png',
            'sale': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/4.7.0/icons/shopping-cart.png',
            'report': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/4.7.0/icons/bar-chart.png'
        }
        
        os.makedirs('icons', exist_ok=True)
        for name, url in icon_data.items():
            path = f'icons/{name}.png'
            try:
                if not os.path.exists(path):
                    urllib.request.urlretrieve(url, path)
                img = Image.open(path).resize((24, 24))
                self.icons[name] = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Error loading {name} icon: {e}")
                self.icons[name] = None

    def create_widgets(self):
        # Header
        header_frame = ttk.Frame(self.root, padding=20)
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text="Narayana Stores", 
                 font=('Arial', 24, 'bold'), foreground='#2c3e50').pack()

        # Notebook
        self.tabs = ttk.Notebook(self.root)
        self.tab_products = ttk.Frame(self.tabs)
        self.tab_inventory = ttk.Frame(self.tabs)
        self.tab_sales = ttk.Frame(self.tabs)
        self.tab_reports = ttk.Frame(self.tabs)
        
        self.tabs.add(self.tab_products, text=' Product Management ')
        self.tabs.add(self.tab_inventory, text=' Inventory ')
        self.tabs.add(self.tab_sales, text=' Point of Sale ')
        self.tabs.add(self.tab_reports, text=' Sales Analytics ')
        self.tabs.pack(expand=1, fill='both', padx=20, pady=10)

        self.create_product_tab()
        self.create_inventory_tab()
        self.create_sales_tab()
        self.create_reports_tab()

    def create_product_tab(self):
        frame = ttk.Frame(self.tab_products, padding=20)
        frame.pack(expand=1, fill=tk.BOTH)

        form_frame = ttk.Frame(frame)
        form_frame.pack(pady=20)

        ttk.Label(form_frame, text="Product Name:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.product_name = ttk.Entry(form_frame, width=30)
        self.product_name.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(form_frame, text="Price ($):").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.product_price = ttk.Entry(form_frame, width=30)
        self.product_price.grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(form_frame, text="Quantity:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.product_quantity = ttk.Entry(form_frame, width=30)
        self.product_quantity.grid(row=2, column=1, padx=10, pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Add Product", image=self.icons['add'],
                  compound=tk.LEFT, command=self.add_product).pack(side=tk.LEFT, padx=10)

    def create_inventory_tab(self):
        frame = ttk.Frame(self.tab_inventory)
        frame.pack(expand=1, fill=tk.BOTH, padx=20, pady=20)

        # Treeview
        columns = ('ID', 'Name', 'Price', 'Stock')
        self.inventory_tree = ttk.Treeview(frame, columns=columns, show='headings')
        for col in columns:
            self.inventory_tree.heading(col, text=col)
            self.inventory_tree.column(col, width=150, anchor=tk.CENTER)
        
        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscroll=vsb.set)
        
        self.inventory_tree.grid(row=0, column=0, sticky=tk.NSEW)
        vsb.grid(row=0, column=1, sticky=tk.NS)
        
        # Controls
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=1, column=0, pady=10)
        ttk.Button(btn_frame, text="Delete Selected", image=self.icons['delete'],
                  compound=tk.LEFT, command=self.delete_product).pack(side=tk.LEFT, padx=5)
        
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        self.refresh_inventory()

    def create_sales_tab(self):
        frame = ttk.Frame(self.tab_sales, padding=20)
        frame.pack(expand=1, fill=tk.BOTH)

        # Product Selection
        ttk.Label(frame, text="Select Product:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.sale_product = ttk.Combobox(frame, state='readonly', width=40)
        self.sale_product.grid(row=0, column=1, padx=10, pady=10)

        # Quantity
        ttk.Label(frame, text="Quantity:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.sale_quantity = ttk.Entry(frame, width=20)
        self.sale_quantity.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        # Process Sale
        ttk.Button(frame, text="Process Sale", image=self.icons['sale'],
                  compound=tk.LEFT, command=self.process_sale).grid(row=2, column=1, pady=20, sticky=tk.E)

        self.refresh_products()

    def create_reports_tab(self):
        frame = ttk.Frame(self.tab_reports)
        frame.pack(expand=1, fill=tk.BOTH, padx=20, pady=20)

        columns = ('ID', 'Product', 'Qty Sold', 'Total', 'Date')
        self.report_tree = ttk.Treeview(frame, columns=columns, show='headings')
        for col in columns:
            self.report_tree.heading(col, text=col)
            self.report_tree.column(col, width=150, anchor=tk.CENTER)
        
        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.report_tree.yview)
        self.report_tree.configure(yscroll=vsb.set)
        
        self.report_tree.grid(row=0, column=0, sticky=tk.NSEW)
        vsb.grid(row=0, column=1, sticky=tk.NS)
        
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        self.refresh_reports()

    # Business Logic
    def add_product(self):
        name = self.product_name.get().strip()
        price = self.product_price.get().strip()
        qty = self.product_quantity.get().strip()

        if not all([name, price, qty]):
            messagebox.showerror("Error", "All fields are required!")
            return

        try:
            price = float(price)
            qty = int(qty)
            if price <= 0 or qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Invalid price or quantity!")
            return

        success, msg = add_product(name, price, qty)
        if success:
            messagebox.showinfo("Success", msg)
            self.product_name.delete(0, tk.END)
            self.product_price.delete(0, tk.END)
            self.product_quantity.delete(0, tk.END)
            self.refresh_inventory()
            self.refresh_products()
        else:
            messagebox.showerror("Error", msg)

    def delete_product(self):
        selected = self.inventory_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a product!")
            return

        product_id = self.inventory_tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Confirm", "Delete this product?"):
            delete_product(product_id)
            self.refresh_inventory()
            self.refresh_products()

    def process_sale(self):
        product = self.sale_product.get()
        qty = self.sale_quantity.get().strip()

        if not product or not qty:
            messagebox.showerror("Error", "Select a product and enter quantity!")
            return

        try:
            product_id = int(product.split(' - ')[0])
            qty = int(qty)
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity!")
            return

        success, msg = process_sale(product_id, qty)
        if success:
            messagebox.showinfo("Success", msg)
            self.sale_quantity.delete(0, tk.END)
            self.refresh_inventory()
            self.refresh_products()
            self.refresh_reports()
        else:
            messagebox.showerror("Error", msg)

    # Refresh Methods
    def refresh_inventory(self):
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        for product in get_all_products():
            self.inventory_tree.insert('', tk.END, values=product)

    def refresh_products(self):
        products = get_all_products()
        self.sale_product['values'] = [f"{p[0]} - {p[1]} (Stock: {p[3]})" for p in products]

    def refresh_reports(self):
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        for sale in get_all_sales():
            self.report_tree.insert('', tk.END, values=sale)

if __name__ == "__main__":
    root = tk.Tk()
    app = RetailManagementApp(root)
    root.mainloop()