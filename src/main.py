from fastapi import FastAPI
from routes import base, data

app = FastAPI()

app.include_router(base.base_router) # it's route base that check out if the server is working or not 
app.include_router(data.data_router)