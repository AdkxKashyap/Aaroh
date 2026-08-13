# Aaroh

Aaroh is a classroom assignment management app with a FastAPI backend and a local Ollama-based AI flow.

This guide shows the simplest way to run the project on your computer.

## 1) Install Python

Make sure Python 3.10 or newer is installed on your machine.

- Check by opening a terminal and running:

  python3 --version

If Python is not installed, install it first from:
https://www.python.org/downloads/

## 2) Open the project folder

Open a terminal and go to the project folder:

cd /Users/akash/Aaroh

If you are in a different folder, replace the path with your own project location.

## 3) Create a virtual environment

Run:

python3 -m venv .venv

Then activate it:

- On macOS/Linux:

  source .venv/bin/activate

## 4) Install project dependencies

From the project root, run:

pip install -r backend/requirements.txt

This installs the backend libraries and tools required to run the app.

## 5) Start Ollama

The app uses Ollama to run the local AI model.

1. Install Ollama from: https://ollama.com/download
2. Open a terminal and start Ollama if it is not already running:

   ollama serve

3. Pull the model used by the app:

   ollama pull qwen2.5:7b

If the model is already installed, this step will just confirm it is available.

## 6) Start PostgreSQL

The backend uses PostgreSQL.

You can run it with Docker if available:

cd backend

docker compose up -d

This starts the database container defined in the project.

If Docker is not available, make sure PostgreSQL is already running locally and matches the database settings in the backend configuration.

## 7) Run database migrations

From the backend folder, run:

cd backend

Then:

alembic upgrade head

This creates the required tables in the database.

## 8) Start the backend server

From the backend folder, run:

cd backend

Then:

PYTHONPATH=. uvicorn src.main:app --reload

The app should start and expose the API locally.

By default, it is usually available at:

http://localhost:8000

## 9) Verify the app is running

Open your browser and visit:

http://localhost:8000/docs

You should see the FastAPI Swagger documentation page.

## 10) Common project commands

To stop the virtual environment later:

 deactivate

To restart the backend:

 cd backend
 PYTHONPATH=. uvicorn src.main:app --reload

## Troubleshooting

### If Python packages fail to install

Try upgrading pip first:

python3 -m pip install --upgrade pip

Then run:

pip install -r backend/requirements.txt

### If the database connection fails

Check that PostgreSQL is running and that the database credentials in the backend configuration match your database.

### If the AI model is not working

Make sure Ollama is running:

ollama serve

Then confirm the model exists:

ollama list

### If the app does not start

Check the terminal output for missing packages or environment errors.

## Project structure overview

- backend/: Python backend code
- backend/src/: application source
- backend/alembic/: database migration files
- backend/requirements.txt: Python dependencies
- README.md: project instructions

## Notes

This project is intended to be run locally for development. For production deployment, additional security, hosting, and database setup would be needed.
