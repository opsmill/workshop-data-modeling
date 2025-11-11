from contextlib import asynccontextmanager
import time
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from neo4j.exceptions import ServiceUnavailable

from workshop_b2.lab2.database import create_initial_constraints, get_db
from workshop_b2.lab2.rest.router import router as rest_router
from workshop_b2.lab2.graphql.router import init_app

from graphql import print_schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = get_db()
    max_retries = 10
    retry_delay = 5
    for attempt in range(max_retries):
        try:
            db.verify_connectivity()
            print("Server successfully started")
            break
        except ServiceUnavailable:
            print(f"Attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            if attempt == max_retries - 1:
                print("Max retries reached, shutting down.")
                db.close()
                raise
    create_initial_constraints()
    yield
    db.close()


app = FastAPI(
    title="Autocon4 Workshop C2 - Lab2",
    docs_url="/docs",
    lifespan=lifespan,
)

app.include_router(rest_router)

graphql_app = init_app()
app.include_router(graphql_app, prefix="/graphql")


@app.get("/schema.graphql", include_in_schema=True)
async def get_graphql_schema() -> PlainTextResponse:
    return PlainTextResponse(content=print_schema(graphql_app.schema._schema))  # type: ignore
