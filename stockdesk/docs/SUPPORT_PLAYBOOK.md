# Support investigation exercise

This is a simulated support case for learning. It is not evidence of professional client work.

## Case

The fictional customer says: "The keyboard quantity looks lower than yesterday. Please check the balance."

## Gather requirements and facts

Ask for the product SKU, expected quantity, last verified time, delivery reference and any invoice created since that time. Ask whether the user is looking at current stock or a historical ledger balance. Record the issue before proposing a correction.

## Reproduce and investigate

1. Open Products and locate the SKU.
2. Open Stock movements and search that SKU or product name.
3. Compare receipts, sales, cancellations and adjustments in chronological order.
4. Inspect invoice references and cancellation states.
5. Use the reconciliation query in `SQL_EXAMPLES.sql` to compare current quantity with the sum of ledger changes.
6. Review the activity log for the responsible user and reason.

## Demo reproduction

Note the keyboard opening balance. Create a sale for two keyboards. Current stock decreases by two and the ledger contains a SALE movement referencing the invoice. Cancel that unpaid invoice. Stock is restored and a CANCEL movement appears. A previous movement's balance-after remains unchanged because it records the balance at that earlier moment.

Do not manually modify the quantity column to reproduce a defect. Use a test database for corruption experiments. If there is a real discrepancy, identify the reason before an authorized administrator records a documented adjustment.

## Example issue update

> We reproduced the reported quantity difference for SKU KB-101. An invoice removed two units after the last stock check. We are verifying the invoice reference and delivery entries before recommending a correction.

## Example resolution

> The current stock matches the recorded receipts and sales. The earlier ledger entry shows the balance at that time; the Products page shows the current balance. We confirmed the invoice reference and demonstrated both views. No stock correction was required.

## Common errors

| Error | Investigation and resolution |
| --- | --- |
| Insufficient stock | Check current product quantity, duplicate selection and recent receipts. Receive verified stock or reduce invoice quantity. |
| Duplicate SKU | Search the existing catalog. Edit the existing product or use a genuinely different SKU. |
| Payment exceeds balance | Inspect invoice payment history. Record only the remaining balance. |
| Invoice with payments cannot be cancelled | Verify payments. This application does not implement refunds; escalate rather than rewriting records. |
| Security token expired | Refresh, sign in again, and retry the intended action once. |
| Database temporarily unavailable | Check service availability. Retry the same request ID; avoid inventing a new request for an uncertain outcome. |
| Site does not open | Keep the server terminal open, check its error message, and ensure port 8000 is available. |
| MySQL cannot connect | Confirm engine/service status, database credentials and hostname. In Compose the host is `db`; from the PC use `127.0.0.1`. |

## Support record template

Issue ID; reported by; date/time and timezone; product/invoice reference; expected behavior; actual behavior; reproduction steps; investigation queries; confirmed cause; authorized correction; validation; user-facing resolution; follow-up.
