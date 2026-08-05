from ..main import AsyncSession
from ..repos.customer_repo import CustomerRepo
from schemas.v1.customer_schemas.request_schemas import CreateCustomerSchema,UpdateCustomerSchema,DeleteCustomerSchema,CreateCustomerOutstandingClearedSchema,CreateCustomerOutstandingSchema,GetAllCustomerOutstClearedSchema,GetAllCustomerSchema,GetCustomerByIdSchema,GetCustomerByShopIdSchema,GetCustomerOutstClearedByIdSchema,GetCustomerOutstClearedByShopIdSchema
from schemas.v1.customer_schemas.db_schemas import CreateCustomerDbSchema,UpdateCustomerDbSchema,DeleteCustomerDbSchema,CreateCustomerOutstandingClearedDbSchema,CreateCustomerOutstandingDbSchema
from schemas.v1.customer_schemas.custom_types import CustomerOutstandingInfosType,CustomerClearedInfosType,CustomerCreditInfosType,CustomerPaymentInfosType
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
        # Check if customer already exists with the same mobile_number or email in this shop
        from sqlalchemy import or_
        email = data.contact_infos.email
        mobile_number = data.contact_infos.mobile_number
        
        conditions = []
        if email:
            conditions.append(Customers.contact_infos['email'].astext == email)
        if mobile_number:
            conditions.append(Customers.contact_infos['mobile_number'].astext == mobile_number)
            
        if conditions:
            stmt = select(Customers).where(
                Customers.shop_id == data.shop_id,
                or_(*conditions)
            )
            existing_cust = (await self.session.execute(stmt)).scalars().first()
            if existing_cust:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponseTypDict(
                        msg="Error : Creating Customer",
                        description="Customer with this email or mobile number already exists in this shop",
                        success=False,
                        status_code=400
                    )
                )

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
            
            customer_name = data.name if hasattr(data, 'name') else 'Customer'

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
                        "action": "CREATED",
                        "entity_type": "CUSTOMER",
                        "entity_id": str(customer_id),
                        "entity_name": str(customer_name),
                        "description": f"Created Customer {customer_name} ({customer_id})",
                        "changes": []
                    },
                    headers={}
                )

                analytics_payload = {
                    "shop_id": data.shop_id,
                    "entity_name": "CUSTOMER",
                    "entity_id": str(customer_id),
                    "action": "CREATE"
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
    

    async def create_bulk(self, data: List[CreateCustomerSchema]) -> List[dict]:
        results = []
        for item in data:
            try:
                res = await self.create(data=item)
                if res:
                    results.append(res)
            except Exception as e:
                ic(f"Error creating customer in bulk: {e}")
        return results
    

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

        
        credit_infos=CustomerCreditInfosType(limit=0)
        if data.credit_infos:
            if data.credit_infos.type==CustomerOutstandingAddEnums.INCREMENT:
                limit=limit=cust_get_res['credit_infos']['limit']+temp_credit_infos["limit"]
                credit_infos=CustomerCreditInfosType(limit=limit,notes=temp_credit_infos['notes'],terms=temp_credit_infos['terms'])
            elif data.credit_infos.type==CustomerOutstandingAddEnums.DECREMENT:
                limit=limit=cust_get_res['credit_infos']['limit']-temp_credit_infos["limit"]
                credit_infos=CustomerCreditInfosType(limit=limit,notes=temp_credit_infos['notes'],terms=temp_credit_infos['terms'])
            elif data.credit_infos.type==CustomerOutstandingAddEnums.DIRECT:
                credit_infos=CustomerCreditInfosType(**temp_credit_infos)



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
                
                # Build exact changes diff using exclude_unset=True, exclude_none=True
                def _is_empty_or_none(val):
                    if val is None: return True
                    if isinstance(val, (dict, list, set, str, tuple)) and len(val) == 0: return True
                    return str(val).strip() in ("None", "{}", "[]", "", "null", "NoneType")

                dumped_updates = data.model_dump(exclude_unset=True, exclude_none=True)
                changes = []
                for key, new_val in dumped_updates.items():
                    if key in ["id", "shop_id", "user_id", "cur_user_id"]:
                        continue
                    prev_val = cust_get_res.get(key)
                    if _is_empty_or_none(prev_val) and _is_empty_or_none(new_val):
                        continue
                    if prev_val != new_val and str(prev_val).strip() != str(new_val).strip():
                        changes.append({
                            "field": key,
                            "before": str(prev_val) if prev_val is not None else "None",
                            "after": str(new_val) if new_val is not None else "None"
                        })
                
                cust_name = cust_get_res.get('name') or getattr(data, 'name', None) or 'Customer'

                await rabbitmq_msg_obj.publish_event(
                    routing_key="activity_logs.routing.key",
                    exchange_name="activity_logs.exchange",
                    payload={
                        "shop_id": data.shop_id,
                        "user_name": "Hyperlocal-User",
                        "service": "Customer",
                        "action": "UPDATED",
                        "entity_type": "CUSTOMER",
                        "entity_id": str(data.id),
                        "entity_name": str(cust_name),
                        "description": f"Updated Customer {cust_name} ({data.id})",
                        "changes": changes
                    },
                    headers={}
                )

                # Send delta analytics event
                old_credit_limit = cust_get_res.get('credit_infos', {}).get('limit', 0.0) if cust_get_res.get('credit_infos') else 0.0
                new_credit_limit = limit
                delta_credit_limit = new_credit_limit - old_credit_limit
                
                analytics_payload = {
                    "shop_id": data.shop_id,
                    "entity_name": "CUSTOMER",
                    "entity_id": str(data.id),
                    "action": "UPDATE"
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
            
            customer_name = res.get('name', 'Customer')

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
                        "action": "DELETED",
                        "entity_type": "CUSTOMER",
                        "entity_id": str(data.id),
                        "entity_name": str(customer_name),
                        "description": f"Deleted Customer {customer_name} ({data.id})",
                        "changes": []
                    },
                    headers={}
                )
                
                analytics_payload = {
                    "shop_id": data.shop_id,
                    "entity_name": "CUSTOMER",
                    "entity_id": str(data.id),
                    "action": "DELETE"
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
    
    @start_db_transaction
    async def add_outstanding(self,data:CreateCustomerOutstandingSchema) -> dict | None:
        cur_outst_amt=data.outstanding_infos.amount
        prev_outst_amt=0.0
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
        exclude_fields = ['outstanding_infos', 'payment_infos', 'cleared_amount', 'total_amount', 'entity_name', 'entity_id', 'payment_method', 'notes']
        final_data=CreateCustomerOutstandingDbSchema(outstanding_infos=outstanding_infos,**data.model_dump(exclude=exclude_fields, exclude_none=True))
        res=await self.customer_repo_obj.add_outstanding(data=final_data)
        ic(res)

        if res:
            # If initial payment or entity_name/id or history metadata is passed, record history entry!
            initial_paid = data.cleared_amount if data.cleared_amount is not None else 0.0
            if not initial_paid and data.payment_infos:
                initial_paid = sum(p.get("amount", 0.0) if isinstance(p, dict) else getattr(p, "amount", 0.0) for p in data.payment_infos)

            if data.entity_name or data.entity_id or initial_paid > 0 or data.payment_infos or data.total_amount:
                try:
                    cleared_infos = CustomerClearedInfosType(
                        outstanding_before=float(prev_outst_amt),
                        outstanding_after=float(cur_outst_amt)
                    )
                    pay_infos_list = []
                    valid_methods = {"UPI", "CASH", "CARD", "BANK"}
                    if data.payment_infos:
                        for p in data.payment_infos:
                            m_raw = p.get("mode") or p.get("method") if isinstance(p, dict) else getattr(p, "method", "CASH")
                            m_str = str(m_raw).upper() if m_raw else "CASH"
                            if m_str not in valid_methods:
                                m_str = "CASH"
                            amt_val = p.get("amount") if isinstance(p, dict) else getattr(p, "amount", 0.0)
                            pay_infos_list.append(CustomerPaymentInfosType(method=m_str, amount=float(amt_val)))
                    else:
                        m_raw = getattr(data, "payment_method", "CASH") or "CASH"
                        m_str = str(m_raw).upper() if m_raw else "CASH"
                        if m_str not in valid_methods:
                            m_str = "CASH"
                        pay_infos_list = [CustomerPaymentInfosType(method=m_str, amount=float(initial_paid))]

                    add_infos = {
                        "entity_name": data.entity_name or "order",
                        "entity_id": str(data.entity_id) if data.entity_id else "",
                        "notes": data.notes or f"Initial payment for {data.entity_name or 'order'}",
                        "total_amount": float(data.total_amount or 0.0),
                        "paid_amount": float(initial_paid),
                        "on_credit_amount": float(data.outstanding_infos.amount)
                    }

                    cleared_db_schema = CreateCustomerOutstandingClearedDbSchema(
                        shop_id=data.shop_id,
                        customer_id=data.id,
                        payment_infos=pay_infos_list,
                        cleared_infos=cleared_infos,
                        additional_infos=add_infos
                    )
                    await self.customer_repo_obj.clear_outstanding(data=cleared_db_schema)
                    ic("Successfully saved customer outstanding history record")
                except Exception as ex:
                    ic("Error saving customer outstanding history record:", ex)

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

            try:
                await self.customer_stats_repo_obj.update_stats(data=stats_data,type=StatsUpdateType.INCR)
            except Exception as e:
                ic(f"Failed to update customer stats in read db: {e}")

            try:
                from messaging.main import RabbitMQMessagingConfig
                rabbitmq_msg_obj = RabbitMQMessagingConfig()
                analytics_payload = {
                    "shop_id": data.shop_id,
                    "entity_name": "CUSTOMER",
                    "entity_id": str(data.id),
                    "action": "UPDATE"
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
                ic(f"Failed to publish analytics event on customer add outstanding: {e}")

        return res
    
    
    @start_db_transaction
    async def clear_outstanding(self,data:CreateCustomerOutstandingClearedSchema) -> dict | None:
        outst_clr_id=generate_uuid()
        # STEP-1 CHECKING THE CUSTOMER EXISTANCE FOR GETTTING PREVIOUS VALUES
        cust_get_res=await self.get_customer_by_id(data=GetCustomerByIdSchema(id=data.id,shop_id=data.shop_id))
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
        final_data=CreateCustomerOutstandingClearedDbSchema(
            shop_id=data.shop_id,
            customer_id=data.id,
            payment_infos=data.payment_infos,
            cleared_infos=cleared_infos
        )
        outstanding_infos=CustomerOutstandingInfosType(amount=cur_outst_amt)
        # STEP-3 (STEP-1) UPDATE THE CUSTOMER OUTSTANDING 
        upd_db_schema=CreateCustomerOutstandingDbSchema(id=data.id,shop_id=data.shop_id,outstanding_infos=outstanding_infos,type=CustomerOutstandingAddEnums.DIRECT)
        cust_upd_res=await self.customer_repo_obj.add_outstanding(data=upd_db_schema)
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

            try:
                await self.customer_stats_repo_obj.update_stats(data=stats_data,type=StatsUpdateType.INCR)
            except Exception as e:
                ic(f"Failed to update customer stats in read db: {e}")

            try:
                from messaging.main import RabbitMQMessagingConfig
                rabbitmq_msg_obj = RabbitMQMessagingConfig()
                analytics_payload = {
                    "shop_id": data.shop_id,
                    "entity_name": "CUSTOMER",
                    "entity_id": str(data.id),
                    "action": "UPDATE"
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
                ic(f"Failed to publish analytics event on customer clear outstanding: {e}")
            
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
