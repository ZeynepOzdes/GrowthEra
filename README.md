# GrowthEra

GrowthEra is an AI-powered personal growth, goal tracking, habit tracking, and productivity analysis platform.

## Purpose

GrowthEra helps users build a structured personal growth system based on goals, habits, daily reflection, productivity data, and AI-powered insights.

GrowthEra does not guarantee personal transformation. Instead, it provides tools that support self-awareness, consistency, and better decision-making.

## Tech Stack

- Python
- FastAPI
- Microsoft SQL Server
- SQLAlchemy
- Docker
- Docker Compose
- JWT Authentication
- AI integration planned

## Project Structure

```text
GrowthEra/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── db/
│   │   ├── dependencies/
│   │   ├── models/
│   │   ├── routers/
│   │   └── schemas/
│   ├── requirements.txt
│   └── .env.example
├── docker-compose.yml
└── README.md

MSSQL container'ını başlatmak için:

```bash
docker compose up -d