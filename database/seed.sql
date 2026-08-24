INSERT INTO customers (
    first_name,
    last_name,
    email,
    state
)
VALUES
('Emma', 'Johnson', 'emma.johnson@example.com', 'WA'),
('Liam', 'Smith', 'liam.smith@example.com', 'CA'),
('Olivia', 'Brown', 'olivia.brown@example.com', 'TX'),
('Noah', 'Davis', 'noah.davis@example.com', 'NY'),
('Ava', 'Wilson', 'ava.wilson@example.com', 'IL')
ON CONFLICT (email) DO NOTHING;

INSERT INTO products (
    product_name,
    category,
    price
)
SELECT *
FROM (
    VALUES
    ('Wireless Headphones', 'Electronics', 89.99::numeric),
    ('Mechanical Keyboard', 'Electronics', 129.99::numeric),
    ('Running Shoes', 'Footwear', 74.50::numeric),
    ('Coffee Maker', 'Home', 59.99::numeric),
    ('Backpack', 'Accessories', 49.99::numeric)
) AS values_table(product_name, category, price)
WHERE NOT EXISTS (
    SELECT 1 FROM products
);

INSERT INTO orders (
    customer_id,
    order_status,
    total_amount
)
SELECT *
FROM (
    VALUES
    (1, 'COMPLETED', 89.99::numeric),
    (2, 'COMPLETED', 129.99::numeric),
    (3, 'PENDING', 149.00::numeric),
    (4, 'COMPLETED', 59.99::numeric),
    (5, 'CANCELLED', 49.99::numeric)
) AS values_table(customer_id, order_status, total_amount)
WHERE NOT EXISTS (
    SELECT 1 FROM orders
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
SELECT *
FROM (
    VALUES
    (1, 1, 1, 89.99::numeric),
    (2, 2, 1, 129.99::numeric),
    (3, 3, 2, 74.50::numeric),
    (4, 4, 1, 59.99::numeric),
    (5, 5, 1, 49.99::numeric)
) AS values_table(order_id, product_id, quantity, unit_price)
WHERE NOT EXISTS (
    SELECT 1 FROM order_items
);

INSERT INTO payments (
    order_id,
    payment_method,
    payment_amount,
    payment_status
)
SELECT *
FROM (
    VALUES
    (1, 'CREDIT_CARD', 89.99::numeric, 'SUCCESS'),
    (2, 'PAYPAL', 129.99::numeric, 'SUCCESS'),
    (3, 'CREDIT_CARD', 149.00::numeric, 'PENDING'),
    (4, 'DEBIT_CARD', 59.99::numeric, 'SUCCESS'),
    (5, 'CREDIT_CARD', 49.99::numeric, 'REFUNDED')
) AS values_table(
    order_id,
    payment_method,
    payment_amount,
    payment_status
)
WHERE NOT EXISTS (
    SELECT 1 FROM payments
);