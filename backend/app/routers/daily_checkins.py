from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.daily_checkin import DailyCheckIn
from app.models.user import User
from app.schemas.daily_checkin import (
    DailyCheckInCreate,
    DailyCheckInResponse,
    DailyCheckInUpdate,
)


router = APIRouter(
    prefix="/daily-checkins",
    tags=["Daily Check-ins"],
)


def get_user_checkin_or_404(
    checkin_id: int,
    user_id: int,
    db: Session,
) -> DailyCheckIn:
    checkin = (
        db.query(DailyCheckIn)
        .filter(
            DailyCheckIn.id == checkin_id,
            DailyCheckIn.user_id == user_id,
        )
        .first()
    )

    if checkin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Daily check-in not found.",
        )

    return checkin


@router.post("/", response_model=DailyCheckInResponse)
def create_or_update_daily_checkin(
    checkin_data: DailyCheckInCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    existing_checkin = (
        db.query(DailyCheckIn)
        .filter(
            DailyCheckIn.user_id == current_user.id,
            DailyCheckIn.checkin_date == checkin_data.checkin_date,
        )
        .first()
    )

    if existing_checkin:
        existing_checkin.mood_score = checkin_data.mood_score
        existing_checkin.energy_score = checkin_data.energy_score
        existing_checkin.focus_score = checkin_data.focus_score
        existing_checkin.stress_score = checkin_data.stress_score
        existing_checkin.sleep_quality_score = checkin_data.sleep_quality_score
        existing_checkin.note = checkin_data.note

        db.commit()
        db.refresh(existing_checkin)

        return existing_checkin

    checkin = DailyCheckIn(
        user_id=current_user.id,
        checkin_date=checkin_data.checkin_date,
        mood_score=checkin_data.mood_score,
        energy_score=checkin_data.energy_score,
        focus_score=checkin_data.focus_score,
        stress_score=checkin_data.stress_score,
        sleep_quality_score=checkin_data.sleep_quality_score,
        note=checkin_data.note,
    )

    db.add(checkin)
    db.commit()
    db.refresh(checkin)

    return checkin


@router.get("/today", response_model=DailyCheckInResponse | None)
def get_today_checkin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    today = date.today()

    checkin = (
        db.query(DailyCheckIn)
        .filter(
            DailyCheckIn.user_id == current_user.id,
            DailyCheckIn.checkin_date == today,
        )
        .first()
    )

    return checkin


@router.get("/", response_model=list[DailyCheckInResponse])
def get_daily_checkins(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = db.query(DailyCheckIn).filter(DailyCheckIn.user_id == current_user.id)

    if start_date is not None:
        query = query.filter(DailyCheckIn.checkin_date >= start_date)

    if end_date is not None:
        query = query.filter(DailyCheckIn.checkin_date <= end_date)

    checkins = query.order_by(DailyCheckIn.checkin_date.desc()).all()

    return checkins


@router.get("/{checkin_id}", response_model=DailyCheckInResponse)
def get_daily_checkin(
    checkin_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    checkin = get_user_checkin_or_404(
        checkin_id=checkin_id,
        user_id=current_user.id,
        db=db,
    )

    return checkin


@router.put("/{checkin_id}", response_model=DailyCheckInResponse)
def update_daily_checkin(
    checkin_id: int,
    checkin_data: DailyCheckInUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    checkin = get_user_checkin_or_404(
        checkin_id=checkin_id,
        user_id=current_user.id,
        db=db,
    )

    update_data = checkin_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(checkin, field, value)

    db.commit()
    db.refresh(checkin)

    return checkin


@router.delete("/{checkin_id}")
def delete_daily_checkin(
    checkin_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    checkin = get_user_checkin_or_404(
        checkin_id=checkin_id,
        user_id=current_user.id,
        db=db,
    )

    db.delete(checkin)
    db.commit()

    return {
        "message": "Daily check-in deleted successfully.",
    }