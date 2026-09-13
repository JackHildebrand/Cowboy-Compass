# Cowboy Compass

An intelligent course schedule optimizer for Oklahoma State University students.

## Overview

Cowboy Compass helps students find better class schedules by analyzing available course sections and ranking possible schedules based on their preferences.

The primary goal is to minimize the amount of time students spend waiting between classes while respecting required courses and scheduling constraints.

## Current Features

- Retrieves course section data from Oklahoma State University's public registration system
- Processes thousands of course sections
- Filters courses by subject, course number, instructor, enrollment, and meeting information
- Parses lecture and lab meeting components
- Handles multiple meeting times within a course section
- Converts OSU's time format into usable scheduling data
- Identifies potential schedule conflicts
- Generates every one-section-per-course schedule
- Removes schedules with overlapping meeting times
- Calculates total idle time between classes
- Scores and ranks conflict-free schedules

## Web app

The React interface is live at [cowboy-compass.vercel.app](https://cowboy-compass.vercel.app/). It lets students enter courses, request schedules, review the top ten ranked options, copy CRNs, and open instructor names in Rate My Professors.

## How It Works

Cowboy Compass is being developed as a constraint-based scheduling system.

```text
OSU Course Data
       ↓
Data Processing
       ↓
Course & Section Filtering
       ↓
Constraint Checking
       ↓
Schedule Generation
       ↓
Schedule Scoring
       ↓
Ranked Schedules
```

The scheduling engine treats course availability and schedule conflicts as hard constraints. Preferences such as minimizing gaps and class days influence the ranking of valid schedules.

## Data

Course data is retrieved from Oklahoma State University's public class registration system.
Generated course-data JSON files are intentionally excluded from this repository because they are large and can become outdated. Render downloads current data during its build instead.

## Tech stack

- Python 3.14
- React 19 and Vite
- REST API with Python's standard library HTTP server
- JSON data processing
- Git and GitHub
- Vercel (frontend) and Render (API hosting)

The reusable scheduling logic lives in `scheduler.py`; both the terminal program and API import it.

## Project status

The scheduling engine and first React web app are working. Spring 2027 data and additional preference controls are planned next.

## Running locally

Clone the repository:
```bash
git clone https://github.com/jackhildebrand/Cowboy-Compass.git
cd Cowboy-Compass
```

Install the dependency and run the terminal program with Python 3.14:
```bash
python3.14 -m pip install requests
python3.14 OSU_Class_Optimizer.py
python3.14 -m unittest discover -s tests -v
```

### React web app

The React interface in `web/` connects to the local Python scheduling API. Run the API in one terminal, then start Vite in another:

```bash
# Terminal 1, from the project root
python3 api.py

# Terminal 2
cd web
pnpm install
pnpm dev
```

Open the local web address printed by Vite, add courses, and choose **Find schedules**. The browser sends the requested course list to Python, and the returned conflict-free schedules replace the sample results.

## Deployment

The repository includes `render.yaml` for the Python API and `web/vercel.json` for the React site.

The production frontend is deployed on Vercel and the Python API is deployed on Render:

- Frontend: [cowboy-compass.vercel.app](https://cowboy-compass.vercel.app/)
- API health check: [cowboy-compass.onrender.com/health](https://cowboy-compass.onrender.com/health)

To reproduce the deployment:

1. Create a Render **Web Service** from this repository. Render uses `render.yaml`; copy the API URL after the service deploys.
2. Create a Vercel project from this repository and set its **Root Directory** to `web`.
3. In Vercel, add `VITE_API_URL` with the Render URL ending in `/api/schedules`.
4. In Render, set `ALLOWED_ORIGIN` to the deployed Vercel URL and redeploy the API.

The API listens on Render's `PORT` environment variable and exposes `/health` for automatic service checks. During its build, Render runs `prepare_render_data.py` to download current OSU sections; generated JSON remains on the service and is never committed.

## Future direction

Planned improvements include Spring 2027 support, customizable ranking preferences, and additional travel-aware scheduling options.
