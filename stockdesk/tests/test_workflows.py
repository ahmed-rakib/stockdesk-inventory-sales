import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

TEST_DB=Path(os.getenv('STOCKDESK_TEST_DB',str(Path(__file__).resolve().parents[1]/'data'/'test-suite.db'))).resolve()
TEST_DB.parent.mkdir(exist_ok=True,parents=True)
os.environ['DATABASE_URL']='sqlite:///'+TEST_DB.as_posix()
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from app.main import app
from app.db import Base,engine,SessionLocal
from app import models as m
from app.security import hash_password

class Workflows(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(engine);Base.metadata.create_all(engine)
        with SessionLocal.begin() as db:
            db.add_all([m.User(username='admin',role='admin',password_hash=hash_password('TestPass123!')),
                m.User(username='staff',role='staff',password_hash=hash_password('TestPass123!'))])
            db.add(m.Customer(name='Test customer'));db.add(m.Supplier(name='Test supplier'))
            db.add_all([m.Product(sku='P-1',name='Keyboard',category='Office',price_cents=12345,cost_cents=9000,stock=20,reorder_level=5),
                m.Product(sku='P-2',name='Mouse',category='Office',price_cents=10000,cost_cents=6000,stock=1,reorder_level=3)])
        self.client=TestClient(app)
        self.login()

    def tearDown(self):self.client.close()

    @classmethod
    def tearDownClass(cls):
        engine.dispose()
        if TEST_DB.exists():TEST_DB.unlink()

    def login(self,username='admin'):
        response=self.client.post('/api/auth/login',json={'username':username,'password':'TestPass123!'})
        self.assertEqual(response.status_code,200,response.text)
        self.client.headers['X-CSRF-Token']=response.json()['csrf_token']

    def sale(self,**overrides):
        body={'customer_id':1,'items':[{'product_id':1,'quantity':2}],'request_id':str(uuid4()),**overrides}
        return self.client.post('/api/invoices',json=body)

    def invoice(self,**overrides):
        response=self.sale(**overrides);self.assertEqual(response.status_code,201,response.text);return response.json()

    def pay(self,id,amount,request_id=None):
        return self.client.post(f'/api/invoices/{id}/payments',json={'amount':amount,'method':'Cash','request_id':request_id or str(uuid4())})

    def stock(self,id=1):
        return next(p['stock'] for p in self.client.get('/api/products').json() if p['id']==id)

    def test_login_cookie_and_logout(self):
        self.assertIn('HttpOnly',self.client.post('/api/auth/login',json={'username':'admin','password':'TestPass123!'}).headers['set-cookie'])
        self.login();self.assertEqual(self.client.post('/api/auth/logout').status_code,200)
        self.assertEqual(self.client.get('/api/products').status_code,401)

    def test_bad_login_and_anonymous_api(self):
        self.assertEqual(self.client.post('/api/auth/login',json={'username':'admin','password':'wrong'}).status_code,401)
        self.assertEqual(TestClient(app).get('/api/products').status_code,401)

    def test_csrf_and_cross_origin(self):
        self.client.headers['X-CSRF-Token']='wrong'
        self.assertEqual(self.sale().status_code,403)
        self.login()
        self.assertEqual(self.client.post('/api/auth/logout',headers={'Origin':'https://other.example'}).status_code,403)

    def test_staff_permissions(self):
        self.login('staff')
        self.assertEqual(self.client.get('/api/users').status_code,403)
        self.assertEqual(self.client.get('/api/audit').status_code,403)
        self.assertEqual(self.client.post('/api/stock/adjust',json={'product_id':1,'quantity':1,'reason':'Count fix','request_id':str(uuid4())}).status_code,403)
        self.assertEqual(self.sale().status_code,201)

    def test_create_product_and_duplicate_sku(self):
        data={'sku':'P-3','name':'Monitor','category':'Displays','price':'100.10','cost':'60.25','reorder_level':2}
        response=self.client.post('/api/products',json=data)
        self.assertEqual(response.status_code,201);self.assertEqual(response.json()['price_cents'],10010)
        self.assertEqual(response.json()['stock'],0)
        self.assertEqual(self.client.post('/api/products',json=data).status_code,409)

    def test_price_precision_and_integer_quantities(self):
        data={'sku':'P-3','name':'Monitor','category':'Displays','price':'0.105'}
        self.assertEqual(self.client.post('/api/products',json=data).status_code,422)
        self.assertEqual(self.sale(items=[{'product_id':1,'quantity':1.5}]).status_code,422)
        self.assertEqual(self.sale(items=[{'product_id':1,'quantity':True}]).status_code,422)

    def test_stock_receive_idempotency_and_conflict(self):
        data={'product_id':1,'quantity':5,'supplier_id':1,'reason':'Delivery received','request_id':str(uuid4())}
        self.assertEqual(self.client.post('/api/stock/receive',json=data).status_code,201)
        self.assertEqual(self.client.post('/api/stock/receive',json=data).status_code,201)
        self.assertEqual(self.stock(),25)
        self.assertEqual(self.client.get('/api/stock/movements').json()[0]['product_sku'],'P-1')
        self.assertEqual(self.client.post('/api/stock/receive',json={**data,'quantity':6}).status_code,409)

    def test_negative_adjustment_rollback(self):
        response=self.client.post('/api/stock/adjust',json={'product_id':1,'quantity':-21,'reason':'Bad adjustment','request_id':str(uuid4())})
        self.assertEqual(response.status_code,409);self.assertEqual(self.stock(),20)
        self.assertEqual(len(self.client.get('/api/stock/movements').json()),0)

    def test_invalid_receive_and_missing_supplier(self):
        data={'product_id':1,'quantity':-1,'reason':'Delivery received','request_id':str(uuid4())}
        self.assertEqual(self.client.post('/api/stock/receive',json=data).status_code,422)
        self.assertEqual(self.client.post('/api/stock/receive',json={**data,'quantity':1,'supplier_id':999}).status_code,404)

    def test_invoice_totals_tax_and_ledger(self):
        inv=self.invoice(discount='10.00',tax_percent='5')
        self.assertEqual(inv['subtotal_cents'],24690);self.assertEqual(inv['tax_cents'],1185)
        self.assertEqual(inv['total_cents'],24875);self.assertEqual(self.stock(),18)
        movement=self.client.get('/api/stock/movements').json()[0]
        self.assertEqual(movement['quantity'],-2);self.assertEqual(movement['balance_after'],18)

    def test_insufficient_stock_atomic_multi_item(self):
        response=self.sale(items=[{'product_id':1,'quantity':3},{'product_id':2,'quantity':2}])
        self.assertEqual(response.status_code,409);self.assertEqual(self.stock(),20)
        self.assertEqual(self.client.get('/api/invoices').json(),[])
        self.assertEqual(self.client.get('/api/stock/movements').json(),[])

    def test_duplicate_invoice_retries(self):
        request_id=str(uuid4());one=self.invoice(request_id=request_id);two=self.invoice(request_id=request_id)
        self.assertEqual(one['id'],two['id']);self.assertEqual(self.stock(),18)
        self.assertEqual(self.sale(request_id=request_id,discount='1').status_code,409)

    def test_duplicate_lines_and_excess_discount(self):
        self.assertEqual(self.sale(items=[{'product_id':1,'quantity':1},{'product_id':1,'quantity':1}]).status_code,422)
        self.assertEqual(self.sale(discount='246.90').status_code,422)
        self.assertEqual(self.stock(),20)

    def test_partial_full_and_overpayment(self):
        inv=self.invoice()
        one=self.pay(inv['id'],'100.00');self.assertEqual(one.status_code,201);self.assertEqual(one.json()['status'],'Partial')
        self.assertEqual(one.json()['due_cents'],14690)
        self.assertEqual(self.pay(inv['id'],'146.91').status_code,409)
        last=self.pay(inv['id'],'146.90');self.assertEqual(last.json()['status'],'Paid')
        self.assertEqual(last.json()['due_cents'],0)

    def test_payment_idempotency(self):
        inv=self.invoice();request_id=str(uuid4())
        self.pay(inv['id'],'50.00',request_id);response=self.pay(inv['id'],'50.00',request_id)
        self.assertEqual(response.json()['paid_cents'],5000)
        self.assertEqual(len(response.json()['payments']),1)
        self.assertEqual(self.pay(inv['id'],'60.00',request_id).status_code,409)

    def test_cancel_restores_stock_once_and_excludes_sales(self):
        inv=self.invoice()
        for _ in range(2):self.assertEqual(self.client.post(f'/api/invoices/{inv["id"]}/cancel',json={'reason':'Customer cancelled'}).status_code,200)
        self.assertEqual(self.stock(),20)
        self.assertEqual(self.client.get('/api/dashboard').json()['sales_cents'],0)
        self.assertEqual(self.pay(inv['id'],'1.00').status_code,409)

    def test_paid_invoice_cannot_cancel(self):
        inv=self.invoice();self.pay(inv['id'],'1.00')
        self.assertEqual(self.client.post(f'/api/invoices/{inv["id"]}/cancel',json={'reason':'Cancel test'}).status_code,409)
        self.assertEqual(self.stock(),18)

    def test_invoice_snapshots_survive_catalog_edits(self):
        inv=self.invoice()
        self.client.put('/api/products/1',json={'sku':'P-NEW','name':'Renamed','category':'Office','price':'999','cost':'20','active':False})
        self.client.put('/api/customers/1',json={'name':'Renamed customer'})
        detail=self.client.get(f'/api/invoices/{inv["id"]}').json()
        self.assertEqual(detail['customer_name'],'Test customer');self.assertEqual(detail['lines'][0]['product_name'],'Keyboard')
        self.assertEqual(detail['lines'][0]['unit_price_cents'],12345)
        self.assertEqual(self.sale().status_code,404)

    def test_reports_and_csv_formula_safety(self):
        self.client.put('/api/customers/1',json={'name':'=HYPERLINK("bad")'})
        inv=self.invoice();self.pay(inv['id'],'100')
        report=self.client.get('/api/reports/receivables').json()
        self.assertEqual(report['due_cents'],14690)
        csv=self.client.get('/api/export/sales.csv')
        self.assertEqual(csv.status_code,200);self.assertIn("'=HYPERLINK",csv.text)
        self.assertIn('total_bdt',csv.text);self.assertIn('246.90',csv.text)
        self.assertEqual(self.client.get('/api/reports/sales?start=2026-10-10&end=2026-10-01').status_code,422)

    def test_concurrent_sales_cannot_oversell(self):
        def order(_):return self.sale(items=[{'product_id':2,'quantity':1}]).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(order,range(2)))
        self.assertEqual(sorted(results),[201,409]);self.assertEqual(self.stock(2),0)

    def test_user_creation_and_audit(self):
        response=self.client.post('/api/users',json={'username':'newstaff','password':'LongPassword123!','role':'staff'})
        self.assertEqual(response.status_code,201);self.assertNotIn('password_hash',response.json())
        self.assertEqual(self.client.get('/api/audit').json()[0]['action'],'user.create')

    def test_health_and_frontend(self):
        self.assertEqual(self.client.get('/health').json()['status'],'ok')
        response=self.client.get('/');self.assertEqual(response.status_code,200)
        self.assertIn('StockDesk',response.text)
        self.assertIn("script-src 'self'",response.headers['content-security-policy'])

if __name__=='__main__':unittest.main(verbosity=2)
