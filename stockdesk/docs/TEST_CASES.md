# Manual acceptance checklist

| ID | Scenario | Expected result |
| --- | --- | --- |
| TC01 | Sign in with the wrong password | Error appears; workspace remains inaccessible |
| TC02 | Add a unique SKU | Product appears with zero stock |
| TC03 | Add the same SKU again | Conflict; one product remains |
| TC04 | Receive 10 units | Stock rises by 10; positive ledger movement appears |
| TC05 | Adjust below zero | Error; stock and ledger remain unchanged |
| TC06 | Invoice two available items | One invoice; both stock quantities reduced |
| TC07 | Invoice one available and one insufficient item | No invoice or partial stock deduction |
| TC08 | Submit an identical request ID twice | One business operation is recorded |
| TC09 | Reuse request ID with changed data | Conflict, no extra operation |
| TC10 | Record a partial payment | Partial status; due equals total minus payment |
| TC11 | Pay above the remaining balance | Error; payment history remains unchanged |
| TC12 | Pay exact balance | Paid status and zero due |
| TC13 | Cancel an unpaid invoice | Stock restored once; report excludes invoice |
| TC14 | Cancel a partially paid invoice | Error; stock remains unchanged |
| TC15 | Edit product/customer after an invoice | Historical invoice retains original names and price |
| TC16 | Sign in as staff | Administrator actions hidden and rejected by API |
| TC17 | Filter sales dates | Only invoices created within the inclusive UTC dates appear |
| TC18 | Export CSV | BDT decimals; matching rows; formula-like values neutralized |
| TC19 | Print an invoice | Only invoice content prints; navigation/actions are omitted |
| TC20 | Use a narrow viewport | Navigation toggles; tables scroll; forms remain usable |

Automated checks are in `tests/test_workflows.py`. This checklist lists acceptance targets; see `VERIFICATION.md` for execution evidence and unverified items.
