from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.agents.agent import create_uni_resource_agent
from src.db.database import init_database
import uvicorn

# 初始化数据库
init_database()

# 创建FastAPI应用
app = FastAPI(
    title="Uni-Resource Agent API",
    description="统一资源管理AI助手API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建Agent实例
agent = create_uni_resource_agent()

@app.get("/")
async def root():
    return {"message": "Uni-Resource Agent API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/query")
async def query_agent(input_text: str):
    """处理用户查询"""
    try:
        result = agent.invoke({"input": input_text})
        return {"response": result["output"]}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)