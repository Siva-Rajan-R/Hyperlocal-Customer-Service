from ..main import AsyncSession
from ..repos.customer_repo import CustomerRepo,Optional,CreateCustomerDbSchema,UpdateCustomerDbSchema
from schemas.v1.request_schema.customer_schema import CreateCustomerSchema,UpdateCustomerSchema
from models.service_models.base_service_model import BaseServiceModel
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from core.decorators.error_handler_dec import catch_errors
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from typing import Optional,List
from ..models.customer_model import Customers

class CustomerService(BaseServiceModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.customer_repo_obj=CustomerRepo(session=session)

    async def create(self,data:CreateCustomerSchema):
        
        customer_id:str=generate_uuid()
        data=CreateCustomerDbSchema(
            **data.model_dump(mode='json'),
            id=customer_id
        )

        res=await self.customer_repo_obj.create(data=data)
        if not res:
            return False
        
        return data
    

    async def create_bulk(self,datas:List[CreateCustomerSchema]):
        datas_toadd=[]
        for data in datas:
            datas_toadd.append(
                Customers(id=generate_uuid(),**data.model_dump(mode='json'))
            )

        return await self.customer_repo_obj.create_bulk(datas=datas_toadd)

    async def update(self,data:UpdateCustomerSchema):
        data=UpdateCustomerDbSchema(**data.model_dump(mode='json',exclude_none=True,exclude_unset=True))
        res=await self.customer_repo_obj.update(data=data)
        if not res:
            return False
        
        return True


    async def delete(self,customer_id:str,shop_id:str):
        res=await self.customer_repo_obj.delete(customer_id=customer_id,shop_id=shop_id)
        if not res:
            return False
        
        return True

    async def check_bulk(self,datas:list):
        return await self.customer_repo_obj.check_bulk(data=datas)

    async def get(self,timezone:TimeZoneEnum,query:Optional[str]="",limit:Optional[int]=10,offset:int=1):
        offset=offset-1
        res=await self.customer_repo_obj.get(query=query,limit=limit,offset=offset,timezone=timezone)
        return res


    async def getby_id(self,timezone:TimeZoneEnum,customer_id:str,shop_id:str):
        res=await self.customer_repo_obj.getby_id(timezone=timezone,customer_id=customer_id,shop_id=shop_id)
        return res
    

    async def search(self, query:str, limit:Optional[int]=5):
        res=await self.customer_repo_obj.search(query=query,limit=limit)
        return res