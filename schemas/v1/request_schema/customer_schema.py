from pydantic import BaseModel
from typing import Optional

CUSTOMER_CREATE_MANDATORY_FIELDS={'shop_id':str}

class CreateCustomerSchema(BaseModel):
    datas:dict


CUSTOMER_UPDATE_MANDATORY_FIELDS={'id':str,'shop_id':str}
class UpdateCustomerSchema(BaseModel):
    datas:dict

# name:Optional[str]=None
# description:Optional[str]=None
# category:Optional[ProductCategoryEnum]=None