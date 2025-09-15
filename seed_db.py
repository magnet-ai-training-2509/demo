import os
import random
import sqlite3
from datetime import datetime, timedelta


def get_db_path() -> str:
    return os.environ.get("DATABASE_PATH", "sample.db")


def init_schema(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON;")
    ddl = [
        # Reference data
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            contact_name TEXT,
            city TEXT,
            country TEXT
        );
        """,
        # Core entities
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            city TEXT,
            country TEXT,
            signup_date TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            title TEXT,
            department TEXT,
            hire_date TEXT NOT NULL,
            manager_id INTEGER,
            FOREIGN KEY(manager_id) REFERENCES employees(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            supplier_id INTEGER,
            unit_price REAL NOT NULL,
            cost REAL NOT NULL,
            in_stock INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(category_id) REFERENCES categories(id),
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
        );
        """,
        # Sales
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            employee_id INTEGER,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL,
            shipped_date TEXT,
            ship_city TEXT,
            ship_country TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            discount REAL NOT NULL DEFAULT 0.0,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            method TEXT NOT NULL,
            payment_date TEXT NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            review_text TEXT,
            review_date TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id),
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        );
        """,
        # Helpful indexes
        "CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);",
        "CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);",
        "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);",
        "CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id);",
    ]
    for stmt in ddl:
        conn.execute(stmt)


def seed_reference(conn: sqlite3.Connection) -> dict:
    categories = [
        "Electronics",
        "Books",
        "Home & Kitchen",
        "Clothing",
        "Sports",
        "Beauty",
        "Toys",
        "Automotive",
    ]
    conn.executemany("INSERT INTO categories(name) VALUES (?)", [(c,) for c in categories])

    supplier_names = [
        "Globex",
        "Initech",
        "Umbrella",
        "Hooli",
        "Stark Industries",
        "Wayne Enterprises",
        "Aperture",
        "Soylent",
        "Wonka",
        "Tyrell",
        "Acme",
        "Cyberdyne",
    ]
    countries = ["USA", "UK", "Germany", "France", "Spain", "Italy", "Poland", "Hungary", "Japan", "Canada"]
    cities = [
        "New York",
        "London",
        "Berlin",
        "Paris",
        "Madrid",
        "Rome",
        "Warsaw",
        "Budapest",
        "Tokyo",
        "Toronto",
    ]
    suppliers = []
    for i, name in enumerate(supplier_names, start=1):
        suppliers.append(
            (
                i,
                name + " Ltd.",
                random.choice(["Alice", "Bob", "Carol", "Dave", "Eve", "Mallory", "Trent", "Peggy"]),
                random.choice(cities),
                random.choice(countries),
            )
        )
    conn.executemany(
        "INSERT INTO suppliers(id, name, contact_name, city, country) VALUES (?, ?, ?, ?, ?)",
        suppliers,
    )

    return {"categories": categories, "cities": cities, "countries": countries, "supplier_ids": list(range(1, len(supplier_names) + 1))}


def seed_employees(conn: sqlite3.Connection, count: int = 25) -> list[int]:
    first_names = ["Anna", "Béla", "Csaba", "Dóra", "Eszter", "Ferenc", "Gábor", "Hanna", "István", "Júlia"]
    last_names = ["Kiss", "Nagy", "Szabó", "Tóth", "Kovács", "Varga", "Balogh", "Horváth", "Molnár", "Farkas"]
    titles = ["Sales Rep", "Sales Manager", "Support", "Analyst", "Engineer", "Director"]
    departments = ["Sales", "Support", "Operations", "Engineering", "HR", "Finance"]

    employees = []
    base_date = datetime(2015, 1, 1)
    for i in range(1, count + 1):
        hire_date = base_date + timedelta(days=random.randint(0, 365 * 8))
        manager_id = random.choice([None] + list(range(1, max(1, i // 5))))
        employees.append(
            (
                i,
                random.choice(first_names),
                random.choice(last_names),
                random.choice(titles),
                random.choice(departments),
                hire_date.date().isoformat(),
                manager_id,
            )
        )

    conn.executemany(
        """
        INSERT INTO employees(id, first_name, last_name, title, department, hire_date, manager_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        employees,
    )
    return list(range(1, count + 1))


def seed_customers(conn: sqlite3.Connection, count: int = 500) -> list[int]:
    first_names = ["Ádám", "Bori", "Cecil", "Dénes", "Emese", "Fanni", "Géza", "Hédi", "Imre", "Janka", "Kriszta", "László", "Mária", "Nóra", "Olivér", "Péter", "Rita", "Sára", "Tamás", "Zita"]
    last_names = ["Kiss", "Nagy", "Tóth", "Szabó", "Horváth", "Varga", "Kovács", "Molnár", "Németh", "Farkas"]
    domains = ["example.com", "mail.com", "demo.local", "test.org"]
    cities = ["Budapest", "Debrecen", "Szeged", "Pécs", "Győr"]
    countries = ["Hungary", "Austria", "Slovakia", "Romania", "Germany"]

    base_date = datetime(2019, 1, 1)
    customers = []
    for i in range(1, count + 1):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        email = f"{fn.lower()}.{ln.lower()}{i}@{random.choice(domains)}"
        phone = f"+36 30 {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}"
        signup = base_date + timedelta(days=random.randint(0, 365 * 5))
        customers.append(
            (
                i,
                fn,
                ln,
                email,
                phone,
                random.choice(cities),
                random.choice(countries),
                signup.date().isoformat(),
            )
        )
    conn.executemany(
        """
        INSERT INTO customers(id, first_name, last_name, email, phone, city, country, signup_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        customers,
    )
    return list(range(1, count + 1))


def seed_products(conn: sqlite3.Connection, meta: dict, count: int = 200) -> list[int]:
    adjectives = ["Portable", "Smart", "Advanced", "Eco", "Compact", "Premium", "Ultra", "Lite", "Pro", "Classic"]
    nouns = ["Speaker", "Headphones", "Mixer", "Blender", "Backpack", "Shoes", "Ball", "Cream", "Puzzle", "Camera", "Drill", "Lamp", "Router", "Monitor", "Keyboard"]
    products = []
    for i in range(1, count + 1):
        name = f"{random.choice(adjectives)} {random.choice(nouns)} {i}"
        category_id = random.randint(1, len(meta["categories"]))
        supplier_id = random.choice(meta["supplier_ids"]) if random.random() < 0.9 else None
        cost = round(random.uniform(5, 150), 2)
        price = round(cost * random.uniform(1.2, 2.5), 2)
        stock = random.randint(0, 500)
        products.append((i, name, category_id, supplier_id, price, cost, stock))
    conn.executemany(
        """
        INSERT INTO products(id, name, category_id, supplier_id, unit_price, cost, in_stock)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        products,
    )
    return list(range(1, count + 1))


