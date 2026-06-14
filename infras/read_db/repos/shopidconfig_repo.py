import httpx
from icecream import ic
from ..models.shopidconfig_model import ShopIdConfigReadModel

# Global in-memory cache
SHOP_CONFIG_CACHE = {}

class ShopIdConfigReadDbRepo:
    
    @classmethod
    async def upsert_config(cls, data: ShopIdConfigReadModel):
        try:
            SHOP_CONFIG_CACHE[data.shop_id] = data.config
            ic(f"In-memory cache updated for shop {data.shop_id}")
            return True
        except Exception as e:
            ic(f"Error in ShopIdConfigReadDbRepo upsert_config: {e}")
            return False

    @classmethod
    async def get_config(cls, shop_id: str) -> dict:
        try:
            # 1. Check in-memory cache
            if shop_id in SHOP_CONFIG_CACHE:
                return {k: v.model_dump() for k, v in SHOP_CONFIG_CACHE[shop_id].items()}
            
            # 2. HTTP Fallback to Utility Service
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"http://127.0.0.1:8001/shop-id-config/{shop_id}")
                if res.status_code == 200:
                    data = res.json()
                    if data.get("success") and data.get("data"):
                        raw_config = data["data"].get("config", {})
                        # Cache it for next time
                        from ..models.shopidconfig_model import ModuleConfigSchema
                        parsed = {k: ModuleConfigSchema(**v) for k, v in raw_config.items()}
                        SHOP_CONFIG_CACHE[shop_id] = parsed
                        return raw_config
            return {}
        except Exception as e:
            ic(f"Error in ShopIdConfigReadDbRepo get_config: {e}")
            return {}
