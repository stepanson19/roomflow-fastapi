from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse

from app.database import Base, engine, session_factory
from app.demo_data import seed_demo_data
from app.errors import http_exception_handler, validation_exception_handler
from app.routers import api_router
from app.ui import HOME_PAGE


@asynccontextmanager
async def lifespan(_application: FastAPI):
    Base.metadata.create_all(bind=engine)
    with session_factory() as db:
        seed_demo_data(db)
    yield


app = FastAPI(
    title="RoomFlow API",
    version="1.0.0",
    description="API for rehearsal room bookings with JWT auth and smart slot recommendations.",
    lifespan=lifespan,
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index() -> str:
    return HOME_PAGE
