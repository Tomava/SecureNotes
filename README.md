## Installation

Requirements:
- Docker
- Docker compose

## Usage

Rename `.env.template` to `.env` in root dir.

**Default values in .env.template are for demoing only and should be changed if running in production!**

Run in root dir:
```sh
docker compose up --build
```

## Development

This will allow to run frontend and backend without docker:

### Backend
```sh
cd backend
sudo rm -rf db-data
docker compose up db --build -d
export DB_PORT=5431 && export DB_HOST=localhost && export ENVIRONMENT=dev && python3 main.py
```

To view database data:
```sh
docker exec -it backend-db-1 psql -U secure_notes_user -d secure_notes
```

### Frontend
```sh
cd frontend
npm install
npm run dev
```
