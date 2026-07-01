from infras.primary_db.services.customer_service import CustomerService
from sqlalchemy.ext.asyncio import AsyncSession
from infras.primary_db.main import AsyncCustomerLocalSession
from schemas.v1.customer_schemas.request_schemas import CreateCustomerSchema,UpdateCustomerSchema,DeleteCustomerSchema,GetAllCustomerOutstClearedSchema,GetAllCustomerSchema,GetCustomerByIdSchema,GetCustomerByShopIdSchema,GetCustomerOutstClearedByIdSchema,GetCustomerOutstClearedByShopIdSchema,CreateCustomerOutstandingClearedSchema,CreateCustomerOutstandingSchema

from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from schemas.v1.customer_schemas.response_schemas.msgqueue_schemas.customer_schema import CustomerCreateResponseSchema,CustomerDeleteResponseSchema,CustomerGetResponseSchema,CustomerUpdateResponseSchema
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
        

    async def get_customers(self,data:Union[GetAllCustomerSchema,dict]):
        async with AsyncCustomerLocalSession() as session:
            customer_service_obj=CustomerService(session=session)
            if isinstance(data, dict):
                data = GetAllCustomerSchema(**data)
            res=await customer_service_obj.get_customers(data=data)
            if not res:
                return res
            return [CustomerGetResponseSchema(**r).model_dump(mode="json") for r in res]
    
    async def get_customer_by_id(self,data:Union[GetCustomerByIdSchema,dict]):
        async with AsyncCustomerLocalSession() as session:
            customer_service_obj=CustomerService(session=session)
            if isinstance(data, dict):
                data = GetCustomerByIdSchema(**data)
            res=await customer_service_obj.get_customer_by_id(data=data)
            if not res:
                return res 
            return res
        
    async def get_customer_by_shop_id(self,data:GetCustomerByShopIdSchema):
        async with AsyncCustomerLocalSession() as session:
            customer_service_obj=CustomerService(session=session)
            if isinstance(data, dict):
                data = GetCustomerByIdSchema(**data)
            res=await customer_service_obj.get_customer_by_shop_id(data=data)
            if not res:
                return res 
            return CustomerGetResponseSchema(**res).model_dump(mode="json")
        
    async def add_customer_outstanding(self,data:Union[CreateCustomerOutstandingSchema,dict]):
        async with AsyncCustomerLocalSession() as session:
            customer_service_obj=CustomerService(session=session)
            if isinstance(data, dict):
                data = CreateCustomerOutstandingSchema(**data)
            res=await customer_service_obj.add_outstanding(data=data)
            if not res:
                return res
            return res
        
    async def clear_customer_outstanding(self,data:Union[CreateCustomerOutstandingClearedSchema,dict]):
        async with AsyncCustomerLocalSession() as session:
            customer_service_obj=CustomerService(session=session)
            if isinstance(data, dict):
                data = CreateCustomerOutstandingClearedSchema(**data)
            res=await customer_service_obj.clear_outstanding(data=data)
            if not res:
                return res
            return res