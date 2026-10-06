import csv
import io
import logging
import os
import secrets
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Request, Response, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func, delete, or_
from sqlalchemy.exc import IntegrityError, OperationalError
from .db import Base, engine, get_db
from . import models as m, schemas as s, services as svc
from .security import current_user, admin_user, hash_password, check_password, token_hash, COOKIE

log = logging.getLogger('stockdesk')
STATIC = Path(__file__).parent / 'static'

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    yield

app=FastAPI(title='StockDesk Inventory and Sales API',version='1.0.0',lifespan=lifespan,
    description='All monetary output fields ending in _cents are integer poisha (BDT × 100). Login creates a cookie; mutations require the X-CSRF-Token returned by login or /api/auth/me.')
app.mount('/static',StaticFiles(directory=STATIC),name='static')

@app.middleware('http')
async def secure_headers(request: Request, call_next):
    if request.method not in ('GET','HEAD','OPTIONS'):
        origin=request.headers.get('origin')
        if origin and origin.rstrip('/') != str(request.base_url).rstrip('/'):
            return JSONResponse(status_code=403,content={'detail':'Cross-origin changes are not allowed.'})
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='same-origin'
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control']='no-store'
    else:
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    return response

@app.exception_handler(IntegrityError)
async def integrity_error(request, exc):
    log.warning('Constraint conflict on %s',request.url.path)
    return JSONResponse(status_code=409,content={'detail':'A duplicate identifier or conflicting change was detected. Refresh and try again.'})

@app.exception_handler(OperationalError)
async def operation_error(request, exc):
    log.error('Database operation failed on %s',request.url.path)
    return JSONResponse(status_code=503,content={'detail':'Database temporarily unavailable. Retry this action using the same request ID.'})

@app.get('/',include_in_schema=False)
def home():
    return FileResponse(STATIC/'index.html')

@app.get('/health')
def health(db=Depends(get_db, scope='function')):
    db.execute(select(1))
    return {'status':'ok','database':engine.dialect.name}

@app.post('/api/auth/login')
def login(data:s.LoginIn,response:Response,db=Depends(get_db, scope='function')):
    user=db.scalar(select(m.User).where(m.User.username==data.username))
    if not user or not check_password(data.password,user.password_hash):
        raise HTTPException(401,'Invalid username or password.')
    db.execute(delete(m.LoginSession).where(m.LoginSession.expires_at<=m.utcnow()))
    token=secrets.token_urlsafe(32)
    csrf=secrets.token_hex(32)
    db.add(m.LoginSession(token_hash=token_hash(token),user_id=user.id,csrf_token=csrf,expires_at=m.utcnow()+timedelta(hours=8)))
    response.set_cookie(COOKIE,token,httponly=True,samesite='strict',secure=os.getenv('COOKIE_SECURE','false').lower()=='true',max_age=8*3600)
    return {'username':user.username,'role':user.role,'csrf_token':csrf}

@app.get('/api/auth/me')
def me(request:Request,user=Depends(current_user),db=Depends(get_db, scope='function')):
    session=db.get(m.LoginSession,token_hash(request.cookies[COOKIE]))
    return {'username':user.username,'role':user.role,'csrf_token':session.csrf_token}

@app.post('/api/auth/logout')
def logout(request:Request,response:Response,user=Depends(current_user),db=Depends(get_db, scope='function')):
    session=db.get(m.LoginSession,token_hash(request.cookies[COOKIE]))
    db.delete(session)
    response.delete_cookie(COOKIE)
    return {'message':'Signed out.'}

@app.get('/api/users')
def users(user=Depends(admin_user),db=Depends(get_db, scope='function')):
    return [{'id':u.id,'username':u.username,'role':u.role} for u in db.scalars(select(m.User).order_by(m.User.id))]

@app.post('/api/users',status_code=201)
def add_user(data:s.UserIn,user=Depends(admin_user),db=Depends(get_db, scope='function')):
    row=m.User(username=data.username,password_hash=hash_password(data.password),role=data.role)
    db.add(row);db.flush()
    svc.audit(db,user.id,'user.create',f'{row.username}: {row.role}')
    return {'id':row.id,'username':row.username,'role':row.role}

@app.get('/api/products')
def products(q:str=Query('',max_length=100),user=Depends(current_user),db=Depends(get_db, scope='function')):
    stmt=select(m.Product).order_by(m.Product.name)
    if q:
        stmt=stmt.where(or_(m.Product.name.contains(q,autoescape=True),m.Product.sku.contains(q,autoescape=True)))
    return [svc.product_dict(p) for p in db.scalars(stmt)]

@app.post('/api/products',status_code=201)
def add_product(data:s.ProductIn,user=Depends(admin_user),db=Depends(get_db, scope='function')):
    values=data.model_dump(exclude={'price','cost'})
    row=m.Product(**values,price_cents=svc.cents(data.price),cost_cents=svc.cents(data.cost),stock=0)
    db.add(row);db.flush()
    svc.audit(db,user.id,'product.create',row.sku)
    return svc.product_dict(row)

