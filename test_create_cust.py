import asyncio
from schemas.v1.customer_schemas.request_schemas import CreateCustomerSchema
from schemas.v1.customer_schemas.custom_types import CustomerContactInfosType, CustomerLocationInfosType, CustomerCreditInfosType
from api.handlers.customer_handler import HandleCustomerRequest
from infras.primary_db.main import get_pg_async_session
import asyncpg

async def test_create_customer():
    shop_id = "697a78a9-3343-57c3-9b96-f9e3aad9a61e"
    
    async for session in get_pg_async_session():
        handler = HandleCustomerRequest(session=session)
        payload = CreateCustomerSchema(
            shop_id=shop_id,
            name="Test Customer Antigravity",
            contact_infos=CustomerContactInfosType(
                email="test_anti@example.com",
                mobile_number="9876543210"
            ),
            location_infos=CustomerLocationInfosType(
                full_address="123 Main St, Chennai",
                state="Tamil Nadu",
                country="India",
                zipcode="600001"
            ),
            can_have_credit=False,
            credit_infos=None,
            custom_fields={}
        )
        res = await handler.create(data=payload)
        print("Create response:", res)
        break

    # Verify directly in PostgreSQL
    conn = await asyncpg.connect("postgresql://postgres:437734@127.0.0.1:5432/CustomerServiceDb")
    cust = await conn.fetchrow("SELECT id, ui_id, name, contact_infos FROM customers WHERE shop_id = $1 AND name = $2", shop_id, "Test Customer Antigravity")
    print("Postgres customer record:", dict(cust) if cust else None)
    
    # Clean up test customer
    if cust:
        await conn.execute("DELETE FROM customers WHERE id = $1", cust["id"])
        print("Cleaned up test customer from DB.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(test_create_customer())
