from pydantic import BaseModel
from typing import Optional

class CreateCustomerDbSchema(BaseModel):
    id:str
    shop_id:str
    datas:dict


class UpdateCustomerDbSchema(BaseModel):
    id:str
    shop_id:str
    datas:dict