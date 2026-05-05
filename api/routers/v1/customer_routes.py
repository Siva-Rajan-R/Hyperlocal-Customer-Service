from fastapi import APIRouter,HTTPException,Query,Depends
from schemas.v1.request_schemas.customer_schema import CreateCustomerSchema,UpdateCustomerSchema,DeleteCustomerSchema,GetAllCustomerSchema,GetCustomerByIdSchema,GetCustomerByShopIdSchema
from typing import Annotated,Optional
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
SHOP_ID="37d5519b-51a1-5854-982b-4d6524171017"

# Write methods
@router.post('')
async def create(data:CreateCustomerSchema,session:PG_ASYNC_SESSION):
    return await HandleCustomerRequest(session=session).create(data=data)

@router.put('')
async def update(data:UpdateCustomerSchema,session:PG_ASYNC_SESSION):
    return await HandleCustomerRequest(session=session).update(data=data)

@router.delete('/{shop_id}/{id}')
async def delete(session:PG_ASYNC_SESSION,data:DeleteCustomerSchema=Depends()):
    return await HandleCustomerRequest(session=session).delete(data=data)


# Read methods
@router.get('/by/shop/{shop_id}')
async def getby_shop(session:PG_ASYNC_SESSION,data:GetCustomerByShopIdSchema=Depends()):
    ic(data)
    return await HandleCustomerRequest(session=session).getby_shop_id(data=data)

@router.get('/by/{shop_id}/{id}')
async def getby_id(session:PG_ASYNC_SESSION,data:GetCustomerByIdSchema=Depends()):
    return await HandleCustomerRequest(session=session).getby_id(data=data)

@router.get('')
async def get(session:PG_ASYNC_SESSION,data:GetAllCustomerSchema=Depends()):
    return await HandleCustomerRequest(session=session).get(data=data)



