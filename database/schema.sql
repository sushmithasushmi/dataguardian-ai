CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    state VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(200),
    category VARCHAR(100),
    price NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    order_status VARCHAR(50),
    total_amount NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id),
    product_id INT REFERENCES products(product_id),
    quantity INT,
    unit_price NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id),
    payment_method VARCHAR(50),
    payment_amount NUMERIC(10,2),
    payment_status VARCHAR(50),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(150) NOT NULL,
    run_status VARCHAR(30) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    source_name VARCHAR(150),
    target_name VARCHAR(150),
    rows_processed INT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds NUMERIC(10,3)
);

CREATE TABLE IF NOT EXISTS pipeline_events (
    event_id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(150) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_message TEXT NOT NULL,
    table_name VARCHAR(150),
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    run_id INT REFERENCES pipeline_runs(run_id)
);