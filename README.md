# YourLifeStory
Web Hub for Personal Internet
---
This is a dedicated space accessible from any device that can run web browser that you can use to store your thoughts, research with a comfort of control over your data.

You can refer to [security policy](SECURITY.md) to learn how to report about vulnerabilities, which versions of the project will receive security updates etc.

## Features
### Publications :construction:
Publications - keep your research structured: write, edit your articles and manage sources.

### Journal :construction:
The home of your thoughts. Write about your daily life, your feelings, your thoughts, your experiences.

### Feed :construction:
Keep your feed truly yours. Invite family members to the Hub and have a feed that built around your close community rather than a global audience.

### Events :construction:
Plan your events and share them with your community.

### Family Tree :construction:
Manage information about your close relatives regardless of their location. Get their important dates right up to your dashboard.

## Tech Stack
Django – Python Web Framework
PostgreSQL – Database
Docker – Containerization

## Database
This project uses PostgreSQL only.

- Docker persists PostgreSQL data in `./.docker/postgres/data`.
- Create a project `.env` from `.env.example` before running Django.
- Host-side Django commands load PostgreSQL settings from the project `.env`.
- Set `POSTGRES_HOST=localhost` in `.env` for host-run Django commands.
- The Docker Compose app container overrides `POSTGRES_HOST` to `database`.
- This keeps one shared PostgreSQL dataset across Docker restarts and when switching between Dockerized and host-run Django processes.
- Missing PostgreSQL variables now fail fast during Django startup instead of falling back to implicit credentials.
