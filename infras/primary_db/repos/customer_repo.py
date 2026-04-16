from models.repo_models.base_repo_model import BaseRepoModel
from ..models.customer_model import Customers,String
from ..main import AsyncSession
from sqlalchemy import select,update,delete,or_,and_,func
from schemas.v1.db_schema.customer_schema import CreateCustomerDbSchema,UpdateCustomerDbSchema
from typing import Optional
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from core.decorators.error_handler_dec import catch_errors
from typing import Optional,List



class CustomerRepo(BaseRepoModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.customer_cols=(
            Customers.id,
            Customers.shop_id,
            Customers.datas
        )



    @start_db_transaction
    async def create(self,data:CreateCustomerDbSchema)->bool:
        self.session.add(Customers(**data.model_dump(mode="json")))
        await self.session.commit()
        return True
    
    @start_db_transaction
    async def create_bulk(self,datas:List[Customers]):
        self.session.add_all(datas)
        return True
    

    @start_db_transaction
    async def update(self,data:UpdateCustomerDbSchema)->str|None:
        customer_toupdate=update(
            Customers
        ).where(
            and_(
                Customers.id==data.id,
                Customers.shop_id==data.shop_id
            )
        ).values(
            datas=data.datas
        ).returning(Customers.id)

        is_updated=(await self.session.execute(customer_toupdate)).scalar_one_or_none()
        return is_updated
    
    @start_db_transaction
    async def delete(self, customer_id:str,shop_id:str)->str|None:
        customer_todel=delete(
            Customers
        ).where(Customers.id==customer_id,Customers.shop_id==shop_id).returning(Customers.id)

        is_deleted=(await self.session.execute(customer_todel)).scalar_one_or_none()

        return is_deleted
    

    async def get(self,timezone:TimeZoneEnum,query:str,limit:int,offset:int):
        search_term=f"%{query}%"
        created_at=func.date(func.timezone(timezone.value,Customers.created_at))
        customer_stmt=(
            select(
                *self.customer_cols,
                created_at
            )
            .where(
                or_(
                    Customers.id.ilike(search_term),
                    Customers.shop_id.ilike(search_term),
                    func.cast(created_at,String).ilike(search_term)
                )
            ).offset(offset=offset).limit(limit=limit)
            .order_by(created_at)
        )

        customers=(await self.session.execute(customer_stmt)).mappings().all()

        return customers

    async def check_bulk(self,data:list):
        check_stmt=(
            select(
                Customers.id
            )
            .where(
                Customers.id.in_(data)
            )
        )

        result = (await self.session.execute(check_stmt)).scalars().all()

        return result
    

    async def getby_id(self,timezone:TimeZoneEnum,customer_id:str,shop_id:str):
        created_at=func.date(func.timezone(timezone.value,Customers.created_at))
        customer_stmt=(
            select(
                *self.customer_cols,
                created_at
            )
            .where(
                Customers.id==customer_id,
                Customers.shop_id==shop_id
            )
        )

        customer=(await self.session.execute(customer_stmt)).mappings().one_or_none()

        return customer
    
    async def search(self, query:str, limit:int):
        search_term=f"%{query}%"
        customer_stmt=(
            select(
                *self.customer_cols
            )
            .where(
                or_(
                    Customers.id.ilike(search_term),
                    Customers.shop_id.ilike(search_term)
                )
            ).limit(limit=limit)
        )

        customer_stmt=(await self.session.execute(customer_stmt)).mappings().all()

        return customer_stmt
