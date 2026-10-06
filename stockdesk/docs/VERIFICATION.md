# Verification record

Verified on 6 October 2026 using Windows, Python 3.12 and the exact dependencies in `requirements.lock.txt`.

## Automated checks

The final automated run completed **22 tests successfully** in 12.536 seconds. It exercised SQLite API workflows, password/session authentication, CSRF/origin checks, staff permissions, user creation, duplicate SKU handling, integer quantity and price validation, atomic insufficient-stock rollback, tax rounding, stock/payment/invoice idempotency, partial/full/overpayment, cancellation, historical snapshots, CSV formula neutralization, reports and audit entries.

The concurrent-sale test submitted two sales for one remaining unit; one succeeded and the other returned a stock conflict. The final stock was zero.

JavaScript syntax validation passed. All 10 database tables compiled using SQLAlchemy's MySQL dialect. This checks generated schema syntax, not a live MySQL execution.

## Browser checks

- Signed into the initialized demo through the browser.
- Created an invoice for two keyboards, a BDT 100 discount and 5% tax: subtotal BDT 2,900; tax BDT 140; total BDT 2,940.
- Recorded BDT 1,000 as a fictional cash payment. The invoice showed Partial and BDT 1,940 remaining due.
- Confirmed the invoice appeared in the customer-dues report.
- Confirmed SKU search `KB-101` filtered the stock ledger to the matching entries, including the sale's deduction.
- Inspected the desktop dashboard, invoice form and report page.
- Checked the responsive report at a 390-by-844 viewport, including the mobile navigation control and horizontal table scrolling.
- Browser console inspection returned no errors or warnings during these checks.

The preview image was captured after these simulated transactions, so its balances differ from a freshly seeded five-invoice demo.

## Not executed here

The Docker engine was unavailable, so Docker image build, Compose startup and live MySQL transactions were not executed. The MySQL configuration and schema compilation are included, but MySQL runtime/concurrency behavior must be checked with a running server. The Windows installer/launcher and macOS/Linux launcher are supplied; a clean machine installation was not executed. Browser print preview was not inspected; print styles and a print button are included.

Starlette emitted a deprecation notice for the supported `httpx` test-client adapter. This did not cause a test failure.
