from fastapi import FastAPI
from api.routers.v1 import customer_routes,customfield_router
from infras.primary_db.main import init_pg_db
from contextlib import asynccontextmanager
from icecream import ic
from dotenv import load_dotenv
import os,asyncio
from core.configs.settings_config import SETTINGS
from hyperlocal_platform.core.enums.environment_enum import EnvironmentEnum
from messaging.worker import worker
from infras.read_db.repos.customer_repo import CustomerStatsRepo
from infras.read_db.main import init_read_db,close_read_db

load_dotenv()


@asynccontextmanager
async def customer_service_lifespan(app:FastAPI):
    try:
        ic("Starting customer service...")
        await init_pg_db()
        await init_read_db()
        # await CustomerStatsRepo.init_stats()
        asyncio.create_task(worker())
        yield

    except Exception as e:
        ic(f"Error : Starting Customer service => {e}")

    finally:
        ic("...Stoping Customer Servcie...")

debug=False
openapi_url=None
docs_url=None
redoc_url=None

if SETTINGS.ENVIRONMENT.value==EnvironmentEnum.DEVELOPMENT.value:
    debug=True
    openapi_url="/openapi.json"
    docs_url="/docs"
    redoc_url="/redoc"

app=FastAPI(
    title="Customer Service",
    description="This service contains all the CRUD operations for customer service",
    debug=debug,
    openapi_url=openapi_url,
    docs_url=docs_url,
    redoc_url=redoc_url,
    lifespan=customer_service_lifespan
)



# Routes to include
app.include_router(customer_routes.router)
app.include_router(customfield_router.router)
