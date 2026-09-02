import os
import json
from datetime import datetime, timezone
import redis.asyncio as aioredis
from icecream import ic
from ..main import AsyncCustomerLocalSession
from ..repos.customer_repo import CustomerRepo
from schemas.v1.customer_schemas.request_schemas import GetCustomerByShopIdSchema
from helpers.export_helper import generate_csv_bytes, generate_xlsx_bytes
from integrations.utility_service import upload_export_file
from helpers.emit_notification import emit_notification

REDIS_URL = os.getenv("PLATFORM_REDIS_URL") or "redis://localhost:6379"

async def process_customer_export(payload: dict) -> dict:
    job_id = payload.get("job_id")
    shop_id = payload.get("shop_id")
    from_record = int(payload.get("from_record", 1))
    to_record = int(payload.get("to_record", 100))
    fmt = str(payload.get("format", "csv")).lower()
    query = payload.get("query")
    from_date = payload.get("from_date")
    to_date = payload.get("to_date")
    user_id = payload.get("user_id")
    has_outstanding = payload.get("has_outstanding")

    limit = max(to_record - from_record + 1, 1)
    offset = from_record

    redis_client = aioredis.Redis.from_url(REDIS_URL, decode_responses=True)
    
    # 1. Update status to IN_PROGRESS
    if job_id:
        await redis_client.set(
            f"EXPORT_JOB:{job_id}",
            json.dumps({
                "job_id": job_id,
                "entity": "CUSTOMER",
                "status": "IN_PROGRESS",
                "params": payload,
                "started_at": datetime.now(timezone.utc).isoformat()
            }),
            ex=86400
        )

    try:
        # 2. Fetch Customers
        async with AsyncCustomerLocalSession() as session:
            repo = CustomerRepo(session=session)
            fetch_schema = GetCustomerByShopIdSchema(
                shop_id=shop_id,
                q=query or "",
                limit=limit,
                offset=offset,
                from_date=from_date,
                to_date=to_date,
                has_outstanding=has_outstanding
            )
            customers = await repo.getby_shop_id(data=fetch_schema)

        # 3. Format Data
        headers = [
            "Customer ID", "Name", "Mobile Number", "Email",
            "Credit Allowed", "Credit Limit", "Outstanding Amount",
            "Address", "City", "Pincode", "State", "Created Date"
        ]

        rows = []
        for cust in (customers or []):
            contact = cust.get("contact_infos") or {}
            credit = cust.get("credit_infos") or {}
            outst = cust.get("outstanding_infos") or {}
            address = cust.get("address") or {}

            rows.append([
                cust.get("ui_id") or cust.get("id"),
                cust.get("name", ""),
                contact.get("mobile_number", ""),
                contact.get("email", ""),
                "Yes" if cust.get("can_have_credit") else "No",
                credit.get("limit", 0.0),
                outst.get("amount", 0.0),
                address.get("full_address", ""),
                address.get("city", ""),
                address.get("pincode", ""),
                address.get("state", ""),
                cust.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if isinstance(cust.get("created_at"), datetime) else str(cust.get("created_at") or "")
            ])

        # 4. Generate File Bytes
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if fmt == "xlsx":
            file_bytes = generate_xlsx_bytes(headers, rows, sheet_name="Customers")
            file_name = f"customers_{shop_id}_{from_record}_{to_record}_{timestamp}.xlsx"
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            file_bytes = generate_csv_bytes(headers, rows)
            file_name = f"customers_{shop_id}_{from_record}_{to_record}_{timestamp}.csv"
            content_type = "text/csv"

        # 5. Upload File
        download_url = await upload_export_file(
            file_bytes=file_bytes,
            filename=file_name,
            content_type=content_type
        )

        # 6. Update Redis status to COMPLETED
        result_data = {
            "job_id": job_id,
            "entity": "CUSTOMER",
            "status": "COMPLETED",
            "download_url": download_url,
            "file_name": file_name,
            "total_records": len(rows),
            "completed_at": datetime.now(timezone.utc).isoformat()
        }

        if job_id:
            await redis_client.set(
                f"EXPORT_JOB:{job_id}",
                json.dumps(result_data),
                ex=86400
            )

        # 7. Emit Notification Event
        await emit_notification(
            title="Customer Export Ready",
            message=f"Export of {len(rows)} customer records ({from_record}-{to_record}) is ready for download.",
            type="info",
            user_id=user_id or shop_id,
            additional_metadata={
                "download_url": download_url,
                "file_name": file_name,
                "entity": "CUSTOMER",
                "count": len(rows),
                "job_id": job_id
            }
        )

        return result_data

    except Exception as e:
        ic(f"Error executing customer export task: {e}")
        err_data = {
            "job_id": job_id,
            "entity": "CUSTOMER",
            "status": "FAILED",
            "error": str(e),
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        if job_id:
            await redis_client.set(
                f"EXPORT_JOB:{job_id}",
                json.dumps(err_data),
                ex=86400
            )
        return err_data
    finally:
        await redis_client.aclose()