@app.put('/api/products/{product_id}')
def edit_product(product_id:int,data:s.ProductIn,user=Depends(admin_user),db=Depends(get_db, scope='function')):
    row=db.scalar(select(m.Product).where(m.Product.id==product_id).with_for_update())
    if not row:
        raise HTTPException(404,'Product not found.')
    for key,value in data.model_dump(exclude={'price','cost'}).items():
        setattr(row,key,value)
    row.price_cents=svc.cents(data.price);row.cost_cents=svc.cents(data.cost)
    svc.audit(db,user.id,'product.update',row.sku)
    db.flush()
    return svc.product_dict(row)

@app.get('/api/customers')
def customers(user=Depends(current_user),db=Depends(get_db, scope='function')):
    return [svc.contact_dict(c) for c in db.scalars(select(m.Customer).order_by(m.Customer.name))]

@app.post('/api/customers',status_code=201)
def add_customer(data:s.ContactIn,user=Depends(current_user),db=Depends(get_db, scope='function')):
    row=m.Customer(**data.model_dump());db.add(row);db.flush()
    svc.audit(db,user.id,'customer.create',row.name)
    return svc.contact_dict(row)

@app.put('/api/customers/{contact_id}')
def edit_customer(contact_id:int,data:s.ContactIn,user=Depends(current_user),db=Depends(get_db, scope='function')):
    row=svc.get_or_404(db,m.Customer,contact_id)
    for k,v in data.model_dump().items():setattr(row,k,v)
    svc.audit(db,user.id,'customer.update',row.name);db.flush()
    return svc.contact_dict(row)

@app.get('/api/suppliers')
def suppliers(user=Depends(current_user),db=Depends(get_db, scope='function')):
    return [svc.contact_dict(c) for c in db.scalars(select(m.Supplier).order_by(m.Supplier.name))]

@app.post('/api/suppliers',status_code=201)
def add_supplier(data:s.ContactIn,user=Depends(admin_user),db=Depends(get_db, scope='function')):
    row=m.Supplier(**data.model_dump());db.add(row);db.flush()
    svc.audit(db,user.id,'supplier.create',row.name)
    return svc.contact_dict(row)

@app.put('/api/suppliers/{contact_id}')
def edit_supplier(contact_id:int,data:s.ContactIn,user=Depends(admin_user),db=Depends(get_db, scope='function')):
    row=svc.get_or_404(db,m.Supplier,contact_id)
    for k,v in data.model_dump().items():setattr(row,k,v)
    svc.audit(db,user.id,'supplier.update',row.name);db.flush()
    return svc.contact_dict(row)

def movement_dict(row,product_name='',supplier_name='',product_sku=''):
    return {**{k:getattr(row,k) for k in ('id','product_id','supplier_id','invoice_id','kind','quantity','balance_after','reference','reason','created_at')},'product_name':product_name,'supplier_name':supplier_name,'product_sku':product_sku}

@app.get('/api/stock/movements')
def movements(product_id:int|None=None,limit:int=Query(100,ge=1,le=1000),user=Depends(current_user),db=Depends(get_db, scope='function')):
    stmt=select(m.StockMovement,m.Product.name,m.Supplier.name,m.Product.sku).join(m.Product,m.StockMovement.product_id==m.Product.id).outerjoin(m.Supplier,m.StockMovement.supplier_id==m.Supplier.id).order_by(m.StockMovement.id.desc()).limit(limit)
    if product_id:stmt=stmt.where(m.StockMovement.product_id==product_id)
    return [movement_dict(row,pname,sname or '',sku) for row,pname,sname,sku in db.execute(stmt)]

@app.post('/api/stock/receive',status_code=201)
def receive(data:s.MovementIn,user=Depends(current_user),db=Depends(get_db, scope='function')):
    return movement_dict(svc.move_stock(db,data,user.id,'RECEIVE'))

@app.post('/api/stock/adjust',status_code=201)
def adjust(data:s.MovementIn,user=Depends(admin_user),db=Depends(get_db, scope='function')):
    return movement_dict(svc.move_stock(db,data,user.id,'ADJUST'))

@app.get('/api/invoices')
def invoices(q:str=Query('',max_length=100),user=Depends(current_user),db=Depends(get_db, scope='function')):
    rows=db.scalars(select(m.Invoice).order_by(m.Invoice.id.desc()))
    result=[svc.invoice_dict(i) for i in rows]
    return [i for i in result if not q or q.lower() in (i['number']+' '+i['customer_name']).lower()]

@app.post('/api/invoices',status_code=201)
def create_invoice(data:s.InvoiceIn,user=Depends(current_user),db=Depends(get_db, scope='function')):
    return svc.invoice_dict(svc.create_invoice(db,data,user.id),True)

@app.get('/api/invoices/{invoice_id}')
def invoice_detail(invoice_id:int,user=Depends(current_user),db=Depends(get_db, scope='function')):
    return svc.invoice_dict(svc.get_or_404(db,m.Invoice,invoice_id),True)

@app.post('/api/invoices/{invoice_id}/payments',status_code=201)
def payment(invoice_id:int,data:s.PaymentIn,user=Depends(current_user),db=Depends(get_db, scope='function')):
    return svc.invoice_dict(svc.pay_invoice(db,invoice_id,data,user.id),True)

