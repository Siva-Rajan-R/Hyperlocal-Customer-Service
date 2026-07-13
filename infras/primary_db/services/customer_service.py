from ..main import AsyncSession
from ..repos.customer_repo import CustomerRepo
from schemas.v1.customer_schemas.request_schemas import CreateCustomerSchema,UpdateCustomerSchema,DeleteCustomerSchema,CreateCustomerOutstandingClearedSchema,CreateCustomerOutstandingSchema,GetAllCustomerOutstClearedSchema,GetAllCustomerSchema,GetCustomerByIdSchema,GetCustomerByShopIdSchema,GetCustomerOutstClearedByIdSchema,GetCustomerOutstClearedByShopIdSchema
from schemas.v1.customer_schemas.db_schemas import CreateCustomerDbSchema,UpdateCustomerDbSchema,DeleteCustomerDbSchema,CreateCustomerOutstandingClearedDbSchema,CreateCustomerOutstandingDbSchema
from schemas.v1.customer_schemas.custom_types import CustomerOutstandingInfosType,CustomerClearedInfosType,CustomerCreditInfosType
from sqlalchemy import select
from models.service_models.base_service_model import BaseServiceModel
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from core.decorators.error_handler_dec import catch_errors
from core.data_formats.enums.customer_enums import CustomerCreditHistoryEnums,CustomerOutstandingAddEnums,StatsUpdateType
from ...read_db.repos.customer_repo import CustomerStatsRepo
from ...read_db.models.customer_model import CustomerStatsSchema
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from typing import Optional,List
from ..models.customer_model import Customers
from ..services.customfield_service import CustomFieldsService,CreateCustomFieldValueSchema
from icecream import ic
import httpx
from integrations.utility_service import get_ui_id, get_shop_category, get_shop_unit





