from ..main import AsyncSession
from ..repos.customer_repo import CustomerRepo
from schemas.v1.db_schemas.customer_schema import CreateCustomerDbSchema,UpdateCustomerDbSchema
from schemas.v1.request_schemas.customer_schema import CreateCustomerSchema,UpdateCustomerSchema,DeleteCustomerSchema,GetAllCustomerSchema,GetCustomerByIdSchema,GetCustomerByShopIdSchema,VerifyCustomerSchema
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

    async def create(self,data:CreateCustomerSchema) -> dict | None:
        
        customer_id:str=generate_uuid()
        data_toadd=CreateCustomerDbSchema(
            **data.model_dump(mode='json',exclude_none=True,exclude_unset=True),
            id=customer_id,
        )

        res=await self.customer_repo_obj.create(data=data_toadd)
        return res
    

    async def update(self,data:UpdateCustomerSchema) -> dict | None:
        data_toupdate=UpdateCustomerDbSchema(
            **data.model_dump(mode='json',exclude_none=True,exclude_unset=True)
        )
        res=await self.customer_repo_obj.update(data=data_toupdate)
        return res


    async def delete(self,data:DeleteCustomerSchema) -> dict | None:
        res=await self.customer_repo_obj.delete(data=data)
        return res


    async def get(self,data:GetAllCustomerSchema) -> List[dict] | list:
        res=await self.customer_repo_obj.get(data=data)
        return res


    async def getby_id(self,data:GetCustomerByIdSchema) -> dict | None:
        res=await self.customer_repo_obj.getby_id(data=data)
        return res
    
    async def getby_shop_id(self,data:GetCustomerByShopIdSchema) -> List[dict] | list:
        res=await self.customer_repo_obj.getby_shop_id(data=data)
        return res
    
    async def verify(self,data:VerifyCustomerSchema) -> dict:
        res=await self.customer_repo_obj.verify(data=data)
        return res
    




    async def search(self, query:str, limit:Optional[int]=5):
        res=await self.customer_repo_obj.search(query=query,limit=limit)
        return res
    
    async def check_bulk(self,datas:list):
        return await self.customer_repo_obj.check_bulk(data=datas)

    async def create_bulk(self,datas:List[CreateCustomerSchema]):
        datas_toadd=[]
        for data in datas:
            datas_toadd.append(
                Customers(id=generate_uuid(),**data.model_dump(mode='json'))
            )

        return await self.customer_repo_obj.create_bulk(datas=datas_toadd)