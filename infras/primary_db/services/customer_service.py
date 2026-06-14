from ..main import AsyncSession
from ..repos.customer_repo import CustomerRepo
from schemas.v1.db_schemas.customer_schema import CreateCustomerDbSchema,UpdateCustomerDbSchema,CreditHistoryCustomerDbSchema,OutstandingClearedCustomerDbSchema
from schemas.v1.request_schemas.customer_schema import CreateCustomerSchema,UpdateCustomerSchema,DeleteCustomerSchema,GetAllCustomerSchema,GetCustomerByIdSchema,GetCustomerByShopIdSchema,VerifyCustomerSchema,DeductCustomerCreditSchema,GetCustomerCreditHistories,OutstandingClearedCustomerSchema,DeductCustomerOutstandingSchema,GetCustomerOutstandingCleared
from models.service_models.base_service_model import BaseServiceModel
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from core.decorators.error_handler_dec import catch_errors
from core.data_formats.enums.customer_enums import CustomerCreditHistoryEnums
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from typing import Optional,List
from ..models.customer_model import Customers
from icecream import ic
import httpx

ACTIVITY_LOG_URL = "http://127.0.0.1:8001/activity-logs"

async def _send_activity_log(shop_id: str, action: str, entity_id: str, description: str, changes: list = None):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(ACTIVITY_LOG_URL, json={
                "shop_id": shop_id,
                "user_name": "siva",
                "service": "Customer",
                "action": action,
                "entity_type": "Customer",
                "entity_id": entity_id,
                "description": description,
                "changes": changes or []
            })
    except Exception as e:
        ic(f"Failed to log activity: {e}")



