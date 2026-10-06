from datetime import datetime, timezone
from sqlalchemy import String, Integer, BigInteger, Boolean, DateTime, ForeignKey, CheckConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(250))
    role: Mapped[str] = mapped_column(String(20), default='staff')

class LoginSession(Base):
    __tablename__ = 'login_sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    csrf_token: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime)

class Product(Base):
    __tablename__ = 'products'
    __table_args__ = (CheckConstraint('stock >= 0'), CheckConstraint('price_cents > 0'), CheckConstraint('cost_cents >= 0'))
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(80), default='General')
    price_cents: Mapped[int] = mapped_column(BigInteger)
    cost_cents: Mapped[int] = mapped_column(BigInteger, default=0)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, default=5)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Customer(Base):
    __tablename__ = 'customers'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(40), default='')
    email: Mapped[str] = mapped_column(String(120), default='')
    address: Mapped[str] = mapped_column(String(250), default='')

class Supplier(Base):
    __tablename__ = 'suppliers'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(40), default='')
    email: Mapped[str] = mapped_column(String(120), default='')
    address: Mapped[str] = mapped_column(String(250), default='')

class Invoice(Base):
    __tablename__ = 'invoices'
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[str] = mapped_column(String(64), unique=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id'))
    customer_name: Mapped[str] = mapped_column(String(120))
    subtotal_cents: Mapped[int] = mapped_column(BigInteger)
    discount_cents: Mapped[int] = mapped_column(BigInteger, default=0)
    tax_cents: Mapped[int] = mapped_column(BigInteger, default=0)
    tax_percent: Mapped[str] = mapped_column(String(10), default='0')
    total_cents: Mapped[int] = mapped_column(BigInteger)
    paid_cents: Mapped[int] = mapped_column(BigInteger, default=0)
    cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str] = mapped_column(String(500), default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    lines: Mapped[list['InvoiceLine']] = relationship(cascade='all, delete-orphan', order_by='InvoiceLine.id')
    payments: Mapped[list['Payment']] = relationship(order_by='Payment.id')
    __table_args__ = (CheckConstraint('paid_cents >= 0 AND paid_cents <= total_cents'), CheckConstraint('total_cents > 0'))

class InvoiceLine(Base):
    __tablename__ = 'invoice_lines'
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey('invoices.id'), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    sku: Mapped[str] = mapped_column(String(50))
    product_name: Mapped[str] = mapped_column(String(120))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price_cents: Mapped[int] = mapped_column(BigInteger)
    line_total_cents: Mapped[int] = mapped_column(BigInteger)
    __table_args__ = (CheckConstraint('quantity > 0'),)

class Payment(Base):
    __tablename__ = 'payments'
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey('invoices.id'), index=True)
    request_id: Mapped[str] = mapped_column(String(64), unique=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    amount_cents: Mapped[int] = mapped_column(BigInteger)
    method: Mapped[str] = mapped_column(String(30))
    reference: Mapped[str] = mapped_column(String(120), default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    __table_args__ = (CheckConstraint('amount_cents > 0'),)

class StockMovement(Base):
    __tablename__ = 'stock_movements'
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), index=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey('suppliers.id'), nullable=True)
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey('invoices.id'), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    request_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    kind: Mapped[str] = mapped_column(String(30))
    quantity: Mapped[int] = mapped_column(Integer)
    balance_after: Mapped[int] = mapped_column(Integer)
    reference: Mapped[str] = mapped_column(String(120), default='')
    reason: Mapped[str] = mapped_column(String(250))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    __table_args__ = (CheckConstraint('balance_after >= 0'), CheckConstraint('quantity != 0'))

class AuditEvent(Base):
    __tablename__ = 'audit_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    action: Mapped[str] = mapped_column(String(60))
    detail: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
