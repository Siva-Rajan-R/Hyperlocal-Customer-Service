from pydantic import BaseModel,EmailStr,Field
from typing import Optional,List,Dict
from core.data_formats.enums.customer_enums import CustomerPaymentTermsEnums,PaymentMethodsEnums


class CustomerContactInfosType(BaseModel):
    mobile_number:Optional[str]=None
    email:Optional[EmailStr]=None

class CustomerCreditInfosType(BaseModel):
    limit:float
    notes:Optional[str]=None
    terms:Optional[CustomerPaymentTermsEnums]=None

class CustomerLocationInfosType(BaseModel):
    zipcode:str
    country:str
    state:str
    full_address:str

class CustomerOutstandingInfosType(BaseModel):
    amount:float


# Cleared Schemas
class CustomerPaymentInfosType(BaseModel):
    method:PaymentMethodsEnums
    amount:float

class CustomerClearedInfosType(BaseModel):
    outstanding_before:float
    outstanding_after:float