from ..main import BASE
from sqlalchemy import Column, String,ForeignKey,Integer,TIMESTAMP,func,BigInteger,Identity,Float,Boolean,BIGINT,UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB



class Customers(BASE):
    __tablename__ = "customers"
    id = Column(String, primary_key=True)
    ui_id=Column(String,nullable=False,index=True)
    sequence_id=Column(BigInteger,Identity(always=True),nullable=False)
    shop_id=Column(String, nullable=False)
    name=Column(String,nullable=False)
    email=Column(String,nullable=False)
    mobile_number=Column(String,nullable=False)
    credit_limit=Column(Float,nullable=False)
    outstanding=Column(Float,nullable=False)
    is_active=Column(Boolean,nullable=False)
    datas=Column(JSONB,nullable=False)

    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now())
    updated_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())

class CustomerCreditHistories(BASE):
    __tablename__="customer_credit_histories"
    id=Column(BigInteger,primary_key=True,autoincrement=True)
    shop_id=Column(String,nullable=False)
    customer_id=Column(String,nullable=False)
    credit_before=Column(Float,nullable=False)
    credit_after=Column(Float,nullable=False)
    type=Column(String,nullable=False)

    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now())
    updated_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())


class CustomerOutstandingClearedHistories(BASE):
    __tablename__="customer_outstanding_cleared_histories"
    id=Column(BigInteger,primary_key=True,autoincrement=True)
    shop_id=Column(String,nullable=False)
    customer_id=Column(String,nullable=False)
    payments=Column(JSONB,nullable=False)
    cleared_amount=Column(Float,nullable=False)
    outstanding_before=Column(Float,nullable=False)
    outstanding_after=Column(Float,nullable=False)

    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now())
    updated_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())