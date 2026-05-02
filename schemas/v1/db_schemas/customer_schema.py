from pydantic import BaseModel,EmailStr
from typing import Optional

class CreateCustomerDbSchema(BaseModel):
    id:str
    shop_id:str
    name:str
    email:EmailStr
    mobile_number:str
    credit_limit:float
    is_active:bool
    datas:Optional[dict]={}


class UpdateCustomerDbSchema(BaseModel):
    id:str
    shop_id:str
    name:Optional[str]=None
    email:Optional[EmailStr]=None
    mobile_number:Optional[str]=None
    credit_limit:Optional[float]=None
    is_active:Optional[bool]=None
    datas:Optional[dict]=None
    datas:Optional[dict]={}
