from pydantic import BaseModel,EmailStr,Field
from typing import Optional,Dict,List
from core.data_formats.typ_dicts.customer_typdict import CustomerAddressTypDict
from core.data_formats.enums.customer_enums import CustomerCreditHistoryEnums,CustomerOutstandingAddEnums,CustomerOutstandingClearedPaymentMethods,PaymentMethodsEnums
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from .custom_types import CustomerContactInfosType,CustomerCreditInfosType,CustomerLocationInfosType,CustomerOutstandingInfosType,CustomerClearedInfosType,CustomerPaymentInfosType


# Writable Schemas
class CreateCustomerSchema(BaseModel):
    shop_id:str
    name:str
    contact_infos:CustomerContactInfosType
    credit_infos:Optional[CustomerCreditInfosType]=None
    location_infos:CustomerLocationInfosType
    can_have_credit:bool
    custom_fields:Optional[dict]={}


class UpdateCustomerSchema(BaseModel):
    id:str
    shop_id:str
    name:Optional[str]=None
    contact_infos:Optional[CustomerContactInfosType]=None
    credit_infos:Optional[CustomerCreditInfosType]=None
    location_infos:Optional[CustomerLocationInfosType]=None
    can_have_credit:Optional[bool]
    custom_fields:Optional[dict]=None


class DeleteCustomerSchema(BaseModel):
    id:str
    shop_id:str


class CreateCustomerOutstandingSchema(BaseModel):
    id:str
    shop_id:str
    outstanding_infos:CustomerOutstandingInfosType
    type:CustomerOutstandingAddEnums
    
    


class CreateCustomerOutstandingClearedSchema(BaseModel):
    shop_id:str
    customer_id:str
    payment_infos:List[CustomerPaymentInfosType]



# Fetchable Schemas
class GetAllCustomerSchema(BaseModel):
    query:str=Field(default="",alias="q")
    limit:int=Field(default=10,le=100)
    offset:int=Field(default=1)
    from_date:Optional[str]=None
    to_date:Optional[str]=None


class GetCustomerByShopIdSchema(BaseModel):
    shop_id:str
    query:str=Field(default="",alias="q")
    limit:int=Field(default=10,le=100)
    offset:int=Field(default=1)
    from_date:Optional[str]=None
    to_date:Optional[str]=None


class GetCustomerByIdSchema(BaseModel):
    id:str
    shop_id:str


# 
class GetAllCustomerOutstClearedSchema(BaseModel):
    query:str=Field(default="",alias="q")
    limit:int=Field(default=10,le=100)
    offset:int=Field(default=1)
    from_date:Optional[str]=None
    to_date:Optional[str]=None


class GetCustomerOutstClearedByShopIdSchema(BaseModel):
    shop_id:str
    query:str=Field(default="",alias="q")
    limit:int=Field(default=10,le=100)
    offset:int=Field(default=1)
    from_date:Optional[str]=None
    to_date:Optional[str]=None


class GetCustomerOutstClearedByIdSchema(BaseModel):
    id:int
    shop_id:str
