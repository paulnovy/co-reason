from fastapi import FastAPI

from .api.variables import router as variable_router

app = FastAPI()

app.include_router(variable_router)

@app.get("/")
def read_root():
    return {"msg": "ok"}
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