@app.post('/api/invoices/{invoice_id}/cancel')
def cancel(invoice_id:int,data:s.CancelIn,user=Depends(admin_user),db=Depends(get_db, scope='function')):
    return svc.invoice_dict(svc.cancel_invoice(db,invoice_id,data.reason,user.id),True)

def date_filter(stmt, start, end):
    if start and end and start>end:
        raise HTTPException(422,'Start date must be before the end date.')
    if start:stmt=stmt.where(m.Invoice.created_at>=datetime.combine(start,datetime.min.time()))
    if end:stmt=stmt.where(m.Invoice.created_at<datetime.combine(end+timedelta(days=1),datetime.min.time()))
    return stmt

@app.get('/api/dashboard')
def dashboard(user=Depends(current_user),db=Depends(get_db, scope='function')):
    sold,paid,count=db.execute(select(func.coalesce(func.sum(m.Invoice.total_cents),0),func.coalesce(func.sum(m.Invoice.paid_cents),0),func.count()).where(m.Invoice.cancelled.is_(False))).one()
    stock_value=db.scalar(select(func.coalesce(func.sum(m.Product.stock*m.Product.cost_cents),0)))
    low=list(db.scalars(select(m.Product).where(m.Product.active.is_(True),m.Product.stock<=m.Product.reorder_level).order_by(m.Product.stock)))
    dates=[(m.utcnow()-timedelta(days=i)).date() for i in reversed(range(7))]
    grouped=dict(db.execute(select(func.date(m.Invoice.created_at),func.sum(m.Invoice.total_cents)).where(m.Invoice.cancelled.is_(False),m.Invoice.created_at>=datetime.combine(dates[0],datetime.min.time())).group_by(func.date(m.Invoice.created_at))).all())
    return {'sales_cents':sold,'collected_cents':paid,'due_cents':sold-paid,'invoice_count':count,
        'product_count':db.scalar(select(func.count()).select_from(m.Product).where(m.Product.active.is_(True))),
        'inventory_value_cents':stock_value,'low_stock':[svc.product_dict(p) for p in low],
        'sales_trend':[{'date':str(d),'total_cents':grouped.get(str(d),grouped.get(d,0))} for d in dates],
        'recent_invoices':[svc.invoice_dict(i) for i in db.scalars(select(m.Invoice).order_by(m.Invoice.id.desc()).limit(5))]}

@app.get('/api/reports/{kind}')
def report(kind:str,start:date|None=None,end:date|None=None,user=Depends(current_user),db=Depends(get_db, scope='function')):
    if kind=='inventory':
        rows=[{**svc.product_dict(p),'value_cents':p.stock*p.cost_cents,'low_stock':p.active and p.stock<=p.reorder_level} for p in db.scalars(select(m.Product).order_by(m.Product.name))]
        return {'rows':rows,'total_value_cents':sum(r['value_cents'] for r in rows)}
    if kind not in ('sales','receivables'):
        raise HTTPException(404,'Report not found.')
    stmt=date_filter(select(m.Invoice).where(m.Invoice.cancelled.is_(False)).order_by(m.Invoice.id.desc()),start,end)
    if kind=='receivables':stmt=stmt.where(m.Invoice.total_cents>m.Invoice.paid_cents)
    rows=[svc.invoice_dict(i) for i in db.scalars(stmt)]
    return {'rows':rows,'sales_cents':sum(r['total_cents'] for r in rows),'paid_cents':sum(r['paid_cents'] for r in rows),'due_cents':sum(r['due_cents'] for r in rows)}

@app.get('/api/export/{kind}.csv')
def export(kind:str,start:date|None=None,end:date|None=None,user=Depends(current_user),db=Depends(get_db, scope='function')):
    data=report(kind,start,end,user,db)
    rows=data['rows']
    keys=['sku','name','category','stock','reorder_level','active','price_cents','cost_cents','value_cents'] if kind=='inventory' else ['number','customer_name','created_at','status','total_cents','paid_cents','due_cents']
    stream=io.StringIO(newline='');writer=csv.writer(stream)
    writer.writerow([k.replace('_cents','_bdt') for k in keys])
    for row in rows:
        values=[]
        for key in keys:
            value=row.get(key,'')
            if key.endswith('_cents'):value=f'{Decimal(value)/100:.2f}'
            # Neutralize spreadsheet formulas, including leading whitespace/control chars.
            if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@')):value="'"+value
            values.append(value)
        writer.writerow(values)
    return Response('\ufeff'+stream.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="stockdesk-{kind}.csv"'})

@app.get('/api/audit')
def audit_log(user=Depends(admin_user),db=Depends(get_db, scope='function')):
    rows=db.execute(select(m.AuditEvent,m.User.username).join(m.User,m.AuditEvent.user_id==m.User.id).order_by(m.AuditEvent.id.desc()).limit(200))
    return [{'id':a.id,'username':name,'action':a.action,'detail':a.detail,'created_at':a.created_at} for a,name in rows]


