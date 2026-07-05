from schemas.v1.customer_schemas.request_schemas import CreateCustomerSchema,UpdateCustomerSchema,DeleteCustomerSchema,GetAllCustomerOutstClearedSchema,GetAllCustomerSchema,GetCustomerByIdSchema,GetCustomerByShopIdSchema,GetCustomerOutstClearedByIdSchema,GetCustomerOutstClearedByShopIdSchema,CreateCustomerOutstandingClearedSchema,CreateCustomerOutstandingSchema
from schemas.v1.customer_schemas.custom_types import CustomerCreditInfosType
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
from infras.primary_db.repos.customfield_repo import CustomFieldsRepo
from schemas.v1.db_schemas.customfield_schema import CreateCustomFieldValueDbSchema
from core.utils.validate_custom_fields import validate_and_filter_custom_fields
class HandleCustomerRequest:
    def __init__(self, session:AsyncSession):
        self.session=session

    # Writables
    async def create(self,data:CreateCustomerSchema):
        if data.can_have_credit and not data.credit_infos:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error Creating Customer",
                    description="Credit limit could not be empty when customer is eligible for the credit",
                    success=False
                )
            )

        if not data.contact_infos.email and not data.contact_infos.mobile_number:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error Creating Customer",
                    description="Please provide a atleast one of the contact info (Email or Mobile number)",
                    success=False
                )
            )
        
        credit_infos=CustomerCreditInfosType(limit=data.credit_infos.limit,notes=data.credit_infos.notes,terms=data.credit_infos.terms)
        if not data.can_have_credit:
            credit_infos=CustomerCreditInfosType(limit=0,notes=None,terms=None)
            
        defined_fields = await CustomFieldsRepo(session=self.session).get_all_fields(shop_id=data.shop_id)
        valid_custom_fields = validate_and_filter_custom_fields(data.custom_fields, defined_fields)

        final_data=CreateCustomerSchema(credit_infos=credit_infos,**data.model_dump(exclude=['credit_infos', 'custom_fields']))
        res=await CustomerService(session=self.session).create(data=final_data)
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
            
        defined_fields_map = {field['field_name']: field['id'] for field in defined_fields}
        for field_name, value in valid_custom_fields.items():
            field_id = defined_fields_map.get(field_name)
            if field_id:
                await CustomFieldsRepo(session=self.session).upsert_field_value(
                    data=CreateCustomFieldValueDbSchema(
                        id=generate_uuid(),
                        shop_id=data.shop_id,
                        customer_id=res['id'],
                        field_id=field_id,
                        value=str(value)
                    )
                )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Customer created successfully",
                status_code=201,
                success=True
            ),
            data=res if res else None
        )


    async def update(self,data:UpdateCustomerSchema):
        if data.can_have_credit and not data.credit_infos:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error Creating Customer",
                    description="Credit limit could not be empty when customer is eligible for the credit",
                    success=False
                )
            )

        if data.contact_infos and (not data.contact_infos.email and not data.contact_infos.mobile_number):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error Creating Customer",
                    description="Please provide a atleast one of the contact info (Email or Mobile number)",
                    success=False
                )
            )
        
        credit_infos=CustomerCreditInfosType(limit=data.credit_infos.limit,notes=data.credit_infos.notes,terms=data.credit_infos.terms)
        if not data.can_have_credit:
            credit_infos=CustomerCreditInfosType(limit=0,notes=None,terms=None)
            
        defined_fields = await CustomFieldsRepo(session=self.session).get_all_fields(shop_id=data.shop_id)
        valid_custom_fields = validate_and_filter_custom_fields(data.custom_fields, defined_fields)

        final_data=UpdateCustomerSchema(credit_infos=credit_infos,**data.model_dump(exclude=['credit_infos', 'custom_fields']))
        res=await CustomerService(session=self.session).update(data=final_data)
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
            
        defined_fields_map = {field['field_name']: field['id'] for field in defined_fields}
        for field_name, value in valid_custom_fields.items():
            field_id = defined_fields_map.get(field_name)
            if field_id:
                await CustomFieldsRepo(session=self.session).upsert_field_value(
                    data=CreateCustomFieldValueDbSchema(
                        id=generate_uuid(),
                        shop_id=data.shop_id,
                        customer_id=res['id'],
                        field_id=field_id,
                        value=str(value)
                    )
                )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Customer updated successfully",
                status_code=200,
                success=True
            ),
            data=res if res else None
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
            data=res if res else None
        )
    

    async def add_outstanding(self,data:CreateCustomerOutstandingSchema) -> dict | None:
        res=await CustomerService(session=self.session).add_outstanding(data=data)
        ic(res)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Outstanding added successfully",
                status_code=200,
                success=True
            ),
            data=res if res else None
        )
    
    
    async def clear_outstanding(self,data:CreateCustomerOutstandingClearedSchema) -> dict | None:
        res=await CustomerService(session=self.session).clear_outstanding(data=data)
        ic(res)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Outstanding cleared successfully",
                status_code=200,
                success=True
            ),
            data=res if res else None
        )
    

    # Readabels
    async def get_customers(self,data:GetAllCustomerSchema):
        res=await CustomerService(session=self.session).get_customers(data=data)

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Customer fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
        )
    

    async def get_customer_by_id(self,data:GetCustomerByIdSchema):
        res=await CustomerService(session=self.session).get_customer_by_id(data=data)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Customer fetched successfully",
                status_code=200,
                success=True
            ),
            data=res if res else None
        )
    

    async def get_customer_by_shop_id(self,data:GetCustomerByShopIdSchema):
        ic(data)
        res=await CustomerService(session=self.session).get_customer_by_shop_id(data=data)

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Customer fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
        )
    


    async def get_outst_clr(self,data:GetAllCustomerOutstClearedSchema) -> List[dict] | None:
        res=await CustomerService(session=self.session).get_outst_clr(data=data)
        ic(res)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Customer outstanding fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
        )
    
    async def get_outst_clr_by_shop_id(self,data:GetCustomerOutstClearedByShopIdSchema) -> List[dict] | None:
        res=await CustomerService(session=self.session).get_outst_clr_by_shop_id(data=data)
        ic(res)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Customer outstanding fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
        )
    
    async def get_outst_clr_by_id(self,data:GetCustomerOutstClearedByIdSchema) -> dict | None:
        res=await CustomerService(session=self.session).get_outst_clr_by_id(data=data)
        ic(res)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Customer outstanding fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
        )


    