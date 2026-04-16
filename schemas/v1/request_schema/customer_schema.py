from pydantic import BaseModel
from typing import Optional

class CreateCustomerSchema(BaseModel):
    shop_id:str
    datas:dict


class UpdateCustomerSchema(BaseModel):
    id:str
    shop_id:str
    datas:dict

# name:Optional[str]=None
# description:Optional[str]=None
# category:Optional[ProductCategoryEnum]=None