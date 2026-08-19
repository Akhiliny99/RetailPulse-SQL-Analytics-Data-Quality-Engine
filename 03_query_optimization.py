

import sqlite3
import time
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "retailpulse.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

TEST_QUERY = """
SELECT o.customer_id, COUNT(*) AS order_count, SUM(oi.quantity * oi.unit_price) AS total_spent
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_date BETWEEN '2023-06-01' AND '2023-12-31'
  AND o.status = 'Completed'
GROUP BY o.customer_id
ORDER BY total_spent DESC;
"""

def explain(label):
    print(f"\n--- EXPLAIN QUERY PLAN ({label}) ---")
    for row in cur.execute("EXPLAIN QUERY PLAN " + TEST_QUERY):
        print(row)

def timeit(label, runs=20):
    start = time.perf_counter()
    for _ in range(runs):
        cur.execute(TEST_QUERY).fetchall()
    elapsed = (time.perf_counter() - start) / runs
    print(f"{label}: avg {elapsed*1000:.3f} ms per run (over {runs} runs)")
    return elapsed

print("=" * 70)
print("BEFORE INDEXING")
print("=" * 70)
explain("no index")
before = timeit("Execution time before index")

print("\n" + "=" * 70)
print("ADDING INDEXES on filter/join columns")
print("=" * 70)
cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_date_status ON orders(order_date, status);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_orderitems_orderid ON order_items(order_id);")
conn.commit()
print("Created: idx_orders_date_status ON orders(order_date, status)")
print("Created: idx_orderitems_orderid ON order_items(order_id)")

print("\n" + "=" * 70)
print("AFTER INDEXING")
print("=" * 70)
explain("with index")
after = timeit("Execution time after index")

print("\n" + "=" * 70)
improvement = (before - after) / before * 100 if before else 0
print(f"RESULT: {improvement:.1f}% faster after adding targeted indexes")
print("=" * 70)

conn.close()
