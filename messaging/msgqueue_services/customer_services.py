from infras.primary_db.services.customer_service import CustomerService
from sqlalchemy.ext.asyncio import AsyncSession
from infras.primary_db.main import AsyncCustomerLocalSession
from schemas.v1.request_schemas.customer_schema import CreateCustomerSchema,UpdateCustomerSchema,DeleteCustomerSchema,GetAllCustomerSchema,GetCustomerByIdSchema,GetCustomerByShopIdSchema,VerifyCustomerSchema,DeductCustomerCreditSchema
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from schemas.v1.response_schemas.msgqueue_schemas.customer_schema import CustomerCreateResponseSchema,CustomerDeleteResponseSchema,CustomerGetResponseSchema,CustomerUpdateResponseSchema
from typing import Optional,List,Union
from icecream import ic

class MessagingQueueCustomerService:

    async def create_customer(self,data:Union[CreateCustomerSchema,dict]):

        if isinstance(data, dict):
            data = CreateCustomerSchema(**data)
        async with AsyncCustomerLocalSession() as session:
            customer_service_obj=CustomerService(session=session)
            res=await customer_service_obj.create(data=data)
            ic(res)
            if not res:
                return res
            return CustomerCreateResponseSchema(
                **res
            ).model_dump(mode="json")

    async def update_customer(self,data:Union[UpdateCustomerSchema,dict]):
        async with AsyncCustomerLocalSession() as session:
            customer_service_obj=CustomerService(session=session)
            if isinstance(data, dict):
                data = UpdateCustomerSchema(**data)
            res=await customer_service_obj.update(data=data)
            if not res:
                return res
            return CustomerUpdateResponseSchema(**res).model_dump(mode="json")

    async def delete_customer(self,data:Union[DeleteCustomerSchema,dict]):
        async with AsyncCustomerLocalSession() as session:
            customer_service_obj=CustomerService(session=session)
            if isinstance(data, dict):
                data = DeleteCustomerSchema(**data)
            res=await customer_service_obj.delete(data=data)
            if not res:
                return res
            return CustomerDeleteResponseSchema(**res).model_dump(mode="json")
        
    async def deduct_credit_customer(self,data:Union[DeductCustomerCreditSchema,dict]):
        async with AsyncCustomerLocalSession() as session:
            customer_service_obj=CustomerService(session=session)
            if isinstance(data, dict):
                data = DeductCustomerCreditSchema(**data)
            
            res=await customer_service_obj.deduct_credit(data=data)
            if not res:
                return res
            
            return CustomerGetResponseSchema(**res) if res else None

    async def get_customers(self,data:Union[GetAllCustomerSchema,dict]):
        async with AsyncCustomerLocalSession() as session:
            customer_service_obj=CustomerService(session=session)
            if isinstance(data, dict):
                data = GetAllCustomerSchema(**data)
            res=await customer_service_obj.get(data=data)
            if not res:
                return res
            return [CustomerGetResponseSchema(**r).model_dump(mode="json") for r in res]
    
    async def get_customer_by_id(self,data:Union[GetCustomerByIdSchema,dict]):
        async with AsyncCustomerLocalSession() as session:
            customer_service_obj=CustomerService(session=session)
            if isinstance(data, dict):
                data = GetCustomerByIdSchema(**data)
            res=await customer_service_obj.getby_id(data=data)
            if not res:
                return res 
            return CustomerGetResponseSchema(**res).model_dump(mode="json")
        
    async def get_customer_by_shop_id(self,data:GetCustomerByShopIdSchema):
        async with AsyncCustomerLocalSession() as session:
            customer_service_obj=CustomerService(session=session)
            if isinstance(data, dict):
                data = GetCustomerByIdSchema(**data)
            res=await customer_service_obj.getby_shop_id(data=data)
            if not res:
                return res 
            return CustomerGetResponseSchema(**res).model_dump(mode="json")
        
    async def verify_customer(self,data:Union[VerifyCustomerSchema,dict])-> bool:
        ic(data)
        async with AsyncCustomerLocalSession() as session:
            customer_service_obj=CustomerService(session=session)
            if isinstance(data, dict):
                data = VerifyCustomerSchema(**data)
            res=await customer_service_obj.verify(data=data)
            return res