def seed_orders(conn: sqlite3.Connection, customer_ids: list[int], employee_ids: list[int], product_ids: list[int], count: int = 2000) -> list[int]:
    statuses = ["Pending", "Processing", "Shipped", "Delivered", "Canceled", "Returned"]
    cities = ["Budapest", "Debrecen", "Szeged", "Pécs", "Győr", "Miskolc"]
    countries = ["Hungary", "Austria", "Slovakia", "Romania", "Germany"]
    start = datetime(2020, 1, 1)
    orders = []
    for i in range(1, count + 1):
        order_date = start + timedelta(days=random.randint(0, 1200))
        status = random.choices(statuses, weights=[15, 25, 25, 25, 5, 5], k=1)[0]
        shipped_date = None
        if status in ("Shipped", "Delivered", "Returned"):
            shipped_date = order_date + timedelta(days=random.randint(1, 10))
        employee_id = random.choice(employee_ids) if random.random() < 0.8 else None
        orders.append(
            (
                i,
                random.choice(customer_ids),
                employee_id,
                order_date.date().isoformat(),
                status,
                shipped_date.date().isoformat() if shipped_date else None,
                random.choice(cities),
                random.choice(countries),
            )
        )
    conn.executemany(
        """
        INSERT INTO orders(id, customer_id, employee_id, order_date, status, shipped_date, ship_city, ship_country)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        orders,
    )

    # Items for each order
    items = []
    item_id = 1
    for order_id in range(1, count + 1):
        for _ in range(random.randint(1, 5)):
            product_id = random.choice(product_ids)
            quantity = random.randint(1, 5)
            # Read unit price from products
            cur = conn.execute("SELECT unit_price FROM products WHERE id = ?", (product_id,))
            unit_price = cur.fetchone()[0]
            discount = round(random.choice([0.0, 0.0, 0.05, 0.1, 0.15]), 2)
            items.append((item_id, order_id, product_id, quantity, unit_price, discount))
            item_id += 1
    conn.executemany(
        """
        INSERT INTO order_items(id, order_id, product_id, quantity, unit_price, discount)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        items,
    )

    # Payments: assume one payment per order for simplicity
    methods = ["Card", "PayPal", "BankTransfer", "CashOnDelivery"]
    payments = []
    pay_id = 1
    for order_id in range(1, count + 1):
        # Compute total amount for the order
        cur = conn.execute(
            """
            SELECT SUM(quantity * unit_price * (1 - discount))
            FROM order_items WHERE order_id = ?
            """,
            (order_id,),
        )
        total = round(cur.fetchone()[0] or 0.0, 2)
        pay_date = start + timedelta(days=random.randint(0, 1200))
        payments.append((pay_id, order_id, total, random.choice(methods), pay_date.date().isoformat()))
        pay_id += 1
    conn.executemany(
        "INSERT INTO payments(id, order_id, amount, method, payment_date) VALUES (?, ?, ?, ?, ?)",
        payments,
    )

    # Reviews: sparse
    reviews = []
    review_id = 1
    for _ in range(count // 3):  # about a third as many reviews as orders
        reviews.append(
            (
                review_id,
                random.choice(product_ids),
                random.choice(customer_ids),
                random.randint(1, 5),
                random.choice([
                    "Great product!",
                    "Works as expected.",
                    "Average quality.",
                    "Not satisfied.",
                    "Excellent value for money.",
                    None,
                ]),
                (start + timedelta(days=random.randint(0, 1200))).date().isoformat(),
            )
        )
        review_id += 1
    conn.executemany(
        """
        INSERT INTO reviews(id, product_id, customer_id, rating, review_text, review_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        reviews,
    )

    return list(range(1, count + 1))


def seed_all(db_path: str) -> None:
    random.seed(42)
    with sqlite3.connect(db_path) as conn:
        init_schema(conn)

        # If tables already have data, skip reseeding to avoid duplicates
        cur = conn.execute("SELECT COUNT(*) FROM customers")
        if cur.fetchone()[0] > 0:
            return

        meta = seed_reference(conn)
        employee_ids = seed_employees(conn, 25)
        customer_ids = seed_customers(conn, 500)
        product_ids = seed_products(conn, meta, 200)
        seed_orders(conn, customer_ids, employee_ids, product_ids, 2000)
        conn.commit()


if __name__ == "__main__":
    path = get_db_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    seed_all(path)
    print(f"Seeded demo database at: {path}")

