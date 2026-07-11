from models.repo_models.base_repo_model import BaseRepoModel
from ..models.customer_model import Customers,String,CustomerOutstandingClearedHistories
from ..main import AsyncSession
from sqlalchemy import select,update,delete,or_,and_,func,case,text
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime, timezone
from schemas.v1.customer_schemas.db_schemas import CreateCustomerDbSchema,UpdateCustomerDbSchema,DeleteCustomerDbSchema,CreateCustomerOutstandingDbSchema,CreateCustomerOutstandingClearedDbSchema
from schemas.v1.customer_schemas.request_schemas import GetAllCustomerSchema,GetCustomerByIdSchema,GetCustomerByShopIdSchema,GetAllCustomerOutstClearedSchema,GetCustomerOutstClearedByIdSchema,GetCustomerOutstClearedByShopIdSchema
from typing import Optional
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from core.decorators.error_handler_dec import catch_errors
from typing import Optional,List
from icecream import ic



class CustomerRepo:
    def __init__(self, session:AsyncSession):
        self.session=session
        self.customer_cols=(
            Customers.id,
            Customers.ui_id,
            Customers.shop_id,
            Customers.sequence_id,
            Customers.name,
            Customers.contact_infos,
            Customers.location_infos,
            Customers.credit_infos,
            Customers.outstanding_infos,
            Customers.can_have_credit,
            Customers.additional_infos,
            Customers.created_at,
            Customers.updated_at,
        )
        self.customer_cleared_his_cols=(
            CustomerOutstandingClearedHistories.id,
            CustomerOutstandingClearedHistories.shop_id,
            CustomerOutstandingClearedHistories.additional_infos,
            CustomerOutstandingClearedHistories.cleared_infos,
            CustomerOutstandingClearedHistories.payment_infos,
            CustomerOutstandingClearedHistories.customer_id,
            CustomerOutstandingClearedHistories.updated_at,
            CustomerOutstandingClearedHistories.created_at
        )



    @start_db_transaction
    async def get_next_sequence(self, shop_id: str, start_from: int) -> int:
        seq_name = f"seq_customer_{shop_id.replace('-', '_').lower()}"
        await self.session.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {seq_name} START WITH {start_from}"))
        res = await self.session.execute(text(f"SELECT nextval('{seq_name}')"))
        return res.scalar_one()

    @start_db_transaction
    async def create(self,data:CreateCustomerDbSchema)->dict | None:
        stmt=(
            insert(
                Customers
            )
            .values(
                **data.model_dump(mode="json")
            )
            .returning(*self.customer_cols)
        )
        res=(await self.session.execute(stmt)).mappings().one_or_none()
        return res
    

    @start_db_transaction
    async def update(self,data:UpdateCustomerDbSchema)->dict|None:
        stmt=update(
            Customers
        ).where(
            and_(
                Customers.id==data.id,
                Customers.shop_id==data.shop_id
            )
        ).values(
            credit_infos=data.credit_infos.model_dump(mode="json"),
            **data.model_dump(mode='json',exclude_none=True,exclude_unset=True,exclude=['id','shop_id','credit_infos'])
        ).returning(*self.customer_cols)

        res=(await self.session.execute(stmt)).mappings().one_or_none()
        return res
    

    @start_db_transaction
    async def delete(self, data:DeleteCustomerDbSchema)->dict|None:
        stmt=delete(
            Customers
        ).where(Customers.id==data.id,Customers.shop_id==data.shop_id).returning(*self.customer_cols)

        res=(await self.session.execute(stmt)).mappings().one_or_none()

        return res
    

    @start_db_transaction
    async def add_outstanding(self,data:CreateCustomerOutstandingDbSchema):
        stmt=(
            update(
                Customers
            )
            .where(
                Customers.id==data.id,
                Customers.shop_id==data.shop_id
            )
            .values(
                outstanding_infos=data.outstanding_infos.model_dump()
            )
        ).returning(*self.customer_cols)

        res=(await self.session.execute(stmt)).mappings().one_or_none()

        return res
    

    @start_db_transaction
    async def clear_outstanding(self,data:CreateCustomerOutstandingClearedDbSchema):
        stmt=(
            insert(
                CustomerOutstandingClearedHistories
            )
            .values(
                **data.model_dump(mode="json")
            )
            .returning(
                *self.customer_cleared_his_cols
            )
        )

        res=(await self.session.execute(stmt)).mappings().one_or_none()
        return res

    

    async def get(self,data:GetAllCustomerSchema) -> List[dict] | list:
        search_term=f"%{data.query}%"
        cursor=(data.offset-1)*data.limit
        stmt=(
            select(
                *self.customer_cols
            )
            .offset(offset=cursor).limit(limit=data.limit)
        )

        res=(await self.session.execute(stmt)).mappings().all()

        return res
    

    async def getby_shop_id(self,data:GetCustomerByShopIdSchema) -> List[dict] | list:
        search_term=f"%{data.query}%"
        cursor=(data.offset-1)*data.limit
        stmt=(
            select(
                *self.customer_cols
            )
            .where(
                Customers.shop_id==data.shop_id
            )
            .offset(offset=cursor).limit(limit=data.limit)
        )

        res=(await self.session.execute(stmt)).mappings().all()

        return res
    
    async def getby_id(self,data:GetCustomerByIdSchema) -> List[dict] | list:
        stmt=(
            select(
                *self.customer_cols
            )
            .where(
                Customers.shop_id==data.shop_id,
                Customers.id==data.id
            )
        )

        res=(await self.session.execute(stmt)).mappings().one_or_none()

        return res
    

    async def get_outst_cleared(self,data:GetAllCustomerOutstClearedSchema):
        search_term=f"%{data.query}%"
        cursor=(data.offset-1)*data.limit
        stmt=(
            select(
                *self.customer_cleared_his_cols
            )
            .offset(offset=cursor).limit(limit=data.limit)
        )

        res=(await self.session.execute(stmt)).mappings().all()

        return res
    

    async def get_outst_cleared_by_shop_id(self,data:GetCustomerOutstClearedByShopIdSchema):
        search_term=f"%{data.query}%"
        cursor=(data.offset-1)*data.limit
        stmt=(
            select(
                *self.customer_cleared_his_cols
            )
            .where(
                CustomerOutstandingClearedHistories.shop_id==data.shop_id
            )
            .offset(offset=cursor).limit(limit=data.limit)
        )

        res=(await self.session.execute(stmt)).mappings().all()

        return res
    

    async def get_outst_cleared_by_id(self,data:GetCustomerOutstClearedByIdSchema):
        stmt=(
            select(
                *self.customer_cleared_his_cols
            )
            .where(
                CustomerOutstandingClearedHistories.shop_id==data.shop_id,
                CustomerOutstandingClearedHistories.customer_id==data.id
            )
        )

        res=(await self.session.execute(stmt)).mappings().all()

        return res

    