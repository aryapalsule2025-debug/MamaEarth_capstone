
-- Mamaearth Returns & Growth Intelligence Pipeline
-- Schema: customers, products, and orders
-- SQLite Compatible 

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    city_tier INTEGER NOT NULL,
    signup_date TEXT NOT NULL,
    acquisition_source TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    order_date TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    discount_pct INTEGER,
    payment_method TEXT NOT NULL,
    rating INTEGER,
    returned INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);
