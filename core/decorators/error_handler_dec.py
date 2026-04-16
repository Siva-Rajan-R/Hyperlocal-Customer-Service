from fastapi import HTTPException
from icecream import ic
import inspect,asyncio
from functools import wraps
from hyperlocal_platform.core.models.req_res_models import BaseResponseTypDict,ErrorResponseTypDict,SuccessResponseTypDict


def catch_errors(func):
    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                ic(f"Error at {func.__name__} -> {e}")
                raise HTTPException(
                    status_code=500, 
                    detail=ErrorResponseTypDict(
                        status_code=500,
                        msg="Error : Internal server error",
                        description="Try agin the request after sometimes , if it's persist. contact our team support@debuggers.com",
                        succsess=False
                    )
                )
        return wrapper

    else:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                ic(f"Error at {func.__name__} -> {e}")
                raise HTTPException(
                    status_code=500, 
                    detail=ErrorResponseTypDict(
                        status_code=500,
                        msg="Error : Internal server error",
                        description="Try agin the request after sometimes , if it's persist. contact our team support@debuggers.com",
                        succsess=False
                    )
                )
            
        return wrapper