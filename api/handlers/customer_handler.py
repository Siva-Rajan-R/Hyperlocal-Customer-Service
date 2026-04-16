from schemas.v1.request_schema.customer_schema import CreateCustomerSchema,UpdateCustomerSchema
from models.service_models.base_service_model import BaseServiceModel
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from fastapi.exceptions import HTTPException
from core.decorators.error_handler_dec import catch_errors
from infras.primary_db.services.customer_service import CustomerService
from sqlalchemy.ext.asyncio import AsyncSession
from core.utils.validate_fields import validate_fields
from typing import Optional,List

class HandleCustomerRequest(BaseServiceModel):
    def __init__(self, session:AsyncSession):
        self.session=session


    async def create(self,data:CreateCustomerSchema):
        # await validate_fields(service_name="CUSTOMER",shop_id="",incoming_fields=data.datas)

        res=await CustomerService(session=self.session).create(data=data)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    msg="Error : Creating customer",
                    description="Invalid datas for creating customers",
                    status_code=400,
                    success=False
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Customer created successfully",
                status_code=201,
                success=True
            )
        )


    async def update(self,data:UpdateCustomerSchema):
        # await validate_fields(service_name="CUSTOMER",shop_id="",incoming_fields=data.datas)
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
            )
        )


    async def delete(self,customer_id:str,shop_id:str):
        res=await CustomerService(session=self.session).delete(customer_id=customer_id,shop_id=shop_id)
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
            )
        )


    async def get(self,timezone:TimeZoneEnum,query:Optional[str]="",limit:Optional[int]=10,offset:int=1):
        res=await CustomerService(session=self.session).get(query=query,limit=limit,offset=offset,timezone=timezone)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Customer fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
        )


    async def getby_id(self,timezone:TimeZoneEnum,shop_id:str,customer_id:str):
        res=await CustomerService(session=self.session).getby_id(timezone=timezone,shop_id=shop_id,customer_id=customer_id)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Customer fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
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