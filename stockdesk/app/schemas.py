from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class Payload(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

Money = Decimal
class LoginIn(Payload):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)

class UserIn(Payload):
    username: str = Field(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_.-]+$')
    password: str = Field(min_length=10, max_length=128)
    role: Literal['admin', 'staff'] = 'staff'

class ProductIn(Payload):
    sku: str = Field(min_length=1, max_length=50, pattern=r'^[A-Za-z0-9_-]+$')
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=80)
    price: Decimal = Field(gt=0, le=10000000, decimal_places=2)
    cost: Decimal = Field(default=Decimal('0'), ge=0, le=10000000, decimal_places=2)
    reorder_level: int = Field(default=5, ge=0, le=1000000, strict=True)
    active: bool = True

class ContactIn(Payload):
    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(default='', max_length=40)
    email: str = Field(default='', max_length=120)
    address: str = Field(default='', max_length=250)

class MovementIn(Payload):
    product_id: int = Field(gt=0, strict=True)
    quantity: int = Field(ge=-1000000, le=1000000, strict=True)
    supplier_id: int | None = Field(default=None, gt=0)
    reference: str = Field(default='', max_length=120)
    reason: str = Field(min_length=3, max_length=250)
    request_id: str = Field(min_length=10, max_length=64)

class SaleItem(Payload):
    product_id: int = Field(gt=0, strict=True)
    quantity: int = Field(gt=0, le=1000000, strict=True)

class InvoiceIn(Payload):
    customer_id: int = Field(gt=0, strict=True)
    items: list[SaleItem] = Field(min_length=1, max_length=50)
    discount: Decimal = Field(default=Decimal('0'), ge=0, le=100000000, decimal_places=2)
    tax_percent: Decimal = Field(default=Decimal('0'), ge=0, le=100, decimal_places=2)
    note: str = Field(default='', max_length=500)
    request_id: str = Field(min_length=10, max_length=64)

class PaymentIn(Payload):
    amount: Decimal = Field(gt=0, le=100000000, decimal_places=2)
    method: Literal['Cash', 'Bank', 'bKash', 'Nagad'] = 'Cash'
    reference: str = Field(default='', max_length=120)
    request_id: str = Field(min_length=10, max_length=64)

class CancelIn(Payload):
    reason: str = Field(min_length=3, max_length=250)
