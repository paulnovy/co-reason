from fastapi import FastAPI

from .api.variables import router as variable_router

app = FastAPI()

app.include_router(variable_router)

@app.get("/")
def read_root():
    return {"msg": "ok"}
