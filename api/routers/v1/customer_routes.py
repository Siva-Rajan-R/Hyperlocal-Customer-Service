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


# --- Export Routes ---
from schemas.v1.export_schemas import ExportDataRequestSchema
from arq import create_pool
from arq.connections import RedisSettings
import json, os, uuid
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict, BaseResponseTypDict
import redis.asyncio as aioredis

REDIS_URL = os.getenv("PLATFORM_REDIS_URL") or "redis://localhost:6379"

@router.post('/export')
async def export_customers(data: ExportDataRequestSchema):
    job_id = str(uuid.uuid4())
    payload = data.model_dump()
    payload["job_id"] = job_id
    
    redis = await create_pool(RedisSettings.from_dsn(REDIS_URL))
    await redis.enqueue_job("export_customers_task", payload, _job_id=job_id, _queue_name="customer_export_queue")
    await redis.close()

    
    # Store initial state in Redis
    redis_client = aioredis.Redis.from_url(REDIS_URL, decode_responses=True)
    await redis_client.set(
        f"EXPORT_JOB:{job_id}",
        json.dumps({
            "job_id": job_id,
            "entity": "CUSTOMER",
            "status": "QUEUED",
            "params": payload
        }),
        ex=86400
    )
    await redis_client.aclose()
    
    return SuccessResponseTypDict(
        detail=BaseResponseTypDict(
            msg="Customer export job scheduled successfully in the background",
            status_code=202,
            success=True
        ),
        data={
            "job_id": job_id,
            "entity": "CUSTOMER",
            "status": "QUEUED"
        }
    )

@router.get('/export/status/{job_id}')
async def get_customer_export_status(job_id: str):
    redis_client = aioredis.Redis.from_url(REDIS_URL, decode_responses=True)
    raw = await redis_client.get(f"EXPORT_JOB:{job_id}")
    await redis_client.aclose()
    
    if not raw:
        raise HTTPException(status_code=404, detail="Export job not found")
        
    return SuccessResponseTypDict(
        detail=BaseResponseTypDict(
            msg="Export status fetched successfully",
            status_code=200,
            success=True
        ),
        data=json.loads(raw)
    )






