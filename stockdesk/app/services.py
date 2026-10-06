import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from fastapi import HTTPException
from sqlalchemy import select
from . import models as m

def cents(value):
    return int((Decimal(value) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def fingerprint(payload):
    data = payload.model_dump(mode='json', exclude={'request_id'})
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def audit(db, user_id, action, detail):
    db.add(m.AuditEvent(user_id=user_id, action=action, detail=detail))

def get_or_404(db, model, id):
    row = db.get(model, id)
    if not row:
        raise HTTPException(404, f'{model.__name__} not found.')
    return row

def product_dict(row):
    return {k: getattr(row, k) for k in ('id','sku','name','category','price_cents','cost_cents','stock','reorder_level','active')}

def contact_dict(row):
    return {k: getattr(row, k) for k in ('id','name','phone','email','address')}

def invoice_dict(row, detail=False):
    status = 'Cancelled' if row.cancelled else ('Paid' if row.paid_cents == row.total_cents else ('Partial' if row.paid_cents else 'Unpaid'))
    out = {k: getattr(row,k) for k in ('id','customer_id','customer_name','subtotal_cents','discount_cents','tax_cents','tax_percent','total_cents','paid_cents','created_at','note')}
    out.update(number=f'INV-{row.id:06d}', status=status, due_cents=0 if row.cancelled else row.total_cents-row.paid_cents)
    if detail:
        out['lines'] = [{k:getattr(l,k) for k in ('product_id','sku','product_name','quantity','unit_price_cents','line_total_cents')} for l in row.lines]
        out['payments'] = [{k:getattr(p,k) for k in ('id','amount_cents','method','reference','created_at')} for p in row.payments]
    return out

def move_stock(db, payload, user_id, kind):
    prior = db.scalar(select(m.StockMovement).where(m.StockMovement.request_id == payload.request_id))
    digest = hashlib.sha256((kind + fingerprint(payload)).encode()).hexdigest()
    if prior:
        if prior.request_hash != digest:
            raise HTTPException(409, 'Request ID already used for a different stock movement.')
        return prior
    if payload.quantity == 0 or (kind == 'RECEIVE' and payload.quantity < 0):
        raise HTTPException(422, 'Receive quantity must be positive; adjustment must be nonzero.')
    product = db.scalar(select(m.Product).where(m.Product.id == payload.product_id).with_for_update())
    if not product or not product.active:
        raise HTTPException(404, 'Active product not found.')
    if payload.supplier_id:
        get_or_404(db, m.Supplier, payload.supplier_id)
    if product.stock + payload.quantity < 0:
        raise HTTPException(409, f'Adjustment would make stock negative. Current stock: {product.stock}.')
    if product.stock + payload.quantity > 2000000000:
        raise HTTPException(422, 'Stock quantity exceeds the supported limit.')
    product.stock += payload.quantity
    row = m.StockMovement(product_id=product.id, supplier_id=payload.supplier_id, kind=kind, quantity=payload.quantity,
        balance_after=product.stock, request_id=payload.request_id, request_hash=digest,
        reference=payload.reference, reason=payload.reason, created_by=user_id)
    db.add(row)
    audit(db,user_id,'stock.'+kind.lower(),f'{product.sku}: {payload.quantity:+d}. {payload.reason}')
    db.flush()
    return row

def create_invoice(db, payload, user_id):
    digest = fingerprint(payload)
    prior = db.scalar(select(m.Invoice).where(m.Invoice.request_id == payload.request_id))
    if prior:
        if prior.request_hash != digest:
            raise HTTPException(409, 'Request ID already used for a different invoice.')
        return prior
    customer = get_or_404(db,m.Customer,payload.customer_id)
    ids = [item.product_id for item in payload.items]
    if len(ids) != len(set(ids)):
        raise HTTPException(422,'Add each product once and update its quantity.')
    products = {p.id:p for p in db.scalars(select(m.Product).where(m.Product.id.in_(ids)).order_by(m.Product.id).with_for_update())}
    subtotal = 0
    for item in payload.items:
        product = products.get(item.product_id)
        if not product or not product.active:
            raise HTTPException(404,'One or more products are unavailable.')
        if product.stock < item.quantity:
            raise HTTPException(409,f'Insufficient stock for {product.name}. Available: {product.stock}; requested: {item.quantity}.')
        subtotal += product.price_cents * item.quantity
    discount = cents(payload.discount)
    if discount >= subtotal:
        raise HTTPException(422,'Discount must be smaller than the subtotal.')
    tax = int((Decimal(subtotal-discount)*payload.tax_percent/100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    inv=m.Invoice(request_id=payload.request_id,request_hash=digest,customer_id=customer.id,customer_name=customer.name,
        subtotal_cents=subtotal,discount_cents=discount,tax_cents=tax,tax_percent=str(payload.tax_percent),
        total_cents=subtotal-discount+tax,paid_cents=0,note=payload.note,created_by=user_id)
    db.add(inv); db.flush()
    for item in payload.items:
        product=products[item.product_id]
        inv.lines.append(m.InvoiceLine(product_id=product.id,sku=product.sku,product_name=product.name,
            quantity=item.quantity,unit_price_cents=product.price_cents,line_total_cents=product.price_cents*item.quantity))
        product.stock -= item.quantity
        db.add(m.StockMovement(product_id=product.id,invoice_id=inv.id,kind='SALE',quantity=-item.quantity,
            balance_after=product.stock,reference=f'INV-{inv.id:06d}',reason='Sales invoice',created_by=user_id))
    audit(db,user_id,'invoice.create',f'INV-{inv.id:06d}: {inv.total_cents/100:.2f} BDT')
    db.flush()
    return inv

def pay_invoice(db, invoice_id, payload, user_id):
    digest = hashlib.sha256((str(invoice_id)+fingerprint(payload)).encode()).hexdigest()
    prior = db.scalar(select(m.Payment).where(m.Payment.request_id==payload.request_id))
    if prior:
        if prior.request_hash != digest:
            raise HTTPException(409,'Request ID already used for a different payment.')
        return get_or_404(db,m.Invoice,invoice_id)
    inv=db.scalar(select(m.Invoice).where(m.Invoice.id==invoice_id).with_for_update())
    if not inv:
        raise HTTPException(404,'Invoice not found.')
    if inv.cancelled:
        raise HTTPException(409,'Cancelled invoices cannot receive payments.')
    amount=cents(payload.amount)
    if amount > inv.total_cents-inv.paid_cents:
        raise HTTPException(409,f'Payment exceeds outstanding balance of {(inv.total_cents-inv.paid_cents)/100:.2f} BDT.')
    inv.paid_cents += amount
    db.add(m.Payment(invoice_id=inv.id,amount_cents=amount,method=payload.method,reference=payload.reference,
        request_id=payload.request_id,request_hash=digest,created_by=user_id))
    audit(db,user_id,'payment.create',f'INV-{inv.id:06d}: {amount/100:.2f} BDT via {payload.method}')
    db.flush(); db.expire(inv,['payments'])
    return inv

def cancel_invoice(db, invoice_id, reason, user_id):
    inv=db.scalar(select(m.Invoice).where(m.Invoice.id==invoice_id).with_for_update())
    if not inv:
        raise HTTPException(404,'Invoice not found.')
    if inv.cancelled:
        return inv
    if inv.paid_cents:
        raise HTTPException(409,'An invoice with payments cannot be cancelled. Refunds are outside this project scope.')
    products={p.id:p for p in db.scalars(select(m.Product).where(m.Product.id.in_([l.product_id for l in inv.lines])).order_by(m.Product.id).with_for_update())}
    for line in inv.lines:
        product=products[line.product_id]
        product.stock += line.quantity
        db.add(m.StockMovement(product_id=product.id,invoice_id=inv.id,kind='CANCEL',quantity=line.quantity,
            balance_after=product.stock,reference=f'INV-{inv.id:06d}',reason=reason,created_by=user_id))
    inv.cancelled=True
    audit(db,user_id,'invoice.cancel',f'INV-{inv.id:06d}: {reason}')
    db.flush()
    return inv
