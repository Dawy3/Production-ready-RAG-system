from fastapi import FastAPI, APIRouter

base_router= APIRouter(
    prefix="/api/v1",
    
)

@base_router.get("/")
def welcome():
    return{
        "message" : "Hello, it's working"
    }