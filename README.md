# JobSeeker

JobSeeker is a LLM-powered full-stack application designed to assist users in their job search process. It leverages modern technologies to provide features like job posting aggregation, resume and cover letter generation tailored to specific job descriptions, and comparison tools to help users identify the best opportunities. The system relies **heavily** on user feedback, the modifications that you make to the LLM generated text is then used to guide future text generation.  The backend is powered by FastAPI, while the frontend is built with React and TypeScript.

## Table of Contents

1.  [Overview](https://www.google.com/search?q=%23overview)
2.  [Technology Stack and Features](https://www.google.com/search?q=%23technology-stack-and-features)
3.  [Directory Structure](https://www.google.com/search?q=%23directory-structure)
4.  [Setup and Installation](https://www.google.com/search?q=%23setup-and-installation)
      * [Prerequisites](https://www.google.com/search?q=%23prerequisites)
      * [Environment Variables](https://www.google.com/search?q=%23environment-variables)
      * [Building and Running with Docker](https://www.google.com/search?q=%23building-and-running-with-docker)
      * [Available Services](https://www.google.com/search?q=%23available-services)
      * [Stopping Docker Containers](https://www.google.com/search?q=%23stopping-docker-containers)
5.  [Backend Development](https://www.google.com/search?q=%23backend-development)
      * [Dependency Management (Poetry)](https://www.google.com/search?q=%23dependency-management-poetry)
      * [Testing](https://www.google.com/search?q=%23testing)
      * [Linting and Formatting (Backend)](https://www.google.com/search?q=%23linting-and-formatting-backend)
      * [Database Migrations (Alembic)](https://www.google.com/search?q=%23database-migrations-alembic)
      * [Key Backend Modules](https://www.google.com/search?q=%23key-backend-modules)
6.  [Frontend Development](https://www.google.com/search?q=%23frontend-development)
      * [Node.js Version Management](https://www.google.com/search?q=%23nodejs-version-management)
      * [Dependency Management (NPM)](https://www.google.com/search?q=%23dependency-management-npm)
      * [Running the Frontend Dev Server](https://www.google.com/search?q=%23running-the-frontend-dev-server)
      * [Generating OpenAPI Client](https://www.google.com/search?q=%23generating-openapi-client)
      * [Linting and Formatting (Frontend)](https://www.google.com/search?q=%23linting-and-formatting-frontend)
      * [Key Frontend Components and Structure](https://www.google.com/search?q=%23key-frontend-components-and-structure)
7.  [Docker Configuration](https://www.google.com/search?q=%23docker-configuration)
8.  [API Documentation](https://www.google.com/search?q=%23api-documentation)
9.  [Deployment](https://www.google.com/search?q=%23deployment)
10. [License](https://www.google.com/search?q=%23license)

## Overview

JobSeeker aims to streamline the job application process by:

  * Scraping and aggregating job postings from platforms like LinkedIn.
  * Allowing users to upload their resumes and parse them using Large Language Models (LLMs).
  * Generating tailored work experiences and cover letter paragraphs based on user profiles and specific job descriptions.
  * Allowing the user to modify the text provided by LLM, and using that feedback for future iterations.
  * Building complete, customized resumes and cover letters in PDF format using LaTeX templates.

## Technology Stack and Features

  * ⚡ **FastAPI** for the Python backend API.
      * 🧰 **SQLModel** for Python SQL database interactions (ORM).
      * 🔍 **Pydantic**, used by FastAPI, for data validation and settings management.
      * 💾 **PostgreSQL** as the SQL database.
      * 🤖 **LLM Integration** (OpenAI, Anthropic) for resume parsing, job description summarization, and content generation.
      * 🕷️ **Web Scraping** capabilities for job postings and company information (primarily LinkedIn).
      * 📄 **LaTeX PDF Generation** for resumes and cover letters.
  * 🚀 **React** for the frontend.
      * 💃 Using TypeScript, hooks, Vite, and other parts of a modern frontend stack.
      * 🎨 **Chakra UI** for frontend components.
      * 🤖 An automatically generated frontend client via OpenAPI.
      * 🦇 Dark mode support.
  * 🐋 **Docker Compose** for development and production.
  * ✅ Tests with **Pytest** (backend).
  * 📞 **Traefik** as a reverse proxy / load balancer.
  * 🚢 Docker compose
  * 🏭 CI (continuous integration) and CD (continuous deployment) based on GitHub Actions (implied by workflow files, not directly provided).
  * 🛠️ **Pre-commit hooks** for code quality.

## Directory Structure

The project is organized into the following main directories:

```
.
├── backend/            # FastAPI backend application
│   ├── app/            # Core application code
│   │   ├── alembic/    # Alembic database migration scripts
│   │   ├── api/        # API endpoint definitions and routing
│   │   ├── core/       # Core logic (config, DB, security)
│   │   ├── crud/       # CRUD operations for database models
│   │   ├── llm/        # Large Language Model integration
│   │   ├── logger/     # Custom logging setup
│   │   ├── scraper/    # Web scraping utilities
│   │   ├── templates/  # LaTeX templates for PDF generation
│   │   ├── models.py   # SQLModel definitions
│   │   └── main.py     # FastAPI application entry point
│   ├── scripts/        # Utility scripts (format, lint, test)
│   ├── Dockerfile
│   └── alembic.ini     # Alembic configuration
├── frontend/           # React frontend application
│   ├── src/            # Source code
│   │   ├── assets/     # Static assets (icons, images)
│   │   ├── client/     # Auto-generated API client
│   │   ├── components/ # React components
│   │   ├── hooks/      # Custom React hooks
│   │   ├── routes/     # TanStack Router route definitions
│   │   ├── main.tsx    # Frontend application entry point
│   │   └── theme.tsx   # Chakra UI theme customization
│   ├── Dockerfile
│   └── package.json    # NPM dependencies and scripts
├── infrastructure/     # Cloud deployment resources (e.g., CloudFormation)
│   └── network-resources.yml
├── .env                # Environment variables for configuration
├── docker-compose.yml  # Main Docker Compose configuration
├── docker-compose.override.yml # Local development Docker Compose overrides
├── docker-compose.traefik.yml # Traefik specific Docker Compose configuration
├── README.md           # This file
└── LICENSE
```

## Setup and Installation

### Prerequisites

  * **Docker & Docker Compose**: Essential for running the application services. ([Install Docker](https://www.docker.com/))
  * **Poetry**: For Python package and environment management in the backend. ([Install Poetry](https://python-poetry.org/))
  * **Node.js and NPM**: For frontend development. It's recommended to use a Node version manager like `nvm` or `fnm`. The project specifies Node.js version 20 in `frontend/.nvmrc`.
      * Install `fnm`: [Official fnm guide](https://github.com/Schniz/fnm#installation)
      * Install `nvm`: [Official nvm guide](https://github.com/nvm-sh/nvm#installing-and-updating)

### Environment Variables

Configuration is managed via a `.env` file in the project root. Create this file by copying `.env.example` (if provided, otherwise create it based on the variables listed below) and customize the values.

Key variables to configure (see `.env` for a full list):

  * `DOMAIN`: The domain for the application (e.g., `localhost` for local development).
  * `ENVIRONMENT`: Set to `local`, `dev`, or `production`.
  * `PROJECT_NAME`: Name of the project (e.g., "Job Seeker").
  * `STACK_NAME`: Stack name used for Docker service labeling (e.g., `job-seeker`).
  * `BACKEND_CORS_ORIGINS`: Comma-separated list of allowed CORS origins for the backend.
  * `SECRET_KEY`: A strong, unique secret key for security purposes. **Change this from the default.**
  * `FIRST_SUPERUSER`: Email for the first superuser account.
  * `FIRST_SUPERUSER_NAME`: Name of the first superuser.
  * `FIRST_SUPERUSER_PASSWORD`: Password for the first superuser. **Change this from the default.**
  * `DB_INSTANCE`: Docker service name for the PostgreSQL database (e.g., `db`).
  * `DB_PORT`: Port for the PostgreSQL database (e.g., `5432`).
  * `DB_NAME`: Name of the PostgreSQL database (e.g., `app`).
  * `DB_USER`: PostgreSQL username (e.g., `postgres`).
  * `DB_PASSWORD`: PostgreSQL password. **Change this from the default.**
  * `OPENAI_API_KEY`: API key for OpenAI services.
  * `ANTHROPIC_API_KEY`: API key for Anthropic services.
  * `DOCKER_IMAGE_BACKEND`: Name for the backend Docker image (e.g., `backend`).
  * `DOCKER_IMAGE_FRONTEND`: Name for the frontend Docker image (e.g., `frontend`).
  * `TAG`: Docker image tag (e.g., `latest`).

**For local development**, these variables are typically sourced from the `.env` file.
**In deployment**, these should be passed as environment variables from secrets.

### Building and Running with Docker

1.  **Build the Docker images**:
    Navigate to the project's root directory and run:

    ```bash
    docker-compose build
    ```

2.  **Start the services**:

    ```bash
    docker-compose up -d
    ```

    This command starts all services defined in `docker-compose.yml` and `docker-compose.override.yml` in detached mode.

### Available Services

Once the Docker containers are running, the following services will be available:

  * **Frontend**: `http://localhost` (or your configured `DOMAIN`)
  * **Backend API**: `http://localhost/api/v1/`
  * **API Documentation (Swagger UI)**: `http://localhost/docs`
  * **Alternative API Documentation (ReDoc)**: `http://localhost/redoc`
  * **Traefik Dashboard** (for local development, via `docker-compose.override.yml`): `http://localhost:8090`

### Stopping Docker Containers

  * To stop all running services:
    ```bash
    docker-compose down
    ```
  * To stop services and remove associated volumes (including database data):
    ```bash
    docker-compose down -v
    ```

## Backend Development

The backend is a FastAPI application. Refer to `backend/README.md` for more detailed instructions specific to backend development.

### Dependency Management (Poetry)

Backend Python dependencies are managed using Poetry.

1.  **Navigate to the backend directory**:
    ```bash
    cd backend
    ```
2.  **Install dependencies**:
    ```bash
    poetry install
    ```
    This will install dependencies listed in `pyproject.toml`. To include development dependencies: `poetry install --with dev`.
3.  **Activate the virtual environment**:
    ```bash
    poetry shell
    ```
    Ensure your editor uses this Poetry-managed virtual environment.

### Testing

Backend tests are written using Pytest.

  * **Run tests**:
    From the `backend` directory:
    ```bash
    bash ./scripts/test.sh
    ```
    This script executes tests, shows missing coverage, and generates an HTML coverage report in `backend/htmlcov/index.html`.
  * **Run tests on an already running stack**:
    ```bash
    docker compose exec backend bash /app/tests-start.sh
    ```
    You can pass Pytest arguments to this script, e.g., `docker compose exec backend bash /app/tests-start.sh -x` to stop on the first error.
    The `tests-start.sh` script internally uses `app/tests_pre_start.py` to ensure the database is ready.

### Linting and Formatting (Backend)

  * **Ruff** is used for linting and formatting.

  * **Mypy** is used for static type checking.

    From the `backend` directory:

  * **Check and fix linting/formatting issues**:

    ```bash
    bash ./scripts/format.sh
    ```

  * **Run linters and type checker**:

    ```bash
    bash ./scripts/lint.sh
    ```

    Configuration for Ruff and Mypy can be found in `backend/pyproject.toml`.

### Database Migrations (Alembic)

Database schema changes are managed using Alembic. Migration scripts are located in `backend/app/alembic/versions/`.

1.  **Start an interactive session in the backend container**:
    ```bash
    docker compose exec backend bash
    ```
2.  **After modifying SQLModel models** (in `backend/app/models.py`), create a new migration revision:
    ```bash
    alembic revision --autogenerate -m "Your descriptive migration message"
    ```
    This will generate a new migration script in the `versions` directory. Commit this script to your Git repository.
3.  **Apply the migration to the database**:
    ```bash
    alembic upgrade head
    ```
    Alembic configuration is in `backend/alembic.ini`, and the environment setup for migrations is in `backend/app/alembic/env.py`.

### Key Backend Modules

  * **`backend/app/main.py`**: The entry point for the FastAPI application. It initializes the app, configures CORS middleware, and includes the main API router. Uses a custom function `custom_generate_unique_id` for OpenAPI operation IDs based on tags and route names.
  * **`backend/app/core/config.py`**: Defines application settings using Pydantic's `BaseSettings`, loading values from environment variables and the `.env` file. Includes computed fields for database URI and server host.
  * **`backend/app/core/db.py`**: Sets up the SQLAlchemy engine (`engine`) and a session maker (`SessionLocal`). Includes `init_db` function to create initial data (superuser, enum values, sample job postings from `job_posting_initial_data.json`) and the `pg_trgm` extension for text similarity searches.
  * **`backend/app/core/security.py`**: Provides utility functions for password hashing (`get_password_hash`, `verify_password`) and JWT access token creation (`create_access_token`).
  * **`backend/app/api/main.py`**: Consolidates all API routers from `backend/app/api/routes/` under the `/api/v1` prefix.
  * **`backend/app/api/routes/`**: Contains individual router modules for different API resources:
      * `login.py`: Handles user authentication and token generation.
      * `users.py`: Manages user creation, updates (including password and resume upload), and retrieval. Includes an endpoint to parse uploaded resumes using LLMs.
      * `job_postings.py`: Endpoints for retrieving job postings (with similarity search), creating new job postings, and triggering LLM-based extraction of details from job posting descriptions.
      * `comparisons.py`: Endpoints related to job comparisons, including creating/activating comparisons, generating tailored work experiences and cover letter paragraphs using LLMs, building resume/cover letter PDFs, and editing generated content.
      * `dimensions.py`: Provides endpoints to fetch predefined dimension data like model names, seniority levels, remote modalities, experience levels, and institution sizes.
  * **`backend/app/api/deps.py`**: Defines FastAPI dependencies for database sessions (`SessionDep`) and current authenticated user (`CurrentUser`).
  * **`backend/app/api/decorators.py`**: Contains custom decorators, such as `require_positive_balance` to restrict access to certain features based on user balance.
  * **`backend/app/models.py`**: Defines all SQLModel data models, which serve as both Pydantic models for API validation and SQLAlchemy models for database tables. This includes `Users`, `JobPostings`, `Institutions`, `Comparisons`, `WorkExperiences`, `CoverLetterParagraphs`, LLM transaction logs, balance transactions, and various dimension/enum tables.
  * **`backend/app/crud/`**: Contains Create, Read, Update, Delete operations for database models.
      * `users.py`: Functions for creating, authenticating, and updating users, and managing user balances.
      * `job_postings.py`: Functions to retrieve job postings (including similarity search), create job postings, and fetch detailed job posting information by joining multiple tables.
      * `comparisons.py`: Functions for managing user-job comparisons, including fetching active comparisons, ordering work experiences/cover letter paragraphs, creating examples of edited content, and creating new comparisons.
  * **`backend/app/llm/`**: Modules for interacting with Large Language Models.
      * `__init__.py` (LLMInitializer, TransactionManager): Initializes LLM clients (OpenAI, Anthropic) based on configuration and manages LLM transaction logging and user balance deduction.
      * `base_extractor.py` (BaseLLMExtractor): A base class for LLM-based data extraction, taking a Pydantic model schema to guide extraction.
      * `base_generator.py` (BaseGenerator, CustomJSONParser): A base class for generating content using LLMs, with methods to fetch comparison data and parse LLM responses into Pydantic models.
      * `base_builder.py` (BasePDFBuilder): A base class for generating PDF documents from LaTeX templates.
      * `resume_data_extractor.py` (ResumeLLMExtractor): Extracts structured data (personal info, work experience, education, skills, languages) from user-uploaded resume PDFs.
      * `job_posting_extractor.py` (JobDescriptionLLMExtractor): Extracts detailed, structured information from job posting text.
      * `work_experience_generator.py` (WorkExperienceGenerator): Generates tailored work experience bullet points based on user's resume and a target job description.
      * `cover_letter_generator.py` (CoverLetterGenerator): Generates tailored cover letter paragraphs.
      * `resume_builder.py` (ResumeBuilder): Constructs a PDF resume using a LaTeX template (`resume_template.tex`) and data from the user's profile and generated work experiences.
      * `cover_letter_builder.py` (CoverLetterBuilder): Constructs a PDF cover letter using a LaTeX template (`cover_letter_template.tex`) and generated paragraphs.
      * `utils.py`: Utility functions for LLM-related tasks, like extracting text from PDF bytes.
  * **`backend/app/scraper/`**: Modules for web scraping.
      * `extractors/company_extractor.py` (CompanyExtractor): Scrapes LinkedIn company pages (via Google search to bypass login) to extract company details.
      * `extractors/job_postings_extractor.py` (JobPostingDataExtractor): Scrapes LinkedIn job posting pages to extract job details.
      * `job_posting_publisher.py` (QueryBuilder, JobIdsFetcher): Builds search queries for LinkedIn job postings and fetches job IDs. Stores these job IDs in the `job_postings_to_scrape` table.
      * `job_posting_consumer.py`: Consumes job IDs from the `job_postings_to_scrape` table and uses `JobPostingDataExtractor` to scrape and store the full job details.
      * `companies_scrape_consumer.py`: Identifies companies from scraped job postings that are not yet in the `institutions` table and uses `CompanyExtractor` to scrape their details.
  * **`backend/app/logger/__init__.py`**: Defines a reusable `Logger` class for consistent logging across the backend application.
  * **`backend/app/templates/`**: Contains LaTeX templates:
      * `resume_template.tex`: For generating PDF resumes.
      * `cover_letter_template.tex`: For generating PDF cover letters.
  * **`backend/app/backend_pre_start.py`**: Script run before the main application starts (during Docker container startup) to wait for the database to be available and run Alembic migrations.
  * **`backend/app/initial_data.py`**: Script run after migrations to populate the database with initial data (e.g., superuser, enum values).

## Frontend Development

The frontend is a React application built with Vite and TypeScript. Refer to `frontend/README.md` for more details.

### Node.js Version Management

The project uses Node.js version 20, as specified in `frontend/.nvmrc`.
Use `fnm` or `nvm` to manage your Node.js version:

1.  Navigate to the `frontend` directory: `cd frontend`
2.  Install the required Node.js version (if not already installed):
      * Using `fnm`: `fnm install`
      * Using `nvm`: `nvm install`
3.  Switch to the correct Node.js version:
      * Using `fnm`: `fnm use`
      * Using `nvm`: `nvm use`

### Dependency Management (NPM)

Frontend dependencies are managed using NPM.

1.  Ensure you are in the `frontend` directory.
2.  Install dependencies:
    ```bash
    npm install
    ```
    This will install packages listed in `frontend/package.json`.

### Running the Frontend Dev Server

  * To start the Vite development server with live reload:
    ```bash
    npm run dev
    ```
  * Open your browser at `http://localhost:5173/`.

### Linting and Formatting (Frontend)

  * **Biome** is used for linting and formatting the frontend code.
  * Configuration is in `frontend/biome.json`.
  * Run Biome to check and apply fixes:
    ```bash
    npm run lint
    ```

### Key Frontend Components and Structure

  * **`frontend/src/main.tsx`**: The main entry point of the React application. It sets up `ChakraProvider` for UI components, `QueryClientProvider` for TanStack Query (data fetching and caching), and `RouterProvider` for TanStack Router (routing). It also configures the `OpenAPI.BASE` URL and `OpenAPI.TOKEN` for the auto-generated API client.
  * **`frontend/vite.config.ts`**: Configuration file for Vite, including the React plugin and TanStack Router Vite plugin.
  * **`frontend/src/client/`**: Contains the auto-generated TypeScript API client. Key files:
      * `services.ts`: Contains service classes with methods for making API calls to different backend endpoints (e.g., `LoginService`, `UsersService`, `JobPostingServices`, `UserComparisonServices`, `DimensionsService`).
      * `models.ts`: TypeScript interfaces/types corresponding to Pydantic models in the backend.
      * `schemas.ts`: JSON schema definitions for models (likely used by `openapi-ts`).
      * `core/`: Core utilities for the API client (ApiError, request handling, OpenAPI config).
  * **`frontend/src/components/`**: Reusable React components, organized by feature:
      * **Admin**: `AddUser.tsx`, `EditUser.tsx` (currently commented out in `ActionsMenu.tsx`, suggesting admin user management features).
      * **Common**: General UI elements like `ActionsMenu.tsx`, `DeleteAlert.tsx`, `JsonDisplay.tsx`, `ModelTemperatureSelector.tsx` (for selecting LLM model and temperature), `NotFound.tsx`, `PdfDisplay.tsx`, `PdfUpload.tsx`, `Sidebar.tsx`, `SidebarItems.tsx`, and `UserMenu.tsx`.
      * **Comparisons**: Components for the job comparison feature:
          * `Layout.tsx`: Main layout for the comparisons section, likely a two-pane view.
          * `ComparisonList.tsx`: Displays a list of active job comparisons.
          * `ComparisonDetails.tsx`: Shows detailed information for a selected comparison, including tabs for resume and cover letter, options to generate/build documents, and displays for work experiences and cover letter paragraphs.
          * `WorkExperienceDisplay.tsx`: Renders and allows editing of tailored work experiences.
          * `CoverLetterParagraphDisplay.tsx`: Renders and allows editing of generated cover letter paragraphs.
      * **JobPostings**: Components for Browse and viewing job postings:
          * `JobList.tsx`: Displays a list of job postings.
          * `JobDetails.tsx`: Shows detailed information for a selected job posting.
          * `Pagination.tsx`: Handles pagination for job listings.
      * **UserSettings**: Components for managing user settings:
          * `UserInformation.tsx`: Allows users to view and edit their basic profile information.
          * `UserCV.tsx`: Interface for uploading a resume PDF, triggering LLM parsing, and viewing the raw and parsed resume data.
          * `ParseResume.tsx`: Component to trigger LLM-based resume parsing.
          * `ChangePassword.tsx`: Form for users to change their password.
          * `Appearance.tsx`: Allows users to switch between light and dark color modes.
          * `DeleteAccount.tsx` & `DeleteConfirmation.tsx`: Handles account deletion.
  * **`frontend/src/hooks/`**: Custom React hooks:
      * `useAuth.ts`: Manages authentication state (login, logout, current user data, loading state, errors) and checks if a user is logged in (`isLoggedIn`).
      * `useCustomToast.ts`: Provides a consistent way to show toast notifications.
  * **`frontend/src/routes/`**: Defines the application's routes using TanStack Router.
      * `__root.tsx`: The root route component, includes `TanStackRouterDevtools`.
      * `_layout.tsx`: A layout route that wraps authenticated pages, providing the `Sidebar` and `UserMenu`. It redirects to `/login` if the user is not authenticated.
      * Page components for `/`, `/admin`, `/comparisons`, `/jobpostings`, `/login`, `/recover-password`, `/reset-password`, `/settings`.
  * **`frontend/src/theme.tsx`**: Customizes the Chakra UI theme (colors, button variants, tab styles).
  * **`frontend/src/utils.ts`**: Contains utility functions, such as regex patterns for email/name validation and rules for password fields.
  * **`frontend/src/routeTree.gen.ts`**: Auto-generated file by TanStack Router that defines the route structure.

## Docker Configuration

The application relies heavily on Docker for development and deployment.

  * **`backend/Dockerfile`**:
      * Uses `tiangolo/uvicorn-gunicorn-fastapi:python3.10` as the base image.
      * Installs Poetry and project dependencies.
      * Installs system dependencies like `gnupg`, `wget`, `curl`, `unzip`, and `texlive` packages for LaTeX PDF generation.
      * Sets up the working directory and copies application code and startup scripts.
  * **`frontend/Dockerfile`**:
      * Uses a multi-stage build.
      * **Stage 0 (`build-stage`)**: Based on `node:20`, installs NPM dependencies, and builds the React application (`npm run build`).
      * **Stage 1**: Based on `nginx:1`, copies the compiled frontend assets from the build stage into the Nginx web server directory.
      * Copies Nginx configuration files (`nginx.conf`, `nginx-backend-not-found.conf`).
  * **`docker-compose.yml`**: Defines the main services for production-like environments:
      * `db`: PostgreSQL 12 service, using a volume (`app-db-data`) for data persistence. Environment variables for database configuration are sourced from `.env`.
      * `backend`: Builds from `./backend/Dockerfile`. Depends on `db`. Configured with Traefik labels for routing. Environment variables are sourced from `.env`.
      * `frontend`: Builds from `./frontend/Dockerfile`. Configured with Traefik labels for routing.
      * Defines a `traefik-public` external network.
  * **`docker-compose.override.yml`**: Provides overrides for local development:
      * `proxy`: Traefik service for local development, exposing ports 80 (HTTP) and 8090 (Traefik Dashboard). Includes configurations for enabling the API, insecure mode for the dashboard, and debug logging.
      * `db`: Exposes the PostgreSQL port `5432` to the host. Sets `restart: "no"`.
      * `backend`: Mounts the local `./backend/` directory into the container for live code reloading. Overrides the command to use `/start-reload.sh`. Exposes port `8888`. Sets `restart: "no"`.
      * `frontend`: Builds with `NODE_ENV=development` and `VITE_API_URL=http://${DOMAIN}`. Sets `restart: "no"`.
      * Defines the `traefik-public` network as non-external for local development.
  * **`docker-compose.traefik.yml`**: Configures Traefik for a more production-like setup, including HTTPS certificate resolution with Let's Encrypt, HTTP to HTTPS redirection, and basic authentication for the Traefik dashboard. It assumes an external `traefik-public` network and uses a volume (`traefik-public-certificates`) for storing SSL certificates.
  * **`.dockerignore` files** (in root, `backend/`, `frontend/`): Specify files and directories to exclude from the Docker build context, optimizing build times and image size.

## API Documentation

The backend API documentation is automatically generated by FastAPI and accessible via:

  * **Swagger UI**: `http://localhost/docs`
  * **ReDoc**: `http://localhost/redoc`

These URLs are available when the Docker services are running.
