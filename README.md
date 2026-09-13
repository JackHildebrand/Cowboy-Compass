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

## Planned Features

- Support preferences such as:
  - Minimize time between classes
  - Prefer days off
  - Avoid early classes
  - Avoid late classes
  - Minimize campus travel
- Display the best schedules in a web interface
- Allow students to customize optimization priorities

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

The scheduling engine will treat requirements such as course availability and schedule conflicts as hard constraints, while preferences such as minimizing gaps between classes will be used to rank valid schedules.
Data
Course data is retrieved from Oklahoma State University's public class registration system.
Generated course-data JSON files are intentionally excluded from this repository because they are large and can become outdated. The project is designed to process current registration data rather than rely on permanently stored course data.
Tech Stack
- Python 3.14.7 (latest stable Python 3 release)
- REST APIs
- JSON
- Data Processing
- Git / GitHub
Planned:
- FastAPI
- PostgreSQL
- React / Next.js
- Docker
- Automated testing
- CI/CD

The reusable scheduling logic lives in `scheduler.py`. The terminal program and future web interface can both import it.
Project Status
🚧 In Development
The current focus is building and testing the scheduling engine before developing the graphical interface.
Running the Project
Clone the repository:
git clone https://github.com/jackhildebrand/Cowboy-Compass.git
cd Cowboy-Compass
Install the dependency and run the Python program with Python 3.14:
python3.14 -m pip install requests
python3.14 OSU_Class_Optimizer.py
python3.14 -m unittest discover -s tests -v

## React Web App

The React interface lives in `web/` and connects to the local Python scheduling API. Run the API in one terminal, then start the web app in another:

```bash
# Terminal 1, from the project root
python3 api.py

# Terminal 2
cd web
pnpm install
pnpm dev
```

Open the local web address printed by Vite, add courses, and choose **Find schedules**. The browser sends the requested course list to Python, and the returned conflict-free schedules replace the sample results.

## Deploying with Vercel and Render

The repository includes `render.yaml` for the Python API and `web/vercel.json` for the React site.

1. Create a Render **Web Service** from this repository. Render will use `render.yaml`; copy the API URL after the service deploys.
2. Create a Vercel project from this repository and set its **Root Directory** to `web`.
3. In Vercel, add `VITE_API_URL` with the Render URL ending in `/api/schedules`.
4. In Render, set `ALLOWED_ORIGIN` to the deployed Vercel URL and redeploy the API.

The API listens on Render's `PORT` environment variable and exposes `/health` so the service can be checked automatically. During its build, Render runs `prepare_render_data.py` to download the current OSU sections; the generated JSON stays on the service and is not committed to Git.
Future Vision
Cowboy Compass is intended to become a full scheduling platform that allows Oklahoma State students to enter their desired courses and preferences and receive several optimized schedules to choose from.
The long-term goal is to make schedule planning faster, more flexible, and more intelligent than manually comparing hundreds of course sections.
