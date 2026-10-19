
-- Mamaearth Returns & Growth Intelligence Pipeline
-- Part 1: SQL Reports
-- Tasks (a) to (i)

USE mamaearth_capstone;


-- (a) Total orders, total revenue, and average order value
-- Expected: 180 orders, revenue = 99860.20, average = 554.78

SELECT
    COUNT(*) AS total_orders,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100)
        ),
        2
    ) AS total_revenue,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100)
        ) / COUNT(*),
        2
    ) AS avg_order_value
FROM orders o
JOIN products p
    ON o.product_id = p.product_id;





-- (b) Count total rows, rated orders, and unrated orders
-- Expected: 180 total, 165 rated, 15 unrated

SELECT
    COUNT(*) AS total_rows,
    COUNT(rating) AS rated_orders,
    COUNT(*) - COUNT(rating) AS unrated_orders
FROM orders;




-- (c1) Customers who have never placed an order
-- Method: LEFT JOIN
-- Expected: C045, Vihaan

SELECT
    c.customer_id,
    c.name
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;




-- (c2) Customers who have never placed an order
-- Method: NOT IN
-- Expected: C045, Vihaan

SELECT
    customer_id,
    name
FROM customers
WHERE customer_id NOT IN (
    SELECT customer_id
    FROM orders
);




-- (d) Cities with a return rate greater than 20%
-- Expected:
-- Jaipur    | 19 orders |  8 returns | 42.1%
-- Lucknow   | 49 orders | 15 returns | 30.6%
-- Bangalore | 33 orders |  8 returns | 24.2%

SELECT
    c.city,
    COUNT(*) AS total_orders,
    SUM(o.returned) AS returned_orders,
    ROUND(
        100.0 * SUM(o.returned) / COUNT(*),
        1
    ) AS return_rate_pct
FROM orders o
JOIN customers c
    ON o.customer_id = c.customer_id
GROUP BY c.city
HAVING 100.0 * SUM(o.returned) / COUNT(*) > 20
ORDER BY return_rate_pct DESC;




-- (e1) Top 5 customers by total spending
-- Expected:
-- C043 Reyansh | 12920.00
-- C026 Isha    |  8371.60
-- C008 Meera   |  4564.60
-- C011 Arjun   |  4111.00
-- C042 Sanya   |  3785.00

SELECT
    c.customer_id,
    c.name,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100)
        ),
        2
    ) AS total_spend
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
JOIN products p
    ON o.product_id = p.product_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 5;




-- (e2) Pagination: skip 2 customers, return the next 3
-- Expected: C008 Meera, C011 Arjun, C042 Sanya

SELECT
    c.customer_id,
    c.name,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100)
        ),
        2
    ) AS total_spend
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
JOIN products p
    ON o.product_id = p.product_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 3 OFFSET 2;



-- (f) Order count and revenue by product category
-- Expected output
-- Skincare     | 60 | 27346.00
-- Haircare     | 54 | 44956.10
-- PersonalCare | 36 | 10753.10
-- Babycare     | 30 | 16805.00
SELECT
    p.category,
    COUNT(*) AS order_count,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100)
        ),
        2
    ) AS total_revenue
FROM orders o
JOIN products p
    ON o.product_id = p.product_id
JOIN customers c
    ON o.customer_id = c.customer_id
GROUP BY p.category
ORDER BY order_count DESC, total_revenue DESC;



-- (g) Find customers whose names start with A
-- Expected: 10 rows

SELECT
    customer_id,
    name
FROM customers
WHERE name LIKE 'A%'
ORDER BY customer_id;




-- (h) List all unique customer acquisition sources
-- Expected: Ad, Organic, Referral, Social

SELECT DISTINCT
    acquisition_source
FROM customers
ORDER BY acquisition_source;




-- (i) Assign loyalty tiers using CASE
-- The ALTER TABLE command has already been executed.
-- Do not run it again on your existing database.

-- ALTER TABLE customers ADD COLUMN loyalty_tier VARCHAR(10);

SET SQL_SAFE_UPDATES = 0;

UPDATE customers
SET loyalty_tier = CASE
    WHEN city_tier = 1 THEN 'Gold'
    ELSE 'Silver'
END;

-- Expected: Gold = 28, Silver = 17

SELECT
    loyalty_tier,
    COUNT(*) AS customer_count
FROM customers
GROUP BY loyalty_tier
ORDER BY loyalty_tier;

