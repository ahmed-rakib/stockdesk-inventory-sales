# StockDesk চালানোর নিয়ম

এটি Inventory & Sales Management-এর একটি portfolio project। FastAPI backend, SQL database এবং web interface একসঙ্গে দেওয়া আছে।

## এখন local demo

Browser-এ `http://127.0.0.1:8000` খোলো।

- Username: `admin`
- Default demo password: `DemoPass123!`

এই demo-র সব customer, invoice ও payment কাল্পনিক। Payment record করা মানে বাস্তবে টাকা পাঠানো নয়।

## ZIP থেকে চালাবে যেভাবে

1. ZIP extract করো।
2. Python 3.12 বা নতুন version না থাকলে Python launcher-সহ install করো।
3. `stockdesk` folder-এর `run.bat` double-click করো।
4. প্রথমবার dependencies download হবে; internet লাগবে।
5. Terminal-এ server ready হলে browser-এ `http://127.0.0.1:8000` খোলো।
6. উপরের demo credentials দিয়ে login করো। আগে `.env`-এ নিজের initial password দিলে সেটি ব্যবহার করবে।

Terminal বন্ধ করলে server বন্ধ হবে। পরে আবার `run.bat` চালালে আগের data থাকবে।

## কী কী করবে

- Products থেকে নতুন product তৈরি ও price পরিবর্তন।
- Customers/Suppliers থেকে contact তৈরি ও edit।
- Stock movements থেকে receipt/adjustment এবং audit trail দেখা।
- Sales invoices থেকে invoice তৈরি, payment record এবং unpaid invoice cancel।
- Reports থেকে sales, inventory ও customer dues report; CSV export।
- Team access থেকে staff account তৈরি।

## Project বুঝে interview দেবে

শুধু feature দেখালে হবে না। `docs/REQUIREMENTS.md`, `docs/ARCHITECTURE.md` এবং `docs/SUPPORT_PLAYBOOK.md` পড়ে transaction, stock calculation, partial payment, SQL JOIN/GROUP BY, error handling এবং client issue investigation বোঝো। `docs/SQL_EXAMPLES.sql`-এ practice queries আছে।

MySQL setup ও Docker configuration `README.md`-এ আছে। এখানে SQLite demo এবং ২২টি automated test যাচাই করা হয়েছে। Live MySQL/Docker test এখনও করা হয়নি।
