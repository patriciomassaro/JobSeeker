# JobSeeker

## Technology Stack and Features

- ⚡ [**FastAPI**](https://fastapi.tiangolo.com) for the Python backend API.
    - 🧰 [SQLModel](https://sqlmodel.tiangolo.com) for the Python SQL database interactions (ORM).
    - 🔍 [Pydantic](https://docs.pydantic.dev), used by FastAPI, for the data validation and settings management.
    - 💾 [PostgreSQL](https://www.postgresql.org) as the SQL database.
- 🚀 [React](https://react.dev) for the frontend.
    - 💃 Using TypeScript, hooks, Vite, and other parts of a modern frontend stack.
    - 🎨 [Chakra UI](https://chakra-ui.com) for the frontend components.
    - 🤖 An automatically generated frontend client.
    - 🦇 Dark mode support.
- 🐋 [Docker Compose](https://www.docker.com) for development and production.
- 🔒 Secure password hashing by default.
- 🔑 JWT token authentication.
- 📫 Email based password recovery.
- ✅ Tests with [Pytest](https://pytest.org).
- 📞 [Traefik](https://traefik.io) as a reverse proxy / load balancer.
- 🚢 Deployment instructions using Docker Compose, including how to set up a frontend Traefik proxy to handle automatic HTTPS certificates.
- 🏭 CI (continuous integration) and CD (continuous deployment) based on GitHub Actions.

## Starting

### Configure env variables

You can update the configs in the `.env` files to customize your configurations.


Before deploying it, make sure you change at least the values for:

- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- RABBITMQ_HOST
- RABBITMQ_PORT="5672"
- RABBITMQ_DEFAULT_USER
- RABBITMQ_DEFAULT_PASS
- POSTGRES_SERVER=db
- POSTGRES_DB=app
- POSTGRES_PORT="5432"
- POSTGRES_USER
- POSTGRES_PASSWORD
- SECRET_KEY
- FIRST_SUPERUSER_PASSWORD

>**Note** For local development, add these variables to your workstation environment variables.

> **In deployment**: You can (and should) pass these as environment variables from secrets. Read the [deployment.md](./deployment.md) docs for more details.

### Building and running the docker images

To build the docker images , move to the repo folder and run

```bash
docker-compose build
```

then run:

```bash
docker-compose up -d
```

### Available services

> - Frontend: http://localhost
> - Backend: http://localhost/api/
> - API Documentation: http://localhost/docs
> - Traefik UI, to see how the routes are being handled by the proxy: http://localhost:8090


### Turning off and deleting docker containers

```bash
docker-compose down
```

If you want to also delete the local database data

```bash
docker-compose down -v
```


## Backend 

Backend docs: [backend/README.md](./backend/README.md).

## Frontend 

Frontend docs: [frontend/README.md](./frontend/README.md).

## Deployment

Deployment docs: [deployment.md](./deployment.md).

## Development

General development docs: [development.md](./development.md).

This includes using Docker Compose, custom local domains, `.env` configurations, etc.

## Release Notes

Check the file [release-notes.md](./release-notes.md).

## License

The Full Stack FastAPI Template is licensed under the terms of the MIT license.
