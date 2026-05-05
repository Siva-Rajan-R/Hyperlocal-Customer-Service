from schemas.v1.request_schemas.customer_schema import CreateCustomerSchema,UpdateCustomerSchema,DeleteCustomerSchema,GetAllCustomerSchema,GetCustomerByIdSchema,GetCustomerByShopIdSchema
from schemas.v1.response_schemas.user_schemas.customer_schema import CustomerCreateResponseSchema,CustomerDeleteResponseSchema,CustomerGetResponseSchema,CustomerUpdateResponseSchema
from models.service_models.base_service_model import BaseServiceModel
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from fastapi.exceptions import HTTPException
from core.decorators.error_handler_dec import catch_errors
from infras.primary_db.services.customer_service import CustomerService
from sqlalchemy.ext.asyncio import AsyncSession
from core.utils.validate_fields import validate_fields,validate_internal_fields
from typing import Optional,List
from icecream import ic

class HandleCustomerRequest(BaseServiceModel):
    def __init__(self, session:AsyncSession):
        self.session=session


    async def create(self,data:CreateCustomerSchema):
        res=await CustomerService(session=self.session).create(data=data)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    msg="Error : Creating customer",
                    description="Invalid datas for creating customers or Customer already exists",
                    status_code=400,
                    success=False
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Customer created successfully",
                status_code=201,
                success=True
            ),
            data=CustomerCreateResponseSchema(**res) if res else None
        )


    async def update(self,data:UpdateCustomerSchema):
        res=await CustomerService(session=self.session).update(data=data)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    msg="Error : Updating customer",
                    description="Invalid customer id for updating customers",
                    status_code=400,
                    success=False
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Customer updated successfully",
                status_code=200,
                success=True
            ),
            data=CustomerUpdateResponseSchema(**res) if res else None
        )


    async def delete(self,data:DeleteCustomerSchema):
        res=await CustomerService(session=self.session).delete(data=data)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    msg="Error : Deleting customer",
                    description="Invalid customer id for deleting customer",
                    status_code=400,
                    success=False
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Customer deleted successfully",
                status_code=200,
                success=True
            ),
            data=CustomerDeleteResponseSchema(**res) if res else None
        )


    async def get(self,data:GetAllCustomerSchema):
        res=await CustomerService(session=self.session).get(data=data)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Customer fetched successfully",
                status_code=200,
                success=True
            ),
            data=[CustomerGetResponseSchema(**r) for r in res] if res else None
        )


    async def getby_id(self,data:GetCustomerByIdSchema):
        res=await CustomerService(session=self.session).getby_id(data=data)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Customer fetched successfully",
                status_code=200,
                success=True
            ),
            data=CustomerGetResponseSchema(**res) if res else None
        )
    

    async def getby_shop_id(self,data:GetCustomerByShopIdSchema):
        ic(data)
        res=await CustomerService(session=self.session).getby_shop_id(data=data)
        ic(res)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Customer fetched successfully",
                status_code=200,
                success=True
            ),
            data=[CustomerGetResponseSchema(**r) for r in res] if res else None
        )


    async def search(self, query:str, limit:Optional[int]=5):
        res=await CustomerService(session=self.session).search(query=query,limit=limit)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Customer fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
        )