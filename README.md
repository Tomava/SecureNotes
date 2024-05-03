## Installation

Requirements:
- Docker
- Docker compose

### Install

Copy `.env.template` to `.env` in `backend` dir:

```sh
cp backend/.env.template backend/.env
```

**Default values in .env.template are for demoing only and should be changed if running in production!**

## Usage

### Setup

Build backend and frontend with Docker Compose:

```sh
cd backend
docker compose up --build -d
cd ../frontend
docker compose up --build -d
cd ..
```

Frontend is now accessible in `localhost:3000`.

### Tear down

Stop and remove containers with:

```sh
cd backend
docker compose down
cd ../frontend
docker compose down
cd ..
```

## Development

This will allow to run frontend and backend in development mode with hot reload:

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

## Testing

Tests are run with containers.

### Backend

```sh
cd backend
docker compose -f docker-compose-tests.yaml up --build -d && docker logs backend-tester-1 -f
# Shut down after running
docker compose -f docker-compose-tests.yaml down
```