class CustomerService:
    def __init__(self, session:AsyncSession):
        self.session=session
        self.customer_repo_obj=CustomerRepo(session=session)
        self.customer_stats_repo_obj=CustomerStatsRepo

    # Writables
    async def create(self,data:CreateCustomerSchema) -> dict | None:
        customer_id:str=generate_uuid()
        ui_id_res = await get_ui_id(shop_id=data.shop_id)
        if isinstance(ui_id_res, dict) and "prefix" in ui_id_res:
            ui_id = f"{ui_id_res.get('prefix')}-{ui_id_res.get('current_number')}"
        else:
            return False
        final_data=CreateCustomerDbSchema(id=customer_id,ui_id=ui_id,**data.model_dump())
        res=await self.customer_repo_obj.create(data=final_data)
        ic(res)

        cust_obj=await CustomFieldsService(session=self.session).upsert_values(
            data=CreateCustomFieldValueSchema(
                shop_id=data.shop_id,
                customer_id=customer_id,
                value_infos=[
                    {'field_id':id,"value":value}
                    for id,value in data.custom_fields.items()
                ]
            )
        )
        ic(cust_obj)
        if res:
            total_credits=data.credit_infos.limit if data.can_have_credit else 0
            total_customers=1
            total_customer_with_credit=1 if data.can_have_credit else 0
            total_outstanding=0

            ic(total_customer_with_credit,total_credits,total_outstanding,total_customers)
            stats_data=CustomerStatsSchema(
                total_credits=total_credits,
                total_customers=total_customers,
                total_customer_with_credit=total_customer_with_credit,
                total_outstanding=total_outstanding
            )

            await self.customer_stats_repo_obj.update_stats(data=stats_data,type=StatsUpdateType.INCR)
            
            customer_name = data.name if hasattr(data, 'name') else 'Unknown'


            try:
                from messaging.main import RabbitMQMessagingConfig
                rabbitmq_msg_obj = RabbitMQMessagingConfig()
                
                analytics_payload = {
                    "shop_id": data.shop_id,
                    "datas": [
                        {
                            "customer_id": customer_id,
                            "credit_limit": total_credits,
                            "outstanding_amounts": 0,
                            "cleared_amounts": 0
                        }
                    ]
                }
                
                await rabbitmq_msg_obj.publish_event(
                    routing_key="analytics.service.routing.key",
                    exchange_name="analytics.service.exchange",
                    payload=analytics_payload,
                    headers={
                        "entity_name": "customer_event",
                        "service_name": "ANALYTICS",
                        "saga_id": "none",
                        "reply_key": "none",
                        "reply_exchange": "none",
                        "reply_entity_name": "none",
                        "body": analytics_payload
                    }
                )
            except Exception as e:
                ic(f"Failed to publish analytics event: {e}")


        return res
    

    async def update(self,data:UpdateCustomerSchema) -> dict | None:

        cust_get_res=await self.get_customer_by_id(data=GetCustomerByIdSchema(id=data.id,shop_id=data.shop_id))

        ic(cust_get_res)
        if not cust_get_res:
            ic("The given customer doesn't exists")
            return False
        
        
        temp_credit_infos={
            'limit':data.credit_infos.limit,
            'notes':data.credit_infos.notes,
            'terms':data.credit_infos.terms
        }
        if not data.can_have_credit:
            temp_credit_infos['limit']=0
            temp_credit_infos["notes"]=None
            temp_credit_infos['terms']=None

        
        if data.credit_infos.type==CustomerOutstandingAddEnums.INCREMENT:
            limit=limit=cust_get_res['credit_infos']['limit']+temp_credit_infos["limit"]
            credit_infos=CustomerCreditInfosType(limit=limit,notes=temp_credit_infos['notes'],terms=temp_credit_infos['terms'])
        elif data.credit_infos.type==CustomerOutstandingAddEnums.DECREMENT:
            limit=limit=cust_get_res['credit_infos']['limit']-temp_credit_infos["limit"]
            credit_infos=CustomerCreditInfosType(limit=limit,notes=temp_credit_infos['notes'],terms=temp_credit_infos['terms'])


        final_data=UpdateCustomerDbSchema(credit_infos=credit_infos,**data.model_dump(exclude=['credit_infos']))

        res=await self.customer_repo_obj.update(data=final_data)
        ic(res)


        # For read Db
        if res:
            cust_obj=await CustomFieldsService(session=self.session).upsert_values(
                data=CreateCustomFieldValueSchema(
                        shop_id=data.shop_id,
                        customer_id=data.id,
                        value_infos=[
                            {'field_id':id,"value":value}
                            for id,value in data.custom_fields.items()
                        ]
                    )
            )
            ic(cust_obj)
            try:
                from messaging.main import RabbitMQMessagingConfig
                rabbitmq_msg_obj = RabbitMQMessagingConfig()
                await rabbitmq_msg_obj.publish_event(
                    routing_key="activity_logs.routing.key",
                    exchange_name="activity_logs.exchange",
                    payload={
                        "shop_id": data.shop_id,
                        "user_name": "Hyperlocal-User",
                        "service": "Customer",
                        "action": "UPDATED",
                        "entity_type": "Customer",
                        "entity_id": data.id,
                        "description": f"Updated Customer {data.id}",
                        "changes": [{"field": "id", "before": str(data.id), "after": "UPDATED"}]
                    },
                    headers={}
                )

                # Send delta analytics event
                old_credit_limit = cust_get_res.get('credit_infos', {}).get('limit', 0.0) if cust_get_res.get('credit_infos') else 0.0
                new_credit_limit = limit
                delta_credit_limit = new_credit_limit - old_credit_limit
                
                analytics_payload = {
                    "shop_id": data.shop_id,
                    "action": "update",
                    "datas": [
                        {
                            "customer_id": data.id,
                            "credit_limit": float(delta_credit_limit),
                            "outstanding_amounts": 0.0,
                            "cleared_amounts": 0.0
                        }
                    ]
                }
                await rabbitmq_msg_obj.publish_event(
                    routing_key="analytics.service.routing.key",
                    exchange_name="analytics.service.exchange",
                    payload=analytics_payload,
                    headers={
                        "entity_name": "customer_event",
                        "service_name": "ANALYTICS",
                        "saga_id": "none",
                        "reply_key": "none",
                        "reply_exchange": "none",
                        "reply_entity_name": "none",
                        "body": analytics_payload
                    }
                )
            except Exception as e:
                ic(f"Failed to publish events: {e}")
        return res
    
    async def delete(self,data:DeleteCustomerSchema) -> dict | None:
        final_data=DeleteCustomerDbSchema(**data.model_dump())
        res=await self.customer_repo_obj.delete(data=final_data)
        ic(res)

        if res:
            total_credits=-res['credit_infos']['limit']
            total_customers=-1
            total_customer_with_credit=-1 if res['can_have_credit'] else 0
            total_outstanding=-res['outstanding_infos']['amount'] if res['outstanding_infos'] else 0

            stats_data=CustomerStatsSchema(
                total_customers=total_customers,
                total_customer_with_credit=total_customer_with_credit,
                total_credits=total_credits,
                total_outstanding=total_outstanding
            )

            await self.customer_stats_repo_obj.update_stats(data=stats_data,type=StatsUpdateType.INCR)
            
            customer_name = res.get('name', 'Unknown')

            try:
                from messaging.main import RabbitMQMessagingConfig
                rabbitmq_msg_obj = RabbitMQMessagingConfig()
                
                analytics_payload = {
                    "shop_id": data.shop_id,
                    "action": "delete",
                    "datas": [
                        {
                            "customer_id": data.id,
                            "credit_limit": -float(res['credit_infos']['limit']) if res.get('credit_infos') else 0.0,
                            "outstanding_amounts": -float(res['outstanding_infos']['amount']) if res.get('outstanding_infos') else 0.0,
                            "cleared_amounts": 0.0
                        }
                    ]
                }
                await rabbitmq_msg_obj.publish_event(
                    routing_key="analytics.service.routing.key",
                    exchange_name="analytics.service.exchange",
                    payload=analytics_payload,
                    headers={
                        "entity_name": "customer_event",
                        "service_name": "ANALYTICS",
                        "saga_id": "none",
                        "reply_key": "none",
                        "reply_exchange": "none",
                        "reply_entity_name": "none",
                        "body": analytics_payload
                    }
                )
            except Exception as e:
                ic(f"Failed to publish analytics event on customer delete: {e}")

        return res
    
    async def add_outstanding(self,data:CreateCustomerOutstandingSchema) -> dict | None:
        cur_outst_amt=data.outstanding_infos.amount
        # STEP-1 CHECKING THE TYPE IF INCREMENT MEANS NEED TO DO CUSTOMER EXISTANCE FOR GETTTING PREVIOUS VALUES
        if data.type!=CustomerOutstandingAddEnums.DIRECT:
            cust_get_res=await self.get_customer_by_id(data=GetCustomerByIdSchema(id=data.id,shop_id=data.shop_id))
            if not cust_get_res:
                ic("The given customer doesn't exists")
                return False
            ic(cust_get_res)
            prev_outst_amt=cust_get_res.get('outstanding_infos').get("amount",0) if cust_get_res.get('outstanding_infos') else 0
            cur_outst_amt=prev_outst_amt+data.outstanding_infos.amount if data.type==CustomerOutstandingAddEnums.INCREMENT else prev_outst_amt-data.outstanding_infos.amount
            if cur_outst_amt<0:
                ic("Credit amount should not be goes into negative")
                return False
        outstanding_infos=CustomerOutstandingInfosType(amount=cur_outst_amt)
        final_data=CreateCustomerOutstandingDbSchema(outstanding_infos=outstanding_infos,**data.model_dump(exclude=['outstanding_infos']))
        res=await self.customer_repo_obj.add_outstanding(data=final_data)
        ic(res)

        if res:

            total_customers=0
            total_customer_with_credit=0
            total_credits=0
            total_outstanding=data.outstanding_infos.amount

            stats_data=CustomerStatsSchema(
                total_customers=total_customers,
                total_customer_with_credit=total_customer_with_credit,
                total_credits=total_credits,
                total_outstanding=total_outstanding
            )

            await self.customer_stats_repo_obj.update_stats(data=stats_data,type=StatsUpdateType.INCR)

        return res
    
    
    async def clear_outstanding(self,data:CreateCustomerOutstandingClearedSchema) -> dict | None:
        outst_clr_id=generate_uuid()
        # STEP-1 CHECKING THE CUSTOMER EXISTANCE FOR GETTTING PREVIOUS VALUES
        cust_get_res=await self.get_customer_by_id(data=GetCustomerByIdSchema(id=data.customer_id,shop_id=data.shop_id))
        if not cust_get_res:
            ic("The given customer doesn't exists")
            return False
        
        # STEP-2 GETTING THE CLEARED AMOUNT AND CREATING THE BEFORE AND AFTER OUTSTANDING INFO
        prev_outst_amt=cust_get_res.get('outstanding_infos').get("amount",0) if cust_get_res.get('outstanding_infos') else 0
        amount_cleared=0

        for payinfo in data.payment_infos:
            amount_cleared+=payinfo.amount

        if amount_cleared>prev_outst_amt:
            ic("Outstanding clearing amount should not be grater than the outstanding amount")
            return False
        
        cur_outst_amt=prev_outst_amt-amount_cleared
        if cur_outst_amt<0:
            ic("Credit amount should not be goes into negative")
            return False
        
        cleared_infos=CustomerClearedInfosType(
            outstanding_before=prev_outst_amt,
            outstanding_after=cur_outst_amt
        )

        # STEP-3 UPDAING ON THE DB
        final_data=CreateCustomerOutstandingClearedDbSchema(cleared_infos=cleared_infos,**data.model_dump())
        outstanding_infos=CustomerOutstandingInfosType(amount=cur_outst_amt)
        # STEP-3 (STEP-1) UPDATE THE CUSTOMER OUTSTANDING 
        cust_upd_res=await self.add_outstanding(data=CreateCustomerOutstandingSchema(id=data.customer_id,shop_id=data.shop_id,outstanding_infos=outstanding_infos,type=CustomerOutstandingAddEnums.DIRECT))
        ic(cust_upd_res)
        if not cust_upd_res:
            ic("Error Updating the customer outstanding")
            return False
        # STEP-3 (STEP-2) THEN CREATE THE CLEAR OUTSTANDING
        outst_clr_res=await self.customer_repo_obj.clear_outstanding(data=final_data)
        ic(outst_clr_res)

        if outst_clr_res:

            total_customers=0
            total_customer_with_credit=0
            total_credits=0
            total_outstanding=-amount_cleared
            ic(total_credits,total_customers,total_customer_with_credit,total_outstanding)

            stats_data=CustomerStatsSchema(
                total_customers=total_customers,
                total_customer_with_credit=total_customer_with_credit,
                total_credits=total_credits,
                total_outstanding=total_outstanding
            )

            await self.customer_stats_repo_obj.update_stats(data=stats_data,type=StatsUpdateType.INCR)
            
        return outst_clr_res
    

    # Readables
    async def get_customers(self,data:GetAllCustomerSchema) -> List[dict] | None:
        res=await self.customer_repo_obj.get(data=data)
        ic(res)
        return res
    
    async def get_customer_by_shop_id(self,data:GetCustomerByShopIdSchema) -> List[dict] | None:
        res=await self.customer_repo_obj.getby_shop_id(data=data)
        ic(res)
        return res
    
    async def get_customer_by_id(self,data:GetCustomerByIdSchema) -> dict | None:
        res=await self.customer_repo_obj.getby_id(data=data)
        ic(res)
        return res
    

    async def get_outst_clr(self,data:GetAllCustomerOutstClearedSchema) -> List[dict] | None:
        res=await self.customer_repo_obj.get_outst_cleared(data=data)
        ic(res)
        return res
    
    async def get_outst_clr_by_shop_id(self,data:GetCustomerOutstClearedByShopIdSchema) -> List[dict] | None:
        res=await self.customer_repo_obj.get_outst_cleared_by_shop_id(data=data)
        ic(res)
        return res
    
    async def get_outst_clr_by_id(self,data:GetCustomerOutstClearedByIdSchema) -> List[dict] | None:
        res=await self.customer_repo_obj.get_outst_cleared_by_id(data=data)
        ic(res)
        return res
