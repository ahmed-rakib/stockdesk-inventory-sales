# Business requirements

## Context

A fictional small computer-accessories business needs to know what is available, record sales and follow up on unpaid invoices. The support engineer must be able to trace a quantity change and explain a customer's invoice balance.

## Actors

| Actor | Permitted actions |
| --- | --- |
| Administrator | All operations, product/supplier maintenance, stock adjustments, unpaid invoice cancellation, user creation and activity log |
| Staff | View catalog and suppliers, maintain customers, receive stock, create invoices, record payments and view/export reports |

## Functional acceptance criteria

1. Each product has a unique SKU, positive selling price and nonnegative stock. New products start with zero stock.
2. A receipt increases stock and creates a ledger entry. An adjustment requires an administrator and a nonempty reason.
3. A sale contains a customer and at least one product. Each product appears once with a positive integer quantity.
4. All invoice lines must have sufficient available stock. If any line fails, no invoice, line, movement or stock change is committed.
5. Invoice numbers derive from the database-generated identifier. Product names, SKU, selling prices and customer name are copied into the invoice as historical snapshots.
6. Discounts reduce the subtotal before tax. The discounted amount must remain positive. Tax is rounded to the nearest poisha using ROUND_HALF_UP.
7. Payments may be partial or full. Their sum may not exceed the total. Cancelled invoices cannot receive payments.
8. An unpaid invoice can be cancelled by an administrator. Cancellation preserves the invoice and restores each line's stock once.
9. Retries using the same request ID and identical payload do not duplicate invoices, payments or receipts/adjustments. Reusing a request ID with a changed payload returns a conflict.
10. Reports exclude cancelled invoices. Date filters refer to invoice creation time in UTC. CSV amounts are BDT decimals.
11. Low stock means an active product's quantity is less than or equal to its reorder level.
12. Team members must sign in. Sessions expire after eight hours. Mutations require a valid CSRF token.
13. Each business mutation creates an audit entry. The web UI shows the latest 200 audit events and 100 stock movements; stock API supports up to 1000 recent entries.

## Data rules

- Money is stored as integer poisha to avoid binary floating-point arithmetic in business totals.
- Customer/supplier phone numbers are text, preserving country codes and leading zeroes.
- Foreign keys protect relationships. The application avoids destructive deletion of business records.
- Product deactivation prevents new sales/receipts while preserving historical invoices and stock valuation.
- Inventory valuation is current stock multiplied by the current configured cost. This is not FIFO accounting or a historical profit calculation.

## Nonfunctional goals

Local responsive UI; human-readable validation errors; no frontend network dependency; explicit transaction rollback; support-friendly references and audit history; separate test database; reproducible setup and packaged source.

## Scope

One organization, one currency (BDT), integer quantities and one stock location. Payment methods are labels for manual records. No gateway, external client messaging, purchase-order workflow, refunds, general ledger, tax-law compliance or production deployment is implemented.
