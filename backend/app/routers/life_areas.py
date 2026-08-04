from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.life_area import LifeArea, UserArea
from app.models.user import User
from app.schemas.life_area import LifeAreaResponse, UserAreaResponse


router = APIRouter(
    prefix="/life-areas",
    tags=["Life Areas"],
)


@router.get("/", response_model=list[LifeAreaResponse])
def get_life_areas(db: Session = Depends(get_db)):
    life_areas = db.query(LifeArea).order_by(LifeArea.name.asc()).all()
    return life_areas


@router.get("/my", response_model=list[LifeAreaResponse])
def get_my_life_areas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    life_areas = (
        db.query(LifeArea)
        .join(UserArea, UserArea.life_area_id == LifeArea.id)
        .filter(
            UserArea.user_id == current_user.id,
            UserArea.is_active == True,
        )
        .order_by(LifeArea.name.asc())
        .all()
    )

    return life_areas


@router.post("/{life_area_id}/select", response_model=UserAreaResponse)
def select_life_area(
    life_area_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    life_area = db.query(LifeArea).filter(LifeArea.id == life_area_id).first()

    if life_area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Life area not found.",
        )

    existing_user_area = (
        db.query(UserArea)
        .filter(
            UserArea.user_id == current_user.id,
            UserArea.life_area_id == life_area_id,
        )
        .first()
    )

    if existing_user_area:
        if existing_user_area.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Life area is already selected.",
            )

        existing_user_area.is_active = True
        db.commit()
        db.refresh(existing_user_area)

        return existing_user_area

    user_area = UserArea(
        user_id=current_user.id,
        life_area_id=life_area_id,
        is_active=True,
    )

    db.add(user_area)
    db.commit()
    db.refresh(user_area)

    return user_area


@router.delete("/{life_area_id}/select")
def unselect_life_area(
    life_area_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    user_area = (
        db.query(UserArea)
        .filter(
            UserArea.user_id == current_user.id,
            UserArea.life_area_id == life_area_id,
            UserArea.is_active == True,
        )
        .first()
    )

    if user_area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected life area not found.",
        )

    user_area.is_active = False
    db.commit()

    return {
        "message": "Life area unselected successfully.",
    }