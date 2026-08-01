from pydantic import BaseModel,EmailStr,Field
from typing import Optional,Dict,List
from core.data_formats.typ_dicts.customer_typdict import CustomerAddressTypDict
from core.data_formats.enums.customer_enums import CustomerCreditHistoryEnums,CustomerOutstandingAddEnums,CustomerOutstandingClearedPaymentMethods,PaymentMethodsEnums
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from .custom_types import CustomerContactInfosType,CustomerCreditInfosType,CustomerLocationInfosType,CustomerOutstandingInfosType,CustomerClearedInfosType,CustomerPaymentInfosType


# Writable Schemas
class CreateCustomerDbSchema(BaseModel):
    id:str
    ui_id:str
    shop_id:str
    name:str
    contact_infos:CustomerContactInfosType
    credit_infos:Optional[CustomerCreditInfosType]
    location_infos:CustomerLocationInfosType
    can_have_credit:bool
    

class UpdateCustomerDbSchema(BaseModel):
    id:str
    shop_id:str
    name:Optional[str]=None
    contact_infos:Optional[CustomerContactInfosType]=None
    credit_infos:Optional[CustomerCreditInfosType]=None
    location_infos:Optional[CustomerLocationInfosType]=None
    can_have_credit:Optional[bool]


class DeleteCustomerDbSchema(BaseModel):
    id:str
    shop_id:str



class CreateCustomerOutstandingDbSchema(BaseModel):
    id:str
    shop_id:str
    outstanding_infos:CustomerOutstandingInfosType
    type:CustomerOutstandingAddEnums



class CreateCustomerOutstandingClearedDbSchema(BaseModel):
    shop_id:str
    customer_id:str
    payment_infos:List[CustomerPaymentInfosType]
    cleared_infos:CustomerClearedInfosType
    additional_infos:Optional[dict]=None