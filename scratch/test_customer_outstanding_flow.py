import asyncio
import sys
import os
import uuid
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infras.primary_db.main import AsyncCustomerLocalSession, init_pg_db
from infras.primary_db.services.customer_service import CustomerService
from infras.primary_db.models.customer_model import Customers
from schemas.v1.customer_schemas.request_schemas import CreateCustomerOutstandingSchema, CreateCustomerOutstandingClearedSchema
from schemas.v1.customer_schemas.custom_types import CustomerOutstandingInfosType, CustomerPaymentInfosType
from core.data_formats.enums.customer_enums import CustomerOutstandingAddEnums
from icecream import ic

async def test_customer_outstanding_flow():
    await init_pg_db()
    
    async with AsyncCustomerLocalSession() as session:
        service = CustomerService(session=session)
        shop_id = "test-shop-cust-clear"
        cust_id = str(uuid.uuid4())
        
        # Seed customer
        cust = Customers(
            id=cust_id,
            shop_id=shop_id,
            ui_id="CUST-200",
            name="Alice Customer",
            can_have_credit=True,
            location_infos={"state": "TN", "country": "India"},
            contact_infos={"email": "alice@example.com"},
            outstanding_infos={"amount": 500.0}
        )
        session.add(cust)
        await session.commit()
        ic("Seeded customer =>", cust_id)
        
        # Test clear_outstanding (clearing 200 of 500 outstanding debt)
        clear_data = CreateCustomerOutstandingClearedSchema(
            shop_id=shop_id,
            id=cust_id,
            payment_infos=[CustomerPaymentInfosType(method="CASH", amount=200.0)]
        )
        
        res = await service.clear_outstanding(data=clear_data)
        ic("Clear outstanding result =>", res)
        assert res is not False, "clear_outstanding should succeed!"
        
        # Verify Customer Outstanding History
        history = await service.customer_repo_obj.get_outst_cleared_by_shop_id(
            __import__("schemas.v1.customer_schemas.request_schemas", fromlist=["GetCustomerOutstClearedByShopIdSchema"]).GetCustomerOutstClearedByShopIdSchema(
                shop_id=shop_id, customer_id=cust_id, offset=1, limit=10
            )
        )
        ic("Customer Outstanding Cleared History =>", history)
        assert len(history) > 0, "History entry should exist!"
        ic("SUCCESS: Customer clear_outstanding flow completed cleanly without transaction error!")

if __name__ == "__main__":
    asyncio.run(test_customer_outstanding_flow())
