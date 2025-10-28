from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from sorawm.server.lifespan import lifespan
from sorawm.server.router import router


def init_app():
    app = FastAPI(lifespan=lifespan)
    
    # 添加全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": f"服务器错误: {str(exc)}"}
        )
    
    app.include_router(router)
    return app
