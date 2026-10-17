import uvicorn
from fastapi import FastAPI
from app.core.database import engine, Base
from app.modules.agent_mgmt.router import router


app = FastAPI(title="编程智能体管理模块", version="0.1.0")


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)
