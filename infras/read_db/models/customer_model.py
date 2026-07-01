from pydantic import BaseModel
from typing import Optional


class CustomerStatsSchema(BaseModel):
    total_customers:Optional[int]=0
    total_customer_with_credit:Optional[int]=0
    total_credits:Optional[float]=0
    total_outstanding:Optional[float]=0