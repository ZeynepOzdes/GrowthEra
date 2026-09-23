from sqlalchemy.orm import Session

from app.models.garden_v2 import (
    DailyAirRewardSchedule,
    GardenRewardObject,
)
from app.models.life_area import LifeArea


DEFAULT_LIFE_AREAS = [
    {
        "name": "Coding",
        "slug": "coding",
        "description": "Improve programming and software development skills.",
        "icon": "code",
    },
    {
        "name": "Study",
        "slug": "study",
        "description": "Track academic learning, courses, and exam preparation.",
        "icon": "book-open",
    },
    {
        "name": "Fitness",
        "slug": "fitness",
        "description": "Build physical strength, movement, and exercise consistency.",
        "icon": "activity",
    },
    {
        "name": "Reading",
        "slug": "reading",
        "description": "Track books, pages, reading time, and learning notes.",
        "icon": "book",
    },
    {
        "name": "Sleep",
        "slug": "sleep",
        "description": "Improve sleep schedule, sleep quality, and recovery.",
        "icon": "moon",
    },
    {
        "name": "Finance",
        "slug": "finance",
        "description": "Track savings, spending awareness, and financial goals.",
        "icon": "wallet",
    },
    {
        "name": "Mindset",
        "slug": "mindset",
        "description": "Support reflection, emotional awareness, and personal discipline.",
        "icon": "brain",
    },
    {
        "name": "Language Learning",
        "slug": "language-learning",
        "description": "Track vocabulary, practice sessions, and language progress.",
        "icon": "languages",
    },
    {
        "name": "Productivity",
        "slug": "productivity",
        "description": "Improve focus, planning, time management, and execution.",
        "icon": "target",
    },
    {
        "name": "Digital Discipline",
        "slug": "digital-discipline",
        "description": "Understand and reduce distracting digital behavior.",
        "icon": "monitor",
    },
]


DEFAULT_AIR_REWARD_OBJECTS = [
    {
        "code": "bench",
        "name": "Garden Bench",
        "object_subtype": "bench",
        "description": "A quiet place to pause and enjoy the garden.",
    },
    {
        "code": "table",
        "name": "Garden Table",
        "object_subtype": "table",
        "description": "A small table for creative moments in the garden.",
    },
    {
        "code": "torch",
        "name": "Garden Torch",
        "object_subtype": "torch",
        "description": "A warm light earned through inspiration.",
    },
    {
        "code": "paper_plane",
        "name": "Paper Plane",
        "object_subtype": "paper_plane",
        "description": "A playful symbol of curiosity and imagination.",
    },
    {
        "code": "wind_chime",
        "name": "Wind Chime",
        "object_subtype": "wind_chime",
        "description": "A gentle decoration inspired by mindful joy.",
    },
    {
        "code": "inspiration_spark",
        "name": "Inspiration Spark",
        "object_subtype": "spark",
        "description": "A small spark awarded when no daily reward is scheduled.",
    },
]


DEFAULT_AIR_REWARD_SCHEDULE = [
    {"journey_day": 1, "reward_code": "bench"},
    {"journey_day": 2, "reward_code": "table"},
    {"journey_day": 3, "reward_code": "torch"},
    {"journey_day": 4, "reward_code": "paper_plane"},
    {"journey_day": 5, "reward_code": "wind_chime"},
]


def seed_default_life_areas(db: Session) -> None:
    for area_data in DEFAULT_LIFE_AREAS:
        existing_area = (
            db.query(LifeArea)
            .filter(LifeArea.slug == area_data["slug"])
            .first()
        )

        if existing_area:
            continue

        life_area = LifeArea(
            name=area_data["name"],
            slug=area_data["slug"],
            description=area_data["description"],
            icon=area_data["icon"],
            is_default=True,
        )

        db.add(life_area)

    db.commit()


def seed_default_air_rewards(db: Session) -> None:
    reward_objects_by_code: dict[str, GardenRewardObject] = {}

    for reward_data in DEFAULT_AIR_REWARD_OBJECTS:
        reward_object = (
            db.query(GardenRewardObject)
            .filter(GardenRewardObject.code == reward_data["code"])
            .first()
        )

        if reward_object is None:
            reward_object = GardenRewardObject(
                code=reward_data["code"],
                name=reward_data["name"],
                element_type="air",
                object_type="decoration",
                object_subtype=reward_data["object_subtype"],
                description=reward_data["description"],
                is_active=True,
            )

            db.add(reward_object)
            db.flush()

        reward_objects_by_code[reward_data["code"]] = reward_object

    for schedule_data in DEFAULT_AIR_REWARD_SCHEDULE:
        existing_schedule = (
            db.query(DailyAirRewardSchedule)
            .filter(
                DailyAirRewardSchedule.journey_day
                == schedule_data["journey_day"]
            )
            .first()
        )

        if existing_schedule is not None:
            continue

        reward_object = reward_objects_by_code[schedule_data["reward_code"]]

        schedule = DailyAirRewardSchedule(
            journey_day=schedule_data["journey_day"],
            reward_object_id=reward_object.id,
            is_active=True,
        )

        db.add(schedule)

    db.commit()