from fastapi import APIRouter
from pydantic import BaseModel

from router_service import RouterService

router = APIRouter(prefix="/router")

service = RouterService()


class QueryRequest(BaseModel):
    query: str


@router.post("/predict")
def predict(request: QueryRequest):

    return service.predict(request.query)