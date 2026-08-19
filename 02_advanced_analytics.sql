-- ============================================================
-- RetailPulse — Advanced Analytics Queries
-- Run against data/retailpulse.db
-- Each query answers a real business question.
-- ============================================================

-- --------------------------------------------------------------
-- Q1. Monthly revenue trend + Month-over-Month growth %
-- Business question: "Is revenue growing month over month, and by how much?"
-- Uses: window function LAG()
-- --------------------------------------------------------------
WITH monthly_revenue AS (
    SELECT
        strftime('%Y-%m', o.order_date) AS month,
        ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'Completed'
      AND oi.quantity > 0                 -- exclude bad data rows
      AND o.order_date <= '2025-12-31'    -- exclude bad future dates
    GROUP BY 1
)
SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue,
    ROUND(
        100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
        / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 2
    ) AS mom_growth_pct
FROM monthly_revenue
ORDER BY month;


-- --------------------------------------------------------------
-- Q2. Top 10 customers by lifetime revenue, with their rank and
--     what % of total company revenue they represent
-- Business question: "Who are our most valuable customers?"
-- Uses: window functions RANK(), SUM() OVER ()
-- --------------------------------------------------------------
WITH customer_revenue AS (
    SELECT
        c.customer_id,
        TRIM(c.full_name) AS customer_name,
        ROUND(SUM(oi.quantity * oi.unit_price), 2) AS lifetime_revenue
    FROM customers c
    JOIN orders o ON o.customer_id = c.customer_id
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'Completed' AND oi.quantity > 0
    GROUP BY c.customer_id, customer_name
)
SELECT
    customer_id,
    customer_name,
    lifetime_revenue,
    RANK() OVER (ORDER BY lifetime_revenue DESC) AS revenue_rank,
    ROUND(100.0 * lifetime_revenue / SUM(lifetime_revenue) OVER (), 2) AS pct_of_total_revenue
FROM customer_revenue
ORDER BY revenue_rank
LIMIT 10;


-- --------------------------------------------------------------
-- Q3. Customer cohort retention analysis
-- Business question: "Of customers who signed up in a given month,
--                      what % placed an order in each following month?"
-- Uses: CTEs, DATE math, self-referencing cohort logic
-- --------------------------------------------------------------
WITH cohorts AS (
    SELECT
        customer_id,
        strftime('%Y-%m', signup_date) AS cohort_month
    FROM customers
),
customer_orders AS (
    SELECT DISTINCT
        o.customer_id,
        strftime('%Y-%m', o.order_date) AS order_month
    FROM orders o
    WHERE o.status = 'Completed'
),
cohort_activity AS (
    SELECT
        c.cohort_month,
        co.order_month,
        (CAST(strftime('%Y', co.order_month || '-01') AS INT) * 12 + CAST(strftime('%m', co.order_month || '-01') AS INT))
        -
        (CAST(strftime('%Y', c.cohort_month || '-01') AS INT) * 12 + CAST(strftime('%m', c.cohort_month || '-01') AS INT))
        AS month_number,
        c.customer_id
    FROM cohorts c
    JOIN customer_orders co ON co.customer_id = c.customer_id
    WHERE co.order_month >= c.cohort_month
),
cohort_size AS (
    SELECT cohort_month, COUNT(*) AS num_customers
    FROM cohorts
    GROUP BY cohort_month
)
SELECT
    ca.cohort_month,
    ca.month_number,
    COUNT(DISTINCT ca.customer_id) AS active_customers,
    cs.num_customers AS cohort_size,
    ROUND(100.0 * COUNT(DISTINCT ca.customer_id) / cs.num_customers, 1) AS retention_pct
FROM cohort_activity ca
JOIN cohort_size cs ON cs.cohort_month = ca.cohort_month
WHERE ca.month_number BETWEEN 0 AND 6
GROUP BY ca.cohort_month, ca.month_number, cs.num_customers
ORDER BY ca.cohort_month, ca.month_number;


-- --------------------------------------------------------------
-- Q4. Product category performance with running total (YTD-style)
-- Business question: "Which categories drive the most revenue, cumulatively?"
-- Uses: window function SUM() OVER (ORDER BY ... ROWS UNBOUNDED PRECEDING)
-- --------------------------------------------------------------
WITH category_revenue AS (
    SELECT
        p.category,
        ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
    FROM order_items oi
    JOIN products p ON p.product_id = oi.product_id
    JOIN orders o ON o.order_id = oi.order_id
    WHERE o.status = 'Completed' AND oi.quantity > 0
    GROUP BY p.category
)
SELECT
    category,
    revenue,
    SUM(revenue) OVER (ORDER BY revenue DESC ROWS UNBOUNDED PRECEDING) AS running_total,
    ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC ROWS UNBOUNDED PRECEDING)
          / SUM(revenue) OVER (), 1) AS running_pct_of_total
FROM category_revenue
ORDER BY revenue DESC;


-- --------------------------------------------------------------
-- Q5. Days-between-orders per customer (purchase frequency)
-- Business question: "How often do repeat customers come back?"
-- Uses: window function LAG() partitioned by customer, julianday date math
-- --------------------------------------------------------------
WITH customer_order_dates AS (
    SELECT DISTINCT
        customer_id,
        order_date
    FROM orders
    WHERE status = 'Completed'
),
gaps AS (
    SELECT
        customer_id,
        order_date,
        LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS prev_order_date
    FROM customer_order_dates
)
SELECT
    customer_id,
    ROUND(AVG(julianday(order_date) - julianday(prev_order_date)), 1) AS avg_days_between_orders,
    COUNT(*) AS repeat_order_count
FROM gaps
WHERE prev_order_date IS NOT NULL
GROUP BY customer_id
HAVING COUNT(*) >= 3
ORDER BY avg_days_between_orders ASC
LIMIT 15;
