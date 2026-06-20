from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from ..database import get_db
from ..models import Survey, InterviewSession, Message
from ..agents.interviewer import generate_question, generate_summary

router = APIRouter(prefix="/interviews", tags=["interviews"])


class StartInterview(BaseModel):
    survey_id: str
    respondent_name: str | None = None


class SendMessage(BaseModel):
    content: str


@router.post("/start")
async def start_interview(data: StartInterview, db: AsyncSession = Depends(get_db)):
    survey = await db.get(Survey, UUID(data.survey_id))
    if not survey:
        raise HTTPException(404, "Survey not found")

    session = InterviewSession(
        survey_id=survey.id,
        respondent_name=data.respondent_name,
    )
    db.add(session)
    await db.flush()

    first_question = await generate_question(
        goal=survey.goal,
        history=[],
        max_questions=survey.max_questions,
        custom_prompt=survey.system_prompt,
    )

    msg = Message(session_id=session.id, role="assistant", content=first_question)
    db.add(msg)
    await db.commit()

    return {
        "session_id": str(session.id),
        "message": first_question,
    }


@router.post("/{session_id}/message")
async def send_message(session_id: UUID, data: SendMessage, db: AsyncSession = Depends(get_db)):
    session = await db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if session.status != "in_progress":
        raise HTTPException(400, "Interview already finished")

    survey = await db.get(Survey, session.survey_id)

    user_msg = Message(session_id=session.id, role="user", content=data.content)
    db.add(user_msg)

    msgs_result = await db.execute(
        select(Message).where(Message.session_id == session.id).order_by(Message.created_at)
    )
    messages = msgs_result.scalars().all()
    history = [{"role": m.role, "content": m.content} for m in messages]
    history.append({"role": "user", "content": data.content})

    question_count = len([m for m in history if m["role"] == "assistant"])

    if question_count >= survey.max_questions:
        summary_data = await generate_summary(goal=survey.goal, history=history)
        session.status = "completed"
        session.finished_at = datetime.utcnow()
        session.summary = summary_data.get("summary", "")
        session.insights = summary_data
        await db.commit()

        return {
            "message": "Спасибо за участие! Интервью завершено.",
            "finished": True,
            "summary": summary_data,
        }

    ai_response = await generate_question(
        goal=survey.goal,
        history=history,
        max_questions=survey.max_questions,
        custom_prompt=survey.system_prompt,
    )

    ai_msg = Message(session_id=session.id, role="assistant", content=ai_response)
    db.add(ai_msg)
    await db.commit()

    return {
        "message": ai_response,
        "finished": False,
        "questions_remaining": survey.max_questions - question_count - 1,
    }


@router.get("/{session_id}")
async def get_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    session = await db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    msgs = await db.execute(
        select(Message).where(Message.session_id == session.id).order_by(Message.created_at)
    )

    return {
        "id": str(session.id),
        "status": session.status,
        "respondent_name": session.respondent_name,
        "summary": session.summary,
        "insights": session.insights,
        "messages": [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in msgs.scalars()],
    }
