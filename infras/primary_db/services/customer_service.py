from ..main import AsyncSession
from ..repos.customer_repo import CustomerRepo
from schemas.v1.db_schemas.customer_schema import CreateCustomerDbSchema,UpdateCustomerDbSchema,CreditHistoryCustomerDbSchema
from schemas.v1.request_schemas.customer_schema import CreateCustomerSchema,UpdateCustomerSchema,DeleteCustomerSchema,GetAllCustomerSchema,GetCustomerByIdSchema,GetCustomerByShopIdSchema,VerifyCustomerSchema,DeductCustomerCreditSchema
from models.service_models.base_service_model import BaseServiceModel
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from core.decorators.error_handler_dec import catch_errors
from core.data_formats.enums.customer_enums import CustomerCreditHistoryEnums
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from typing import Optional,List
from ..models.customer_model import Customers
from icecream import ic

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

        customer_res=await self.customer_repo_obj.create(data=data_toadd)
        return customer_res
    

    async def update(self,data:UpdateCustomerSchema) -> dict | None:
        previous_credit=(await self.getby_id(data=GetCustomerByIdSchema(id=data.id,shop_id=data.shop_id)))
        ic(previous_credit)
        if not previous_credit:
            return False
        
        data_toupdate=UpdateCustomerDbSchema(
            **data.model_dump(mode='json',exclude_none=True,exclude_unset=True)
        )
        customer_res=await self.customer_repo_obj.update(data=data_toupdate)
        if customer_res and data.credit_limit and data.credit_limit!=previous_credit['credit_limit'] and previous_credit['is_active']==True:
            customer_credit_res=await self.customer_repo_obj.create_credit_history(
                data=CreditHistoryCustomerDbSchema(
                    id=generate_uuid(),
                    shop_id=data.shop_id,
                    customer_id=data.id,
                    credit_before=previous_credit['credit_limit'],
                    credit_after=customer_res['credit_limit'],
                    type=CustomerCreditHistoryEnums.UPDATED
                    
                )
            )

            ic(customer_credit_res)

        return customer_res
    

    async def deduct_credit(self,data:DeductCustomerCreditSchema):
        previous_credit=(await self.getby_id(data=GetCustomerByIdSchema(id=data.id,shop_id=data.shop_id)))
        ic(previous_credit)
        if not previous_credit:
            return False
        customer_res=await self.customer_repo_obj.deduct_credit(data=data)
        ic(customer_res)
        if customer_res and previous_credit['is_active']==True:
            customer_credit_res=await self.customer_repo_obj.create_credit_history(
                data=CreditHistoryCustomerDbSchema(
                    id=generate_uuid(),
                    shop_id=data.shop_id,
                    customer_id=data.id,
                    credit_before=previous_credit['credit_limit'],
                    credit_after=customer_res['credit_limit'],
                    type=CustomerCreditHistoryEnums.SALES
                    
                )
            )

            ic(customer_credit_res)
        return customer_res
    


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