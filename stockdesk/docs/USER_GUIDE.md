# User guide and demonstration

## Start and sign in

Run `run.bat` on Windows, open http://127.0.0.1:8000 and sign in with the configured admin password. The default local demo credentials are admin / DemoPass123!. Sample records are fictional. Click your account name in the upper-right to sign out.

## Products

Choose Products, then Add product. Enter a unique SKU, product name, category, selling price, unit cost and reorder level. Stock starts at zero. Edit a product to change pricing or mark it inactive. Inactive products cannot be selected for new invoices or stock receipts.

## Customers and suppliers

Add the customer before creating their first invoice. Suppliers are optional on receipts but help trace deliveries. Both contact lists support edits. Changing a customer's name does not change the name displayed on an existing invoice.

## Stock receipts

Choose Stock movements, then Receive stock. Select a product, positive quantity and optional supplier. Enter a delivery reference and reason. Save, then check the positive quantity and balance-after in the ledger.

Administrators can use Adjust stock for physical-count corrections. Enter a positive number to add or a negative number to remove. Explain the difference in the reason. Stock cannot become negative.

## Invoice creation

Choose New invoice, select a customer and add products with positive quantities. Select each product once. Enter an optional discount, tax percentage and note. The preview shows the current prices; the server checks the latest stock/prices and calculates the final totals when saving. Refresh if another team member changed inventory.

After saving, the invoice list shows its status and balance due. Open an invoice to view lines, payment history or print it.

## Payments

Open an unpaid/partial invoice and choose Record payment. Enter the received amount, method and optional reference. Partial payment changes the status to Partial; paying the exact balance changes it to Paid. Payment labels do not transfer money. Amounts greater than the outstanding balance are rejected.

## Cancellation

Administrators may cancel invoices with no recorded payments. Enter a reason. The invoice remains visible as Cancelled, each quantity is restored, and sales/dues reports exclude the invoice. Cancelling the same invoice again does not restore stock twice.

## Reports and exports

- Sales: invoice totals, received payments and dues.
- Inventory: quantities, configured costs, low-stock state and stock value.
- Customer dues: invoices with a remaining unpaid balance.

Sales/dues date filters use invoice dates in UTC. Export CSV downloads the matching rows for Excel. CSV monetary columns ending in `_bdt` contain decimal BDT amounts. Inventory value uses current configured unit cost.

## Team access

Administrators can create staff/admin accounts under Team access. Passwords need at least ten characters. Staff may handle daily sales, customers, receipts, payments and reports. They cannot edit products/suppliers, adjust stock, cancel invoices or access administrator tools.

## Five-minute interview demo

1. Explain the dashboard and distinguish total sales from money actually collected.
2. Receive five keyboards with reference `DELIVERY-001`.
3. Invoice two keyboards and one mouse for a customer.
4. Record a partial payment and show Customer dues.
5. Attempt an excessive quantity. Explain HTTP 409, transaction rollback and unchanged stock.
6. Cancel a different unpaid invoice and show the CANCEL stock movement.
7. Show the audit log, CSV output, test suite and SQL examples.
