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

## Planned Features

- Generate valid schedules from a list of required courses
- Minimize gaps between classes
- Rank schedules based on user preferences
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

## Data
Course data is retrieved from Oklahoma State University's public class registration system.
Generated course-data JSON files are intentionally excluded from this repository because they are large and can become outdated. The project is designed to process current registration data rather than rely on permanently stored course data.

## Tech Stack
- Python
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

## Project Status
🚧 In Development
The current focus is building and testing the scheduling engine before developing the graphical interface.

## Running the Project
Clone the repository:

```bash git clone https://github.com/jackhildebrand/Cowboy-Compass.git```

```bash cd Cowboy-Compass```

Run the Python program:

```bash python3 OSU_Class_Optimizer.py```

## Future Vision
Cowboy Compass is intended to become a full scheduling platform that allows Oklahoma State students to enter their desired courses and preferences and receive several optimized schedules to choose from.
The long-term goal is to make schedule planning faster, more flexible, and more intelligent than manually comparing hundreds of course sections.
