"""Idempotent portfolio demo initialization. Run: python -m app.seed."""
import os
from datetime import timedelta
from sqlalchemy import select, func
from .db import Base, engine, SessionLocal
from . import models as m, schemas as s, services as svc
from .security import hash_password

def seed():
    Base.metadata.create_all(engine)
    with SessionLocal.begin() as db:
        if db.scalar(select(func.count()).select_from(m.User)):
            print('Database already initialized. Existing data was preserved.')
            return
        password=os.getenv('APP_ADMIN_PASSWORD','DemoPass123!')
        if len(password)<10:raise ValueError('APP_ADMIN_PASSWORD must contain at least 10 characters.')
        admin=m.User(username='admin',password_hash=hash_password(password),role='admin')
        db.add(admin);db.flush()
        supplier=m.Supplier(name='Northstar Distribution',phone='01700-000001',email='supplier@example.com',address='Dhaka')
        db.add(supplier)
        customers=[m.Customer(name=name,phone=f'01700-00000{i+2}',email=f'customer{i+1}@example.com',address='Dhaka') for i,name in enumerate(['Orion Office','Bluebird Studio','Walk-in Customer'])]
        db.add_all(customers);db.flush()
        items=[('KB-101','Wireless Keyboard','Accessories',1450,1050,32,10),('MS-201','Wireless Mouse','Accessories',850,550,7,8),('MON-301','24 inch Monitor','Displays',16500,13000,12,4),('USB-401','USB-C Hub','Accessories',2200,1600,4,6),('SSD-501','512 GB SSD','Storage',4500,3600,22,5),('CAM-601','HD Webcam','Accessories',2800,2100,14,4)]
        products=[]
        for sku,name,category,price,cost,stock,reorder in items:
            p=m.Product(sku=sku,name=name,category=category,price_cents=price*100,cost_cents=cost*100,stock=stock,reorder_level=reorder)
            db.add(p);db.flush();products.append(p)
            db.add(m.StockMovement(product_id=p.id,supplier_id=supplier.id,kind='OPENING',quantity=stock,balance_after=stock,reference='DEMO-OPENING',reason='Opening demo stock',created_by=admin.id,created_at=m.utcnow()-timedelta(days=5)))
        for i in range(5):
            inv=svc.create_invoice(db,s.InvoiceIn(customer_id=customers[i%3].id,items=[s.SaleItem(product_id=products[i%len(products)].id,quantity=i%2+1)],tax_percent='5',request_id=f'demo-invoice-{i:03}'),admin.id)
            inv.created_at=m.utcnow()-timedelta(days=4-i)
            for movement in db.scalars(select(m.StockMovement).where(m.StockMovement.invoice_id==inv.id)):
                movement.created_at=inv.created_at
            if i%3!=0:
                amount=inv.total_cents if i%3==1 else inv.total_cents//2
                svc.pay_invoice(db,inv.id,s.PaymentIn(amount=str(amount/100),method='Cash',request_id=f'demo-payment-{i:03}'),admin.id)
                for payment in inv.payments:payment.created_at=inv.created_at
        svc.audit(db,admin.id,'demo.initialize','Fictional sample records created.')
    print('StockDesk initialized. Username: admin')
    print('Password: value of APP_ADMIN_PASSWORD (default local demo: DemoPass123!)')

if __name__=='__main__':seed()
