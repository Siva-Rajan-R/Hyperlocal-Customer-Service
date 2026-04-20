from fastapi import APIRouter,HTTPException,Query,Depends
from infras.primary_db.services.customer_service import CustomerService,CreateCustomerSchema,UpdateCustomerSchema,Optional
from typing import Annotated
from infras.primary_db.main import get_pg_async_session,AsyncSession
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from core.utils.validate_fields import validate_fields
from ...handlers.customer_handler import HandleCustomerRequest
print(TimeZoneEnum)

router=APIRouter(
    tags=['Customer CRUD'],
    prefix='/customers'
)

PG_ASYNC_SESSION=Annotated[AsyncSession,Depends(get_pg_async_session)]
SHOP_ID="string"

# Write methods
@router.post('')
async def create(data:CreateCustomerSchema,session:PG_ASYNC_SESSION):
    return await HandleCustomerRequest(session=session).create(data=data)

@router.put('')
async def update(data:UpdateCustomerSchema,session:PG_ASYNC_SESSION):
    return await HandleCustomerRequest(session=session).update(data=data)

@router.delete('/{customer_id}')
async def delete(customer_id:str,session:PG_ASYNC_SESSION):
    return await HandleCustomerRequest(session=session).delete(customer_id=customer_id,shop_id=SHOP_ID)


# Read methods
@router.get('/search')
async def search(session:PG_ASYNC_SESSION,q:str=Query(...),limit:Optional[int]=Query(5)):
    return await HandleCustomerRequest(session=session).search(query=q,limit=limit)

@router.get('/by/{customer_id}')
async def get(session:PG_ASYNC_SESSION,customer_id:str,timezone:Optional[TimeZoneEnum]=Query(TimeZoneEnum.Asia_Kolkata)):
    return await HandleCustomerRequest(session=session).getby_id(customer_id=customer_id,shop_id=SHOP_ID,timezone=timezone)

@router.get('')
async def get(session:PG_ASYNC_SESSION,timezone:Optional[TimeZoneEnum]=Query(TimeZoneEnum.Asia_Kolkata),q:Optional[str]=Query(''),limit:Optional[int]=Query(10),offset:int=Query(1)):
    return await HandleCustomerRequest(session=session).get(
        query=q,
        limit=limit,
        offset=offset,
        timezone=timezone
    )


