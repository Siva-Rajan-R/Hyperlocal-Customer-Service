from ..main import BASE
from sqlalchemy import Column, String,ForeignKey,Integer,TIMESTAMP,func,BigInteger,Identity,Float,Boolean,BIGINT,UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB



class Customers(BASE):
    __tablename__ = "customers"
    id = Column(String, primary_key=True)
    ui_id=Column(String,nullable=False,index=True)
    sequence_id=Column(BigInteger,Identity(always=True),nullable=False)
    shop_id=Column(String, nullable=False)
    name=Column(String,nullable=False)
    contact_infos=Column(JSONB)
    credit_infos=Column(JSONB)
    location_infos=Column(JSONB)
    outstanding_infos=Column(JSONB)
    can_have_credit=Column(Boolean)
    additional_infos=Column(JSONB)

    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now())
    updated_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())

    cust_out_clr_hist=relationship("CustomerOutstandingClearedHistories",back_populates="customer",cascade="all, delete-orphan")


class CustomerOutstandingClearedHistories(BASE):
    __tablename__="customer_outstanding_cleared_histories"
    id=Column(BigInteger,primary_key=True,autoincrement=True)
    shop_id=Column(String,nullable=False)
    customer_id=Column(String,ForeignKey("customers.id",ondelete="CASCADE"),nullable=False)
    payment_infos=Column(JSONB,nullable=False)
    cleared_infos=Column(JSONB)
    additional_infos=Column(JSONB)

    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now())
    updated_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())

    customer=relationship("Customers",back_populates="cust_out_clr_hist")