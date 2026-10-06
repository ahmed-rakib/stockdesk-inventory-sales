# StockDesk — Inventory & Sales Management

A web application for managing products, stock movements, sales invoices, and customer payments. StockDesk helps a small business trace inventory changes, track outstanding balances, and export reports for Excel.

Built with **Python, FastAPI, SQLAlchemy, and a responsive HTML/CSS/JavaScript interface**. SQLite provides a local demo, with MySQL configuration available for a database-server setup.

![StockDesk dashboard showing sales, payments, customer dues, and low-stock alerts](docs/preview.jpg)

The screenshot uses fictional demo data. Its balances include sample transactions performed during browser testing.

**বাংলায় setup guide:** [START_HERE_BN.md](START_HERE_BN.md)

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

## Access roles

| Role | Permissions |
| --- | --- |
| Staff | View products/suppliers, maintain customers, receive stock, create invoices, record payments, and view/export reports |
| Administrator | All staff operations plus product/supplier maintenance, stock adjustments, unpaid invoice cancellation, user creation, and activity-log access |

Passwords use salted PBKDF2-SHA256 hashing. Authentication uses an HttpOnly, SameSite Strict session cookie with an eight-hour expiry. Mutations require a CSRF token.

## MySQL setup

### Docker Compose

Start Docker's Linux engine. Copy `.env.example` to `.env`, then add:

```dotenv
MYSQL_PASSWORD=your_database_password
MYSQL_ROOT_PASSWORD=your_root_password
APP_ADMIN_PASSWORD=your_admin_password
```

Choose an administrator password with at least ten characters. Use letters, digits, and underscores for the database passwords in this example; special characters in a manually composed connection URL must be URL-encoded.

```bash
docker compose up --build -d
docker compose logs -f web
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Compose initializes the application after MySQL passes its health check. Data persists in the `mysql_data` volume. Stop the services while retaining data with:

```bash
docker compose down
```

### Existing MySQL server

Create a database and dedicated account:

```sql
CREATE DATABASE stockdesk CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'stockdesk'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON stockdesk.* TO 'stockdesk'@'localhost';
```

Set the connection in `.env`, then run the initializer and server using the quick-start commands:

```dotenv
DATABASE_URL=mysql+pymysql://stockdesk:your_password@127.0.0.1:3306/stockdesk?charset=utf8mb4
APP_ADMIN_PASSWORD=your_admin_password
```

Tables are created during initialization/startup. Schema migrations are outside the current scope.

## API reference

Interactive documentation: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**. Swagger UI assets require internet; the main application does not.

| Routes | Purpose |
| --- | --- |
| `/api/auth/login`, `/api/auth/me`, `/api/auth/logout` | Login, session details, and logout |
| `/api/products`, `/api/products/{id}` | List, create, and update products |
| `/api/customers`, `/api/customers/{id}` | Customer records |
| `/api/suppliers`, `/api/suppliers/{id}` | Supplier records |
| `/api/stock/receive`, `/api/stock/adjust`, `/api/stock/movements` | Receipts, corrections, and stock history |
| `/api/invoices`, `/api/invoices/{id}` | Invoice creation, listing, and details |
| `/api/invoices/{id}/payments`, `/api/invoices/{id}/cancel` | Payment recording and cancellation |
| `/api/dashboard`, `/api/reports/{kind}`, `/api/export/{kind}.csv` | Dashboard, reports, and exports |
| `/api/users`, `/api/audit` | Team access and activity log |
| `/health` | Application/database health |

Report kinds are `sales`, `inventory`, and `receivables`. Sales/receivables accept `start` and `end` query parameters in `YYYY-MM-DD` format.

For API mutations, include the session cookie and the `X-CSRF-Token` returned by login or `/api/auth/me`. Output fields ending in `_cents` are integer poisha: `10050` represents **BDT 100.50**. CSV monetary columns ending in `_bdt` contain decimal BDT values.

## Tests and verification

Run the automated suite from the repository root:

```powershell
# Windows
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

```bash
# macOS / Linux
.venv/bin/python -m unittest discover -s tests -v
```

The suite uses a separate SQLite test database and checks authentication, permissions, validation, rollback, concurrent sales, invoice arithmetic, payment limits, cancellation, retry handling, historical snapshots, reports, and CSV safety.

| Verification | Result |
| --- | --- |
| Automated SQLite workflow tests | 22 passed |
| Browser invoice/payment workflow | Verified |
| Desktop/mobile interface checks | Verified |
| JavaScript syntax check | Passed |
| MySQL schema compilation | All 10 tables compiled |
| Live MySQL transactions / Docker startup | Not executed |

Live MySQL/Docker execution and a clean-machine launcher installation remain unverified. See the [verification record](docs/VERIFICATION.md) for the tested environment and detailed evidence.

## Project structure

```text
stockdesk/
├── app/
│   ├── db.py              # Database engine and transaction lifecycle
│   ├── models.py          # Database schema and relationships
│   ├── schemas.py         # Request validation
│   ├── security.py        # Passwords, sessions, CSRF, and roles
│   ├── services.py        # Stock, invoice, payment, and cancellation rules
│   ├── main.py            # API routes, reports, and frontend serving
│   ├── seed.py            # Fictional demo initialization
│   └── static/            # HTML, CSS, and JavaScript interface
├── tests/                 # Automated workflow tests
├── docs/                  # Requirements, architecture, SQL, and support guides
├── .env.example           # Configuration template
├── requirements.txt       # Supported dependency ranges
├── requirements.lock.txt  # Exact versions used during verification
├── run.bat                # Windows launcher
├── run.sh                 # macOS/Linux launcher
├── Dockerfile
├── compose.yaml
└── START_HERE_BN.md        # Bengali setup guide
```

## Documentation

- [Business requirements](docs/REQUIREMENTS.md)
- [Architecture and database ERD](docs/ARCHITECTURE.md)
- [User guide and demonstration](docs/USER_GUIDE.md)
- [Manual acceptance test cases](docs/TEST_CASES.md)
- [Support investigation playbook](docs/SUPPORT_PLAYBOOK.md)
- [SQL practice queries](docs/SQL_EXAMPLES.sql)
- [Verification record](docs/VERIFICATION.md)

## Project scope

This portfolio implementation covers one organization, one stock location, BDT amounts, and integer quantities. Cash, Bank, bKash, and Nagad are labels for manually recorded payments; no money is transferred by the application.

Purchase orders, returns/refunds, accounting journal entries, multiple warehouses, schema migrations, and automatic backups are not implemented. The supplied launchers bind the demo to localhost; public hosting requires a separate deployment setup.

## Author

**Golam Ahammed Rakib** · [GitHub](https://github.com/ahmed-rakib)
