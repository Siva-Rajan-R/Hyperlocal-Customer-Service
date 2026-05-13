from pydantic import BaseModel,EmailStr,Field
from typing import Optional
from core.data_formats.typ_dicts.customer_typdict import CustomerAddressTypDict
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum


# Optional Field Schemas
class CustomerOptionalFieldsSchema(BaseModel):
    address:Optional[CustomerAddressTypDict]={}
    additional_notes:Optional[str]=None
    payment_cycle:Optional[str]=None



# Writable Schemas
class CreateCustomerSchema(BaseModel):
    shop_id:str
    name:str
    email:EmailStr
    mobile_number:str
    credit_limit:Optional[float]=0
    is_active:bool
    datas:Optional[CustomerOptionalFieldsSchema]={}


class UpdateCustomerSchema(BaseModel):
    id:str
    shop_id:str
    name:Optional[str]=None
    email:Optional[EmailStr]=None
    mobile_number:Optional[str]=None
    credit_limit:Optional[float]=None
    is_active:Optional[bool]=None
    datas:Optional[CustomerOptionalFieldsSchema]=None


class DeleteCustomerSchema(BaseModel):
    id:str
    shop_id:str



# Fetchable Schemas
class GetAllCustomerSchema(BaseModel):
    query:str=Field(default="",alias="q")
    limit:int=Field(default=10,le=100)
    offset:int=Field(default=1)
    timezone:Optional[TimeZoneEnum]=TimeZoneEnum.Asia_Kolkata


class GetCustomerByShopIdSchema(BaseModel):
    shop_id:str
    query:str=Field(default="",alias="q")
    limit:int=Field(default=10,le=100)
    offset:int=Field(default=1)
    timezone:Optional[TimeZoneEnum]=TimeZoneEnum.Asia_Kolkata


class GetCustomerByIdSchema(BaseModel):
    timezone:Optional[TimeZoneEnum]=TimeZoneEnum.Asia_Kolkata
    id:str
    shop_id:str

class DeductCustomerCreditSchema(BaseModel):
    id:str
    shop_id:str
    amount:float


class VerifyCustomerSchema(BaseModel):
    shop_id:str
    email:Optional[EmailStr]=None
    mobile_number:Optional[str]=None

# name:Optional[str]=None
# description:Optional[str]=None
# category:Optional[ProductCategoryEnum]=None