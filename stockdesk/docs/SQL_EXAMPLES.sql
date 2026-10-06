-- Read-only SQL practice. Money columns are poisha; divide by 100 for BDT.
-- These queries are compatible with the project schema in MySQL and SQLite.

-- 1. Stock needing attention.
SELECT sku, name, stock, reorder_level
FROM products
WHERE active = TRUE AND stock <= reorder_level
ORDER BY stock, name;

-- 2. Customer outstanding balances, using JOIN and GROUP BY.
SELECT c.id, c.name, SUM(i.total_cents - i.paid_cents) / 100.0 AS due_bdt
FROM customers c
JOIN invoices i ON i.customer_id = c.id
WHERE i.cancelled = FALSE
GROUP BY c.id, c.name
HAVING SUM(i.total_cents - i.paid_cents) > 0
ORDER BY due_bdt DESC;

-- 3. Reconcile current stock with the complete movement ledger.
SELECT p.sku, p.name, p.stock,
       COALESCE(SUM(sm.quantity), 0) AS ledger_quantity,
       p.stock - COALESCE(SUM(sm.quantity), 0) AS difference
FROM products p
LEFT JOIN stock_movements sm ON sm.product_id = p.id
GROUP BY p.id, p.sku, p.name, p.stock;

-- 4. Sales totals by invoice date, excluding cancelled invoices.
SELECT DATE(created_at) AS sales_date, COUNT(*) AS invoices,
       SUM(total_cents) / 100.0 AS sales_bdt,
       SUM(paid_cents) / 100.0 AS paid_bdt
FROM invoices
WHERE cancelled = FALSE
GROUP BY DATE(created_at)
ORDER BY sales_date;

-- 5. Trace a stock movement to its invoice and supplier.
SELECT sm.id, p.sku, sm.kind, sm.quantity, sm.balance_after,
       sm.invoice_id, s.name AS supplier, sm.reference, sm.reason, sm.created_at
FROM stock_movements sm
JOIN products p ON p.id = sm.product_id
LEFT JOIN suppliers s ON s.id = sm.supplier_id
WHERE p.sku = 'KB-101'
ORDER BY sm.id;

-- 6. Reconcile cached payment total against individual payment records.
SELECT i.id, i.paid_cents,
       COALESCE(SUM(p.amount_cents), 0) AS recorded_payments_cents
FROM invoices i
LEFT JOIN payments p ON p.invoice_id = i.id
GROUP BY i.id, i.paid_cents
HAVING i.paid_cents <> COALESCE(SUM(p.amount_cents), 0);
