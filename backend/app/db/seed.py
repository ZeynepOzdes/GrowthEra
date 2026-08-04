from sqlalchemy.orm import Session

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