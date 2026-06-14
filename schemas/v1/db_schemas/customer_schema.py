from pydantic import BaseModel,EmailStr
from typing import Optional,Dict
from core.data_formats.enums.customer_enums import CustomerCreditHistoryEnums,CustomerPaymentCycleEnums,CustomerOutstandingClearedPaymentMethods

class CreateCustomerDbSchema(BaseModel):
    id:str
    ui_id:str
    shop_id:str
    name:str
    email:EmailStr
    mobile_number:str
    credit_limit:float
    is_active:bool
    outstanding:float
    datas:Optional[dict]={}


class UpdateCustomerDbSchema(BaseModel):
    id:str
    shop_id:str
    name:Optional[str]=None
    email:Optional[EmailStr]=None
    mobile_number:Optional[str]=None
    credit_limit:Optional[float]=None
    is_active:Optional[bool]=None
    datas:Optional[dict]={}

class CreditHistoryCustomerDbSchema(BaseModel):
    shop_id:str
    customer_id:str
    credit_before:float
    credit_after:float
    type:CustomerCreditHistoryEnums

class OutstandingClearedCustomerDbSchema(BaseModel):
    shop_id:str
    customer_id:str
    payments:Dict[CustomerOutstandingClearedPaymentMethods,float]
    cleared_amount:float
    outstanding_after:float
    outstanding_before:float
