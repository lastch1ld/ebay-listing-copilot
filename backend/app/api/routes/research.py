from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.application.jobs import JobRunner
from app.application.research import ResearchService
from app.persistence.models import ItemModel

router = APIRouter()


@router.post("/api/items/{item_id}/research")
async def start_research(item_id: str, request: Request) -> JSONResponse:
    job_runner: JobRunner = request.app.state.job_runner
    research_service: ResearchService = request.app.state.research_service
    session_factory = request.app.state.session_factory

    with session_factory() as session:
        if session.get(ItemModel, item_id) is None:
            return JSONResponse(status_code=404, content={"detail": f"item not found: {item_id}"})

    job_id = job_runner.enqueue("ITEM_RESEARCH", {"item_id": item_id})

    async def handle(input_data: dict[str, object]) -> str | None:
        await research_service.run(item_id=str(input_data["item_id"]))
        return None

    await job_runner.process_due({"ITEM_RESEARCH": handle})

    return JSONResponse(status_code=202, content={"job_id": job_id, "item_id": item_id})
