from typing import Optional,List
from pydantic import BaseModel,EmailStr
from pydantic import BaseModel,EmailStr
from datetime import date,datetime
from typing import Union


class CustomerCreateResponseSchema(BaseModel):
    id:str
    shop_id:str
    ui_id:Union[str, int]
    name:str
    email:EmailStr
    mobile_number:str
    credit_limit:float
    outstanding:float
    is_active:bool
    datas:Optional[dict]={}

    created_at:datetime
    updated_at:datetime


class CustomerUpdateResponseSchema(BaseModel):
    id:str
    shop_id:str
    ui_id:Union[str, int]
    name:str
    email:EmailStr
    mobile_number:str
    outstanding:float
    credit_limit:float
    is_active:bool
    datas:Optional[dict]={}

    created_at:datetime
    updated_at:datetime

class CustomerDeleteResponseSchema(BaseModel):
    id:str
    shop_id:str
    ui_id:Union[str, int]
    name:str
    email:EmailStr
    mobile_number:str
    outstanding:float
    credit_limit:float
    is_active:bool
    datas:Optional[dict]={}

    created_at:datetime
    updated_at:datetime

class CustomerGetResponseSchema(BaseModel):
    id:str
    shop_id:str
    ui_id:Union[str, int]
    name:str
    email:EmailStr
    mobile_number:str
    outstanding:float
    credit_limit:float
    is_active:bool
    datas:Optional[dict]={}

    created_at:datetime
    updated_at:datetime


