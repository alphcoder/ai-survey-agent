from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from ..database import get_db
from ..models import Survey, SurveyStatus, InterviewSession

router = APIRouter(prefix="/surveys", tags=["surveys"])


class SurveyCreate(BaseModel):
    title: str
    description: str | None = None
    goal: str
    target_audience: str | None = None
    max_questions: int = 10
    system_prompt: str | None = None


class SurveyUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    goal: str | None = None
    status: SurveyStatus | None = None
    max_questions: int | None = None


@router.get("")
async def list_surveys(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Survey).order_by(Survey.created_at.desc()))
    surveys = result.scalars().all()

    items = []
    for s in surveys:
        count = await db.execute(
            select(func.count(InterviewSession.id)).where(InterviewSession.survey_id == s.id)
        )
        items.append({
            "id": str(s.id),
            "title": s.title,
            "goal": s.goal,
            "status": s.status,
            "sessions_count": count.scalar(),
            "created_at": s.created_at.isoformat(),
        })
    return items


@router.post("")
async def create_survey(data: SurveyCreate, db: AsyncSession = Depends(get_db)):
    survey = Survey(**data.model_dump())
    db.add(survey)
    await db.commit()
    await db.refresh(survey)
    return {"id": str(survey.id)}


@router.get("/{survey_id}")
async def get_survey(survey_id: UUID, db: AsyncSession = Depends(get_db)):
    survey = await db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(404, "Survey not found")
    return survey


@router.put("/{survey_id}")
async def update_survey(survey_id: UUID, data: SurveyUpdate, db: AsyncSession = Depends(get_db)):
    survey = await db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(404, "Survey not found")
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(survey, key, value)
    await db.commit()
    return {"ok": True}


@router.get("/{survey_id}/analytics")
async def get_analytics(survey_id: UUID, db: AsyncSession = Depends(get_db)):
    sessions = await db.execute(
        select(InterviewSession).where(
            InterviewSession.survey_id == survey_id,
            InterviewSession.status == "completed",
        )
    )
    completed = sessions.scalars().all()

    all_insights = []
    sentiments = []
    for s in completed:
        if s.insights:
            all_insights.extend(s.insights.get("key_insights", []))
            sentiments.append(s.insights.get("sentiment", "neutral"))

    return {
        "total_sessions": len(completed),
        "sentiments": {s: sentiments.count(s) for s in set(sentiments)},
        "top_insights": all_insights[:20],
    }
