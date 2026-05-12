from daedalus_search.server import Server
from fastapi import FastAPI

server = Server("Verso")
app = FastAPI()
app.include_router(server.router)