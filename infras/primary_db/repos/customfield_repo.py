from sqlalchemy import select, update, delete,or_,and_,bindparam
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from icecream import ic
from sqlalchemy.dialects.postgresql import insert
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from ..models.customfield_model import CustomerCustomFields, CustomerCustomFieldsValues
from schemas.v1.db_schemas.customfield_schema import CreateCustomFieldDbSchema, CreateCustomFieldValueDbSchema,UpdateCustomFieldDbSchema,DeleteCustomFieldDbSchema
from schemas.v1.request_schemas.customfield_schema import GetFieldById,GetFieldByShopIdSchema,GetFieldByName,GetValueByIdName,GetvaluesByCustomerId

class CustomFieldsRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Custom Fields (Definitions) ---
    
    async def create_all_field(self, data: List[CreateCustomFieldDbSchema]) -> bool:
        field_toadd=[CustomerCustomFields(**field.model_dump()) for field in data]
        self.session.add_all(field_toadd)
        await self.session.commit()
        return True
    

    async def update_field(self, data:UpdateCustomFieldDbSchema) -> Optional[str]:
        stmt = (
            update(CustomerCustomFields)
            .where(CustomerCustomFields.id == data.id, CustomerCustomFields.shop_id == data.shop_id)
            .values(**data.model_dump(exclude=['field_id','shop_id'],exclude_none=True,exclude_unset=True))
            .returning(CustomerCustomFields.id)
        )
        res = (await self.session.execute(stmt)).scalar_one_or_none()
        await self.session.commit()
        return res

    async def delete_field(self,data:DeleteCustomFieldDbSchema) -> bool:
        stmt = delete(CustomerCustomFields).where(CustomerCustomFields.id == (data.id if hasattr(data, "id") and data.id else getattr(data, "field_id", None)), CustomerCustomFields.shop_id == data.shop_id)
        res = await self.session.execute(stmt)
        await self.session.commit()
        return res.rowcount > 0


    async def get_field_by_id(self,data:GetFieldById) -> Optional[dict]:
        stmt = select(CustomerCustomFields).where(
            CustomerCustomFields.id == data.id, 
            CustomerCustomFields.shop_id == data.shop_id
        )
        res = (await self.session.execute(stmt)).scalars().first()
        if res:
            return {c.name: getattr(res, c.name) for c in res.__table__.columns}
        return None
    

    async def get_bulk_fields(self,shop_id: str,ids: List[str]=[],names:List[str]=[]) -> Optional[dict]:
        if not ids and not names:
            return []
        
        stmt = select(CustomerCustomFields).where(
            or_(CustomerCustomFields.id.in_(ids),CustomerCustomFields.field_name.in_(names)), 
            CustomerCustomFields.shop_id == shop_id
        )
        res = (await self.session.execute(stmt)).mappings().all()
        if res:
            return [{c.name: getattr(row, c.name) for c in row.__table__.columns} for row in res]
        return []
    

    async def get_field_by_name(self, data:GetFieldByName) -> Optional[dict]:
        stmt = select(CustomerCustomFields).where(
            CustomerCustomFields.field_name == data.name, 
            CustomerCustomFields.shop_id == data.shop_id
        )
        res = (await self.session.execute(stmt)).scalars().first()
        if res:
            return {c.name: getattr(res, c.name) for c in res.__table__.columns}
        return None

    async def get_fields_by_shop_id(self, data:GetFieldByShopIdSchema) -> List[dict]:
        stmt = select(CustomerCustomFields).where(CustomerCustomFields.shop_id == data.shop_id)
        res = (await self.session.execute(stmt)).scalars().all()
        
        field_ids = [row.id for row in res]
        valued_field_ids = set()
        if field_ids:
            val_stmt = select(CustomerCustomFieldsValues.field_id).where(
                CustomerCustomFieldsValues.field_id.in_(field_ids),
                CustomerCustomFieldsValues.shop_id == data.shop_id,
                CustomerCustomFieldsValues.value.isnot(None),
                CustomerCustomFieldsValues.value != ""
            ).distinct()
            val_res = (await self.session.execute(val_stmt)).scalars().all()
            valued_field_ids = set(val_res)
            
        result = []
        for row in res:
            d = {c.name: getattr(row, c.name) for c in row.__table__.columns}
            d["has_values"] = row.id in valued_field_ids
            result.append(d)
        return result
    

    async def get_fields(self) -> List[dict]:
        stmt = select(CustomerCustomFields)
        res = (await self.session.execute(stmt)).scalars().all()
        return [{c.name: getattr(row, c.name) for c in row.__table__.columns} for row in res]


    async def upsert_field_value(self, data: List[CreateCustomFieldValueDbSchema]) -> bool:
        if not data:
            return True

        # 1. Convert the pydantic schemas to a list of raw dictionaries
        insert_mappings = [d.model_dump() for d in data]

        # 2. Build the native PostgreSQL INSERT statement
        stmt = insert(CustomerCustomFieldsValues)
        
        # 3. Construct the UPSERT (ON CONFLICT) logic
        # Resolves on the unique combination of customer and field
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["customer_id", "field_id"],  
            set_={
                "value": stmt.excluded.value,   # Update the actual text/data value
                "shop_id": stmt.excluded.shop_id  # Keeps the shop relation intact/valid
            }
        )

        # 4. Execute the batch operation efficiently in one database round-trip
        res = await self.session.execute(upsert_stmt, insert_mappings)
        
        ic("Total rows handled (Inserted + Updated) => ", res.rowcount)
        return True

        
    async def get_values_by_customer_id(self, data:GetvaluesByCustomerId) -> List[dict]:
        stmt = select(CustomerCustomFieldsValues).where(
            CustomerCustomFieldsValues.customer_id == data.id,
            CustomerCustomFieldsValues.shop_id == data.shop_id
        )
        res = (await self.session.execute(stmt)).scalars().all()
        return [{c.name: getattr(row, c.name) for c in row.__table__.columns} for row in res]

    async def get_values(self):
        stmt = select(CustomerCustomFieldsValues)
        res = (await self.session.execute(stmt)).scalars().all()
        return [{c.name: getattr(row, c.name) for c in row.__table__.columns} for row in res]
    
    async def get_values_by_id(self,id:str,shop_id:str):
        stmt = select(CustomerCustomFieldsValues).where(
            CustomerCustomFieldsValues.id == id,
            CustomerCustomFieldsValues.shop_id == shop_id
        )
        res = (await self.session.execute(stmt)).mappings().all()
        return [{c.name: getattr(row, c.name) for c in row.__table__.columns} for row in res]


    async def get_values_by_field_id(self, field_id: str, shop_id: str) -> List[dict]:
        stmt = select(CustomerCustomFieldsValues).where(
            CustomerCustomFieldsValues.field_id == field_id,
            CustomerCustomFieldsValues.shop_id == shop_id
        )
        res = (await self.session.execute(stmt)).scalars().all()
        return [{c.name: getattr(row, c.name) for c in row.__table__.columns} for row in res]
