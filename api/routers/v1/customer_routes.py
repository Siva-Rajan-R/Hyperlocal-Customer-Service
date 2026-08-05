from fastapi import APIRouter,HTTPException,Query,Depends
from schemas.v1.customer_schemas.request_schemas import CreateCustomerSchema,UpdateCustomerSchema,DeleteCustomerSchema,GetAllCustomerOutstClearedSchema,GetAllCustomerSchema,GetCustomerByIdSchema,GetCustomerByShopIdSchema,GetCustomerOutstClearedByIdSchema,GetCustomerOutstClearedByShopIdSchema,CreateCustomerOutstandingClearedSchema,CreateCustomerOutstandingSchema
from typing import Annotated,Optional,List
from infras.primary_db.main import get_pg_async_session,AsyncSession
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from core.utils.validate_fields import validate_fields
from ...handlers.customer_handler import HandleCustomerRequest
print(TimeZoneEnum)
from icecream import ic

router=APIRouter(
    tags=['Customer CRUD'],
    prefix='/customers'
)

PG_ASYNC_SESSION=Annotated[AsyncSession,Depends(get_pg_async_session)]
SHOP_ID="TEST-SHOP"

# Write methods
@router.post('')
async def create(data:CreateCustomerSchema,session:PG_ASYNC_SESSION):
    return await HandleCustomerRequest(session=session).create(data=data)


@router.post('/bulk')
async def create_bulk(data:List[CreateCustomerSchema],session:PG_ASYNC_SESSION):
    return await HandleCustomerRequest(session=session).create_bulk(data=data)


@router.put('')
async def update(data:UpdateCustomerSchema,session:PG_ASYNC_SESSION):
    return await HandleCustomerRequest(session=session).update(data=data)

@router.delete('/{shop_id}/{id}')
async def delete(session:PG_ASYNC_SESSION,data:DeleteCustomerSchema=Depends()):
    return await HandleCustomerRequest(session=session).delete(data=data)

@router.post('/outstanding/add')
async def add_outstanding(session:PG_ASYNC_SESSION,data:CreateCustomerOutstandingSchema):
    return await HandleCustomerRequest(session=session).add_outstanding(data=data)

@router.post('/outstanding/clear')
async def clear_outstanding(session:PG_ASYNC_SESSION,data:CreateCustomerOutstandingClearedSchema):
    return await HandleCustomerRequest(session=session).clear_outstanding(data=data)


# Read methods
@router.get('/by/shop/{shop_id}')
async def get_cusotmerby_shop_id(session:PG_ASYNC_SESSION,data:GetCustomerByShopIdSchema=Depends()):
    ic(data)
    return await HandleCustomerRequest(session=session).get_customer_by_shop_id(data=data)

@router.get('/by/id/{shop_id}/{id}')
async def get_customer_by_id(session:PG_ASYNC_SESSION,data:GetCustomerByIdSchema=Depends()):
    return await HandleCustomerRequest(session=session).get_customer_by_id(data=data)

@router.get('')
async def get_customers(session:PG_ASYNC_SESSION,data:GetAllCustomerSchema=Depends()):
    return await HandleCustomerRequest(session=session).get_customers(data=data)


@router.get('/cleared-histories/by/shop/{shop_id}')
async def get_clr_hist_by_shop_id(session:PG_ASYNC_SESSION,data:GetCustomerOutstClearedByShopIdSchema=Depends()):
    ic(data)
    return await HandleCustomerRequest(session=session).get_outst_clr_by_shop_id(data=data)

@router.get('/cleared-histories/by/id/{shop_id}/{id}')
async def get_clr_hist_by_id(session:PG_ASYNC_SESSION,data:GetCustomerOutstClearedByIdSchema=Depends()):
    return await HandleCustomerRequest(session=session).get_outst_clr_by_id(data=data)

@router.get('/cleared-histories')
async def get_clr_hist(session:PG_ASYNC_SESSION,data:GetAllCustomerOutstClearedSchema=Depends()):
    return await HandleCustomerRequest(session=session).get_outst_clr(data=data)





