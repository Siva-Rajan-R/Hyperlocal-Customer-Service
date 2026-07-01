from ..collections.customer import customer_collection
from ..models.customer_model import CustomerStatsSchema
from icecream import ic
from typing import Optional,List
from enum import Enum
from core.data_formats.enums.customer_enums import StatsUpdateType


class CustomerStatsRepo:
    @staticmethod
    async def init_stats():
        customer_db = customer_collection()

        await customer_db.update_one(
            {"_id": "customer_stats"},
            {
                "$setOnInsert": {
                    "total_credits": 0,
                    "total_customer_with_credit": 0,
                    "total_customers": 0,
                    "total_outstanding": 0,
                }
            },
            upsert=True
        )

        return True
    
    @staticmethod
    async def update_stats(data: CustomerStatsSchema,type: StatsUpdateType):
        customer_db = customer_collection()

        stats_data = data.model_dump(
            mode="json",
            exclude_none=True
        )

        # if type == StatsUpdateType.DECR:
        #     stats_data = {
        #         key: -value
        #         for key, value in stats_data.items()
        #     }

        await customer_db.update_one(
            {"_id":"customer_stats"},
            {
                "$inc": stats_data
            },
            upsert=True
        )

        return True
    

