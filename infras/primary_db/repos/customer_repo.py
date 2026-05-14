from models.repo_models.base_repo_model import BaseRepoModel
from ..models.customer_model import Customers,String,CustomerCreditHistories,CustomerOutstandingClearedHistories
from ..main import AsyncSession
from sqlalchemy import select,update,delete,or_,and_,func
from sqlalchemy.dialects.postgresql import insert
from schemas.v1.db_schemas.customer_schema import CreateCustomerDbSchema,UpdateCustomerDbSchema,CreditHistoryCustomerDbSchema,OutstandingClearedCustomerDbSchema
from schemas.v1.request_schemas.customer_schema import DeleteCustomerSchema,UpdateCustomerSchema,GetAllCustomerSchema,GetCustomerByIdSchema,GetCustomerByShopIdSchema,VerifyCustomerSchema,DeductCustomerCreditSchema,GetCustomerCreditHistories,DeductCustomerOutstandingSchema,GetCustomerOutstandingCleared
from typing import Optional
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from core.decorators.error_handler_dec import catch_errors
from typing import Optional,List
from icecream import ic



class CustomerRepo(BaseRepoModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.customer_cols=(
            Customers.id,
            Customers.ui_id,
            Customers.shop_id,
            Customers.sequence_id,
            Customers.name,
            Customers.email,
            Customers.mobile_number,
            Customers.is_active,
            Customers.credit_limit,
            Customers.outstanding,
            Customers.created_at,
            Customers.updated_at,
            Customers.datas
        )



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
    async def create_outstanding_cleared(self,data:OutstandingClearedCustomerDbSchema)->dict | None:
        stmt=(
            insert(
                CustomerOutstandingClearedHistories
            )
            .values(
                **data.model_dump(mode="json")
            )
            .returning(
                CustomerOutstandingClearedHistories.id,
                CustomerOutstandingClearedHistories.cleared_amount,
                CustomerOutstandingClearedHistories.outstanding_after,
                CustomerOutstandingClearedHistories.outstanding_before,
                CustomerOutstandingClearedHistories.customer_id,
                CustomerOutstandingClearedHistories.created_at,
                CustomerOutstandingClearedHistories.payments
            )
        )
        res=(await self.session.execute(stmt)).mappings().one_or_none()
        return res
    

    @start_db_transaction
    async def create_credit_history(self,data:CreditHistoryCustomerDbSchema)->dict | None:
        stmt=(
            insert(
                CustomerCreditHistories
            )
            .values(
                **data.model_dump(mode="json")
            )
            .returning(CustomerCreditHistories.id)
        )
        res=(await self.session.execute(stmt)).mappings().one_or_none()
        return res
    
    @start_db_transaction
    async def create_bulk(self,datas:List[Customers]):
        self.session.add_all(datas)
        return True
    

    @start_db_transaction
    async def update(self,data:UpdateCustomerDbSchema)->dict|None:
        customer_toupdate=update(
            Customers
        ).where(
            and_(
                Customers.id==data.id,
                Customers.shop_id==data.shop_id
            )
        ).values(
            **data.model_dump(mode='json',exclude_none=True,exclude_unset=True,exclude=['id','shop_id'])
        ).returning(*self.customer_cols)

        is_updated=(await self.session.execute(customer_toupdate)).mappings().one_or_none()
        return is_updated
    

    @start_db_transaction
    async def deduct_credit(self,data:DeductCustomerCreditSchema)->dict|None:
        customer_toupdate=update(
            Customers
        ).where(
            and_(
                Customers.id==data.id,
                Customers.shop_id==data.shop_id,
                Customers.is_active==True
            )
        ).values(
            credit_limit=Customers.credit_limit-data.amount
        ).returning(*self.customer_cols)

        is_updated=(await self.session.execute(customer_toupdate)).mappings().one_or_none()
        return is_updated
    

    @start_db_transaction
    async def deduct_outstanding(self,data:DeductCustomerOutstandingSchema)->dict|None:
        customer_toupdate=update(
            Customers
        ).where(
            and_(
                Customers.id==data.id,
                Customers.shop_id==data.shop_id,
                Customers.is_active==True
            )
        ).values(
            outstanding=Customers.outstanding-data.amount
        ).returning(*self.customer_cols)

        is_updated=(await self.session.execute(customer_toupdate)).mappings().one_or_none()
        return is_updated
    
    @start_db_transaction
    async def add_outstanding(self,data:DeductCustomerOutstandingSchema)->dict|None:
        customer_toupdate=update(
            Customers
        ).where(
            and_(
                Customers.id==data.id,
                Customers.shop_id==data.shop_id,
                Customers.is_active==True
            )
        ).values(
            outstanding=Customers.outstanding+data.amount
        ).returning(*self.customer_cols)

        

        is_updated=(await self.session.execute(customer_toupdate)).mappings().one_or_none()
        ic(is_updated)
        return is_updated
    
    @start_db_transaction
    async def delete(self, data:DeleteCustomerSchema)->dict|None:
        customer_todel=delete(
            Customers
        ).where(Customers.id==data.id,Customers.shop_id==data.shop_id).returning(*self.customer_cols)

        is_deleted=(await self.session.execute(customer_todel)).mappings().one_or_none()

        return is_deleted
    

    async def get(self,data:GetAllCustomerSchema) -> List[dict] | list:
        search_term=f"%{data.query}%"
        created_at=func.date(func.timezone(data.timezone.value,Customers.created_at))
        cursor=(data.offset-1)*data.limit
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
            ).offset(offset=cursor).limit(limit=data.limit)
            .order_by(created_at)
        )

        customers=(await self.session.execute(customer_stmt)).mappings().all()

        return customers
    

    async def get_customer_credit_histories(self,data:GetCustomerCreditHistories)-> List[dict] | list:
        ic(data)
        customer_hist_stmt=(
            select(
                CustomerCreditHistories.id,
                CustomerCreditHistories.customer_id,
                CustomerCreditHistories.created_at,
                CustomerCreditHistories.type,
                CustomerCreditHistories.credit_after,
                CustomerCreditHistories.credit_before
            )
            .where(
                CustomerCreditHistories.customer_id==data.customer_id,
                CustomerCreditHistories.shop_id==data.shop_id
            )
        )

        res=(await self.session.execute(customer_hist_stmt)).mappings().all()

        return res
    

    async def get_outstanding_cleared(self,data:GetCustomerOutstandingCleared):
        ic(data)
        customer_hist_stmt=(
            select(
                CustomerOutstandingClearedHistories.id,
                CustomerOutstandingClearedHistories.customer_id,
                CustomerOutstandingClearedHistories.created_at,
                CustomerOutstandingClearedHistories.cleared_amount,
                CustomerOutstandingClearedHistories.outstanding_after,
                CustomerOutstandingClearedHistories.outstanding_before,
                CustomerOutstandingClearedHistories.payments
            )
            .where(
                CustomerOutstandingClearedHistories.customer_id==data.customer_id,
                CustomerOutstandingClearedHistories.shop_id==data.shop_id
            )
        )

        res=(await self.session.execute(customer_hist_stmt)).mappings().all()

        return res

    async def getby_shop_id(self,data:GetCustomerByShopIdSchema) -> List[dict] | list:
        ic(data)
        search_term=f"%{data.query}%"
        created_at=func.date(func.timezone(data.timezone.value,Customers.created_at))
        cursor=(data.offset-1)*data.limit
        customer_stmt=(
            select(
                *self.customer_cols,
                created_at
            )
            .where(
                Customers.shop_id==data.shop_id,
                or_(
                    Customers.id.ilike(search_term),
                    Customers.shop_id.ilike(search_term),
                    func.cast(created_at,String).ilike(search_term)
                )
            ).offset(offset=cursor).limit(limit=data.limit)
            .order_by(created_at)
        )

        customers=(await self.session.execute(customer_stmt)).mappings().all()
        ic(customers)
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
    

    async def getby_id(self,data:GetCustomerByIdSchema)-> dict | None:
        created_at=func.date(func.timezone(data.timezone.value,Customers.created_at))
        customer_stmt=(
            select(
                *self.customer_cols,
                created_at
            )
            .where(
                Customers.id==data.id,
                Customers.shop_id==data.shop_id
            )
        )

        customer=(await self.session.execute(customer_stmt)).mappings().one_or_none()

        return customer
    

    async def verify(self,data:VerifyCustomerSchema)-> dict | None:
        stmt=(
            select(
                Customers.id
            )
            .where(
                Customers.shop_id==data.shop_id,
                Customers.id==data.id,
                Customers.shop_id==data.shop_id
            )
        )

        res=(await self.session.execute(stmt)).scalar_one_or_none()
        if res:
            return {'id':res,'exists':True}
        
        return {'id':'','exists':False}
    


    async def search(self, query:str, limit:int):
        search_term=f"%{query}%"
        customer_stmt=(
            select(
                **self.customer_cols
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
