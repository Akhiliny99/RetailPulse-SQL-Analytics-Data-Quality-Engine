"""
RetailPulse — Data Generator
Creates a realistic, intentionally messy retail dataset and loads it into SQLite.

Tables:
  customers  - has duplicates, inconsistent casing/whitespace, missing emails
  products   - has inconsistent category labels, some negative/null prices
  orders     - has some orphaned customer_ids (referential integrity issue), out-of-range dates
  order_items - has some negative quantities, some orphaned product_ids, price mismatches

Run: python3 01_generate_data.py
Output: ../data/retailpulse.db
"""

import sqlite3
import random
import string
from datetime import datetime, timedelta
import os

random.seed(42)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "retailpulse.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executescript("""
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    full_name   TEXT,
    email       TEXT,
    city        TEXT,
    signup_date TEXT
);

CREATE TABLE products (
    product_id  INTEGER PRIMARY KEY,
    product_name TEXT,
    category    TEXT,
    unit_price  REAL
);

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER,
    order_date  TEXT,
    status      TEXT
);

CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id      INTEGER,
    product_id    INTEGER,
    quantity      INTEGER,
    unit_price    REAL
);
""")

# ---------- CUSTOMERS (with messiness) ----------
first_names = ["Amal", "Nadeesha", "Kasun", "Ishara", "Tharindu", "Dilani", "Ruwan", "Sanduni",
               "Chamara", "Piumi", "Nuwan", "Hasini", "Roshan", "Anjali", "Malith", "Chathurika"]
last_names = ["Perera", "Fernando", "Silva", "Jayasuriya", "Rathnayake", "Wickramasinghe",
              "Gunawardena", "Bandara", "Dissanayake", "Karunaratne"]
cities = ["Colombo", "colombo", "COLOMBO", "Malabe", "Malabe ", "Kandy", "Galle", "Negombo",
          "Kurunegala", None, "Jaffna", "Kandy"]

customers = []
cid = 1001
for i in range(500):
    fn = random.choice(first_names)
    ln = random.choice(last_names)
    name = f"{fn} {ln}"
    # inject inconsistent casing/whitespace on some names
    if random.random() < 0.1:
        name = name.upper()
    if random.random() < 0.1:
        name = f" {name} "
    email = f"{fn.lower()}.{ln.lower()}@example.com" if random.random() > 0.08 else None  # missing emails
    city = random.choice(cities)
    signup = datetime(2022, 1, 1) + timedelta(days=random.randint(0, 900))
    customers.append((cid, name, email, city, signup.strftime("%Y-%m-%d")))
    cid += 1

# inject exact duplicate customers (same person, re-registered)
for _ in range(15):
    dupe = random.choice(customers)
    new_id = cid
    customers.append((new_id, dupe[1], dupe[2], dupe[3], dupe[4]))
    cid += 1

cur.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", customers)

# ---------- PRODUCTS ----------
category_variants = {
    "Electronics": ["Electronics", "electronics", "ELECTRONICS", "Electronic"],
    "Grocery": ["Grocery", "groceries", "Grocery "],
    "Apparel": ["Apparel", "apparel", "Clothing"],
    "Home & Kitchen": ["Home & Kitchen", "home and kitchen", "Home&Kitchen"],
    "Beauty": ["Beauty", "beauty"],
}
product_names = {
    "Electronics": ["USB Cable", "Wireless Mouse", "Bluetooth Speaker", "Power Bank", "LED Bulb"],
    "Grocery": ["Basmati Rice 5kg", "Coconut Oil 1L", "Tea Leaves 200g", "Sugar 1kg", "Milk Powder 400g"],
    "Apparel": ["Cotton T-Shirt", "Denim Jeans", "Formal Shirt", "Sarong", "Rain Jacket"],
    "Home & Kitchen": ["Non-stick Pan", "Blender", "Storage Container Set", "Cushion Cover", "Table Lamp"],
    "Beauty": ["Face Wash", "Sunscreen SPF50", "Shampoo 400ml", "Lip Balm", "Hair Oil"],
}

products = []
pid = 501
for cat, variants in category_variants.items():
    for name in product_names[cat]:
        for _ in range(4):
            price = round(random.uniform(150, 15000), 2)
            if random.random() < 0.03:
                price = None  # missing price
            elif random.random() < 0.02:
                price = -abs(price)  # bad negative price
            products.append((pid, name, random.choice(variants), price))
            pid += 1

cur.executemany("INSERT INTO products VALUES (?,?,?,?)", products)

# ---------- ORDERS ----------
valid_customer_ids = [c[0] for c in customers]
orders = []
oid = 20001
for _ in range(3000):
    cust = random.choice(valid_customer_ids)
    # inject orphaned customer_id (referential integrity break) ~2% of the time
    if random.random() < 0.02:
        cust = random.randint(90000, 99999)
    order_date = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 700))
    # inject a few bad future dates
    if random.random() < 0.005:
        order_date = datetime(2031, 1, 1)
    status = random.choices(
        ["Completed", "Completed", "Completed", "Cancelled", "Refunded", "Pending"],
        weights=[50, 20, 15, 8, 4, 3]
    )[0]
    orders.append((oid, cust, order_date.strftime("%Y-%m-%d"), status))
    oid += 1

cur.executemany("INSERT INTO orders VALUES (?,?,?,?)", orders)

# ---------- ORDER ITEMS ----------
valid_product_rows = [(p[0], p[3]) for p in products if p[3] is not None and p[3] > 0]
order_items = []
item_id = 500001
for order in orders:
    n_items = random.randint(1, 5)
    for _ in range(n_items):
        pid_choice, price = random.choice(valid_product_rows)
        qty = random.randint(1, 6)
        if random.random() < 0.01:
            qty = -qty  # bad negative quantity
        item_price = price
        # inject price mismatch vs product table ~3% of time (stale price capture)
        if random.random() < 0.03:
            item_price = round(price * random.uniform(0.8, 1.2), 2)
        # inject orphaned product_id ~1% of the time
        p_ref = pid_choice
        if random.random() < 0.01:
            p_ref = random.randint(80000, 89999)
        order_items.append((item_id, order[0], p_ref, qty, item_price))
        item_id += 1

cur.executemany("INSERT INTO order_items VALUES (?,?,?,?,?)", order_items)

conn.commit()

print(f"Database created at {DB_PATH}")
print(f"  customers:   {len(customers)} rows")
print(f"  products:    {len(products)} rows")
print(f"  orders:      {len(orders)} rows")
print(f"  order_items: {len(order_items)} rows")

conn.close()