class CustomerService(BaseServiceModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.customer_repo_obj=CustomerRepo(session=session)

    async def create(self,data:CreateCustomerSchema) -> dict | None:
        
        customer_id:str=generate_uuid()
        shop_id = data.shop_id
        customer_name = data.name if hasattr(data, 'name') else 'Unknown'
        
        from infras.read_db.repos.shopidconfig_repo import ShopIdConfigReadDbRepo
        from core.utils.id_formatter import format_ui_id
        
        shop_config = await ShopIdConfigReadDbRepo.get_config(shop_id)
        cus_config = shop_config.get("customer", {})
        prefix = cus_config.get("prefix", "CUS")
        start_from = cus_config.get("start_from", 1)
        
        raw_sequence = await self.customer_repo_obj.get_next_sequence(shop_id, start_from)
        ui_id_str = format_ui_id(prefix, start_from, raw_sequence)

        data_toadd=CreateCustomerDbSchema(
            **data.model_dump(mode='json',exclude_none=True,exclude_unset=True),
            id=customer_id,
            ui_id=ui_id_str,
            outstanding=0
        )

        customer_res=await self.customer_repo_obj.create(data=data_toadd)
        if customer_res:
            customer_res = dict(customer_res)
            await _send_activity_log(
                shop_id=shop_id,
                action="CREATE",
                entity_id=customer_id,
                description=f"Created new customer: {customer_name}",
                changes=[{"field": "name", "before": "", "after": str(customer_name)}]
            )
        return customer_res
    

    async def create_outstanding_cleared(self,data:OutstandingClearedCustomerSchema) -> dict | None:
        out_ded_res=await self.customer_repo_obj.deduct_outstanding(data=DeductCustomerOutstandingSchema(id=data.customer_id,shop_id=data.shop_id,amount=data.cleared_amount))
        ic(out_ded_res)
        if not out_ded_res:
            return False
        
        data_toadd=OutstandingClearedCustomerDbSchema(
            **data.model_dump(mode='json',exclude_none=True,exclude_unset=True),
            outstanding_before=out_ded_res['outstanding']+data.cleared_amount,
            outstanding_after=out_ded_res['outstanding']
        )

        customer_res=await self.customer_repo_obj.create_outstanding_cleared(data=data_toadd)
        return customer_res
    
    async def add_outstanding(self,data:DeductCustomerOutstandingSchema) -> dict | None:
        out_add_res=await self.customer_repo_obj.add_outstanding(data=data)
        ic(out_add_res)
        return out_add_res
    

    async def update(self,data:UpdateCustomerSchema) -> dict | None:
        previous_credit=(await self.getby_id(data=GetCustomerByIdSchema(id=data.id,shop_id=data.shop_id)))
        ic(previous_credit)
        if not previous_credit:
            return False
        
        data_toupdate=UpdateCustomerDbSchema(
            **data.model_dump(mode='json',exclude_none=True,exclude_unset=True)
        )
        customer_res=await self.customer_repo_obj.update(data=data_toupdate)
        ic(customer_res)
        if customer_res:
            customer_res = (await _format_ui_id_for_customers(data.shop_id, [customer_res]))[0]
            if data.credit_limit and data.credit_limit!=previous_credit['credit_limit'] and previous_credit['is_active']==True:
                customer_credit_res=await self.customer_repo_obj.create_credit_history(
                    data=CreditHistoryCustomerDbSchema(
                        shop_id=data.shop_id,
                        customer_id=data.id,
                        credit_before=previous_credit['credit_limit'],
                        credit_after=customer_res['credit_limit'],
                        type=CustomerCreditHistoryEnums.UPDATED
                        
                    )
                )

                ic(customer_credit_res)

            if previous_credit:
                changes_list = []
                desc_changes = []
                for k, v in data_toupdate.model_dump(exclude_none=True, exclude_unset=True).items():
                    if k not in ["id", "shop_id"] and k in previous_credit and str(previous_credit[k]) != str(v):
                        desc_changes.append(f"{k} prv({previous_credit[k]}) after ({v})")
                        changes_list.append({
                            "field": k,
                            "before": str(previous_credit[k]),
                            "after": str(v)
                        })
                
                if desc_changes:
                    desc = f"updated customer {', '.join(desc_changes)}"
                    await _send_activity_log(
                        shop_id=data.shop_id,
                        action="UPDATE",
                        entity_id=data.id,
                        description=desc,
                        changes=changes_list
                    )

        return customer_res
    

    async def deduct_credit(self,data:DeductCustomerCreditSchema):
        previous_credit=(await self.getby_id(data=GetCustomerByIdSchema(id=data.id,shop_id=data.shop_id)))
        ic(previous_credit)
        if not previous_credit:
            return False
        customer_res=await self.customer_repo_obj.deduct_credit(data=data)
        ic(customer_res)
        if customer_res and previous_credit['is_active']==True:
            customer_credit_res=await self.customer_repo_obj.create_credit_history(
                data=CreditHistoryCustomerDbSchema(
                    id=generate_uuid(),
                    shop_id=data.shop_id,
                    customer_id=data.id,
                    credit_before=previous_credit['credit_limit'],
                    credit_after=customer_res['credit_limit'],
                    type=CustomerCreditHistoryEnums.SALES
                    
                )
            )

            ic(customer_credit_res)
        return customer_res
    


    async def delete(self,data:DeleteCustomerSchema) -> dict | None:
        old_customer = await self.getby_id(data=GetCustomerByIdSchema(id=data.id, shop_id=data.shop_id))
        res=await self.customer_repo_obj.delete(data=data)
        if res:
            res = (await _format_ui_id_for_customers(data.shop_id, [res]))[0]
            customer_name = old_customer.get('name', 'Unknown') if old_customer else 'Unknown'
            await _send_activity_log(
                shop_id=data.shop_id,
                action="DELETE",
                entity_id=data.id,
                description=f"Deleted customer: {customer_name}",
                changes=[{"field": "name", "before": str(customer_name), "after": "DELETED"}]
            )
        return res


    async def get(self,data:GetAllCustomerSchema) -> dict:
        res=await self.customer_repo_obj.get(data=data)
        res = await _format_ui_id_for_customers(data.shop_id, res)
        if data.offset == 1:
            overall_values = await self.customer_repo_obj.get_overall_values(data=data)
            return {
                "overall_datas": overall_values,
                "datas": res
            }
        return {"datas": res}
    
    async def get_outstanding_cleared(self,data:GetCustomerOutstandingCleared) -> List[dict] | list:
        res=await self.customer_repo_obj.get_outstanding_cleared(data=data)
        return res

    async def get_customer_credit_histories(self,data:GetCustomerCreditHistories):
        res=await self.customer_repo_obj.get_customer_credit_histories(data=data)
        return res

    async def getby_id(self,data:GetCustomerByIdSchema) -> dict | None:
        res=await self.customer_repo_obj.getby_id(data=data)
        if res:
            res = dict(res)
        return res
    
    async def getby_shop_id(self,data:GetCustomerByShopIdSchema) -> dict:
        res=await self.customer_repo_obj.getby_shop_id(data=data)
        if data.offset == 1:
            overall_values = await self.customer_repo_obj.get_overall_values(data=data)
            return {
                "overall_datas": overall_values,
                "datas": res
            }
        return {"datas": res}
    
    async def verify(self,data:VerifyCustomerSchema) -> dict:
        res=await self.customer_repo_obj.verify(data=data)
        return res
    




    async def search(self, query:str, limit:Optional[int]=5):
        res=await self.customer_repo_obj.search(query=query,limit=limit)
        return res
    
    async def check_bulk(self,datas:list):
        return await self.customer_repo_obj.check_bulk(data=datas)

    async def create_bulk(self,datas:List[CreateCustomerSchema]):
        datas_toadd=[]
        for data in datas:
            datas_toadd.append(
                Customers(id=generate_uuid(),**data.model_dump(mode='json'))
            )

        return await self.customer_repo_obj.create_bulk(datas=datas_toadd)