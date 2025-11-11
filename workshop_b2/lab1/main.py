from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse
from graphql import print_schema

from ..models import AllModels
from .database import create_db_and_tables
from .graphql.router import init_app
from .rest.router import router as rest_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="Autocon4 Workshop C2 - Lab1",
    docs_url="/docs",
    lifespan=lifespan,
)

app.include_router(rest_router)

graphql_app = init_app()
app.include_router(graphql_app, prefix="/graphql")


@app.get("/schema.graphql", include_in_schema=True)
async def get_graphql_schema() -> PlainTextResponse:
    return PlainTextResponse(content=print_schema(graphql_app.schema._schema))  # type: ignore


@app.get("/jsonschema", include_in_schema=True)
async def get_json_schema() -> JSONResponse:
    return JSONResponse(content=AllModels.model_json_schema())
