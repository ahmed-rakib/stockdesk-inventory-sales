# StockDesk - Inventory & Sales Management

A web application for managing products, stock movements, sales invoices, and customer payments. StockDesk helps a small business trace inventory changes, track outstanding balances, and export reports for Excel.

Built with **Python, FastAPI, SQLAlchemy, and a responsive HTML/CSS/JavaScript interface**. SQLite provides a local demo, with MySQL configuration available for a database-server setup.

![StockDesk dashboard showing sales, payments, customer dues, and low-stock alerts](docs/preview.jpg)

The screenshot uses fictional demo data. Its balances include sample transactions performed during browser testing.


## Features

| Module | Capabilities |
| --- | --- |
| Dashboard | Sales totals, collected payments, outstanding dues, inventory value, seven-day sales chart, and low-stock alerts |
| Products | Unique SKU, category, selling price, unit cost, reorder level, and active/inactive state |
| Contacts | Customer and supplier records with editable contact details |
| Stock ledger | Receipts and adjustments with quantity changes, balance after, supplier, reference, and reason |
| Sales invoices | Multiple products, discounts, tax, automatic stock deduction, historical price/name snapshots, and printing |
| Payments | Partial/full payment records, payment history, and outstanding balance tracking |
| Reports | Sales, inventory, customer dues, invoice-date filters, and CSV exports |
| Team access | Administrator/staff roles, session authentication, CSRF checks, and an activity log |

## Tech stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.12+, FastAPI, Uvicorn |
| Database access | SQLAlchemy 2, PyMySQL |
| Database | SQLite for the local demo; MySQL configuration provided |
| Validation | Pydantic |
| Frontend | HTML, CSS, vanilla JavaScript |
| Tests | Python unittest, FastAPI TestClient, HTTPX |
| Container setup | Dockerfile and Docker Compose with MySQL 8.4 |

The frontend requires no build step or external CDN.

## Quick start

Clone or download this repository, then open its root folder. Python 3.12 or newer is required. The first setup downloads dependencies.

### Windows

Double-click **`run.bat`**, or run these commands from the repository root:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.venv\Scripts\python.exe -m app.seed
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### macOS and Linux

```bash
sh run.sh
```

Alternatively:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m app.seed
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)**. Keep the server terminal open; press `Ctrl+C` to stop it.

### Local demo account

| Username | Password |
| --- | --- |
| `admin` | `DemoPass123!` |

The initializer creates fictional products, contacts, stock entries, and invoices. SQLite data persists in `data/stockdesk.db`. Running the initializer again preserves existing data.

To choose the initial administrator password, copy `.env.example` to `.env` and set `APP_ADMIN_PASSWORD` **before running the initializer for the first time**. Changing this setting later does not reset an existing account's password. `.env` is excluded from Git.

## Example workflow

1. Add a product with its selling price, unit cost, and reorder level.
2. Receive stock and record the supplier and delivery reference.
3. Add a customer and create a sales invoice.
4. Record a partial payment and review the remaining balance.
5. Open the customer-dues report and export it as CSV.
6. Trace a stock change using its product SKU, invoice reference, and activity log.

Administrators can cancel an unpaid invoice to restore stock. Invoices with recorded payments cannot be cancelled.

## Business rules

- **Exact monetary calculations:** amounts are stored as integer poisha. Input prices and payments use decimal BDT with at most two decimal places.
- **Atomic sales:** if any invoice item has insufficient stock, the entire sale is rejected without partial stock changes.
- **Payment limits:** a payment cannot exceed the invoice's outstanding balance.
- **Retry handling:** invoices, payments, receipts, and adjustments use request IDs to prevent duplicate records. Reusing an ID with different data returns a conflict.
- **Historical records:** invoice names, SKUs, and prices are snapshots; later catalog/contact edits preserve the original invoice details.
- **Stock traceability:** quantity changes are recorded through ledger entries. Cancellation restores an unpaid sale's quantities once.
- **Reporting:** cancelled invoices are excluded from sales and dues. Invoice-date filters use UTC. Inventory value uses current configured unit cost.

The MySQL implementation uses row locks for stock and invoice updates. The SQLite demo serializes database transactions because SQLite does not provide equivalent row-level locks.



## Project scope

This portfolio implementation covers one organization, one stock location, BDT amounts, and integer quantities. Cash, Bank, bKash, and Nagad are labels for manually recorded payments; no money is transferred by the application.

Purchase orders, returns/refunds, accounting journal entries, multiple warehouses, schema migrations, and automatic backups are not implemented. The supplied launchers bind the demo to localhost; public hosting requires a separate deployment setup.

## Author

**Golam Ahammed Rakib** · [GitHub](https://github.com/ahmed-rakib)
