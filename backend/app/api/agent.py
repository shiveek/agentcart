from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.agent.agent_service import run_commerce_agent
from app.db.session import get_db
from app.schemas.agent import AgentChatRequest, AgentChatResponse

router = APIRouter(prefix="/agent", tags=["AI Commerce Agent"])


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Interact with AI Commerce Agent",
    description=(
        "Executes natural language commerce tasks through autonomous structured agent tools, "
        "enforcing inventory checks, server-side pricing, and pure Policy Engine governance."
    ),
)
def agent_chat(
    request: AgentChatRequest,
    db: Session = Depends(get_db),
) -> AgentChatResponse:
    """Agent chat endpoint."""
    return run_commerce_agent(db, request)
