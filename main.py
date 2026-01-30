
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from routers import agent_response, relevant_context, tools_management, tool_template_router, apikey_router

# 1. Khởi tạo app
app = FastAPI()

# Cấu hình CORS
origins = [
    "http://localhost:3000", # Port của Next.js
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    #allow_origins=origins,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], # Cho phép tất cả các method (GET, POST, etc.)
    allow_headers=["*"],
)

# 1. Gắn router Products
# prefix="/products": Tự động thêm chữ /products vào trước mọi link trong file đó
# tags=["Products"]: Gom nhóm trong giao diện Swagger UI cho đẹp
app.include_router(agent_response.router, prefix="/agent_response", tags=["Agent Response"])
app.include_router(relevant_context.router, prefix="/rag", tags=["Chunk and Embedding"])
app.include_router(tools_management.router, prefix="/tools_management", tags=["Tools Management"])
app.include_router(tool_template_router.router, prefix="/tool_template", tags=["Tools Template"])
app.include_router(apikey_router.router, prefix="/apikeys", tags=["API Keys Management"])

# API Test đơn giản để biết server đang chạy
@app.get("/")
def read_root():
    return {"Hello": "Đây là API BA AI"}