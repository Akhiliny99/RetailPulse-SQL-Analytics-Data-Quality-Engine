
SELECT
    'DQ1_DUPLICATE_CUSTOMER' AS check_name,
    'HIGH' AS severity,
    TRIM(LOWER(full_name)) AS name_key,
    email,
    COUNT(*) AS duplicate_count,
    GROUP_CONCAT(customer_id) AS affected_ids
FROM customers
WHERE email IS NOT NULL
GROUP BY TRIM(LOWER(full_name)), email
HAVING COUNT(*) > 1;


SELECT
    'DQ2_MISSING_EMAIL' AS check_name,
    'MEDIUM' AS severity,
    COUNT(*) AS affected_rows,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM customers), 2) AS pct_of_table
FROM customers
WHERE email IS NULL
UNION ALL
SELECT
    'DQ2_MISSING_CITY',
    'LOW',
    COUNT(*),
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM customers), 2)
FROM customers
WHERE city IS NULL;


SELECT
    'DQ3_INCONSISTENT_CITY' AS check_name,
    'MEDIUM' AS severity,
    TRIM(LOWER(city)) AS normalized_value,
    GROUP_CONCAT(DISTINCT city) AS raw_variants,
    COUNT(DISTINCT city) AS variant_count
FROM customers
WHERE city IS NOT NULL
GROUP BY TRIM(LOWER(city))
HAVING COUNT(DISTINCT city) > 1

UNION ALL

SELECT
    'DQ3_INCONSISTENT_CATEGORY',
    'MEDIUM',
    TRIM(LOWER(category)),
    GROUP_CONCAT(DISTINCT category),
    COUNT(DISTINCT category)
FROM products
GROUP BY TRIM(LOWER(category))
HAVING COUNT(DISTINCT category) > 1;


SELECT
    'DQ4_ORPHANED_ORDER_CUSTOMER' AS check_name,
    'CRITICAL' AS severity,
    COUNT(*) AS affected_rows
FROM orders o
LEFT JOIN customers c ON c.customer_id = o.customer_id
WHERE c.customer_id IS NULL

UNION ALL

SELECT
    'DQ4_ORPHANED_ORDERITEM_PRODUCT',
    'CRITICAL',
    COUNT(*)
FROM order_items oi
LEFT JOIN products p ON p.product_id = oi.product_id
WHERE p.product_id IS NULL;

SELECT 'DQ5_NEGATIVE_PRICE' AS check_name, 'HIGH' AS severity, COUNT(*) AS affected_rows
FROM products WHERE unit_price < 0
UNION ALL
SELECT 'DQ5_NULL_PRICE', 'MEDIUM', COUNT(*)
FROM products WHERE unit_price IS NULL
UNION ALL
SELECT 'DQ5_NEGATIVE_QUANTITY', 'HIGH', COUNT(*)
FROM order_items WHERE quantity < 0;


SELECT
    'DQ6_PRICE_MISMATCH' AS check_name,
    'MEDIUM' AS severity,
    oi.order_item_id,
    oi.product_id,
    oi.unit_price AS charged_price,
    p.unit_price AS current_catalog_price,
    ROUND(ABS(oi.unit_price - p.unit_price), 2) AS price_diff
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
WHERE p.unit_price IS NOT NULL
  AND ABS(oi.unit_price - p.unit_price) > 0.01
LIMIT 20;   -- sample; remove LIMIT for full audit


SELECT
    'DQ7_FUTURE_DATED_ORDER' AS check_name,
    'HIGH' AS severity,
    order_id,
    order_date
FROM orders
WHERE order_date > date('now');

SELECT 'Duplicate customers' AS issue, COUNT(*) AS count FROM (
    SELECT TRIM(LOWER(full_name)), email FROM customers
    WHERE email IS NOT NULL GROUP BY 1,2 HAVING COUNT(*) > 1
)
UNION ALL
SELECT 'Missing emails', COUNT(*) FROM customers WHERE email IS NULL
UNION ALL
SELECT 'Orphaned order->customer', COUNT(*) FROM orders o
    LEFT JOIN customers c ON c.customer_id = o.customer_id WHERE c.customer_id IS NULL
UNION ALL
SELECT 'Orphaned item->product', COUNT(*) FROM order_items oi
    LEFT JOIN products p ON p.product_id = oi.product_id WHERE p.product_id IS NULL
UNION ALL
SELECT 'Negative prices', COUNT(*) FROM products WHERE unit_price < 0
UNION ALL
SELECT 'Negative quantities', COUNT(*) FROM order_items WHERE quantity < 0
UNION ALL
SELECT 'Future-dated orders', COUNT(*) FROM orders WHERE order_date > date('now');
