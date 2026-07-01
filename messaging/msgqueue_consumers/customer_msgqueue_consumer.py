from messaging.main import RabbitMQMessagingConfig
from icecream import ic
import orjson
from aio_pika.abc import AbstractIncomingMessage
from infras.primary_db.main import AsyncCustomerLocalSession
from infras.primary_db.repos.customer_repo import CustomerRepo
from schemas.v1.customer_schemas.request_schemas import GetCustomerByIdSchema
from schemas.v1.customer_schemas.db_schemas import CreateCustomerOutstandingDbSchema
from core.data_formats.enums.customer_enums import CustomerOutstandingAddEnums

class CustomerMsgQueueConsumer:
    async def process_outstanding_update(self, message: AbstractIncomingMessage):
        try:
            async with message.process():
                payload = orjson.loads(message.body)
                ic(f"Received customer outstanding update: {payload}")
                
                shop_id = payload.get("shop_id")
                customer_id = payload.get("customer_id")
                amount = float(payload.get("amount", 0.0))
                action = payload.get("action")
                
                if not shop_id or not customer_id:
                    ic("Missing shop_id or customer_id in payload")
                    return
                
                async with AsyncCustomerLocalSession() as session:
                    customer_repo = CustomerRepo(session=session)
                    customer = await customer_repo.get_by_id(data=GetCustomerByIdSchema(id=customer_id, shop_id=shop_id))
                    
                    if not customer:
                        ic(f"Customer {customer_id} not found in shop {shop_id}")
                        return
                    
                    # Update outstanding balance logic
                    outstanding = customer.get("outstanding_infos", {})
                    if not outstanding:
                        outstanding = {"amount": 0.0}
                        
                    current_balance = outstanding.get("amount", 0.0)
                    
                    if action == "CLEAR":
                        # We are clearing outstanding balance (i.e. refunding into the customer's account/clearing debt)
                        current_balance -= amount
                    elif action == "ADD":
                        # We are adding to outstanding balance (i.e. they owe us more)
                        current_balance += amount
                        
                    outstanding["amount"] = current_balance
                    
                    update_schema = CreateCustomerOutstandingDbSchema(
                        id=customer_id,
                        shop_id=shop_id,
                        outstanding_infos=outstanding,
                        type=CustomerOutstandingAddEnums.DEDUCT if action == "CLEAR" else CustomerOutstandingAddEnums.ADD
                    )
                    
                    await customer_repo.add_outstanding(data=update_schema)
                    
                    ic(f"Successfully updated outstanding balance for customer {customer_id} to {current_balance}")
                
        except Exception as e:
            ic(f"Error processing customer outstanding update event: {e}")

    async def consume(self):
        try:
            rb_msg = RabbitMQMessagingConfig()
            queue = await rb_msg.create_queue(
                routing_key="customer.outstanding.update",
                exchange_name="customer_exchange",
                queue_name="customer_service_outstanding_q"
            )
            await rb_msg.consume_event(queue_name=queue.name, handler=self.process_outstanding_update)
            ic("CustomerMsgQueueConsumer started listening on customer_service_outstanding_q")
        except Exception as e:
            ic(f"Failed to start CustomerMsgQueueConsumer: {e}")
