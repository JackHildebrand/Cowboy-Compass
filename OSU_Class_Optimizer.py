"""Terminal interface for Cowboy Compass."""

from __future__ import annotations

import json
import secrets
import time
from pathlib import Path
from typing import Any

from scheduler import (
    DAY_LABELS,
    MEETING_TYPE_NAMES,
    build_course_options,
    calculate_total_gap,
    count_class_days,
    find_course_sections,
    rank_schedules,
    remove_conflicting_schedules,
    generate_schedules,
    score_schedule,
    time_to_minutes,
)

BASE_URL = "https://studentregistrationssb.okstate.edu/StudentRegistrationSsb/ssb"
TERM = "202660"  # Spring 2026
REQUESTED_PAGE_SIZE = 1_000
OUTPUT_PATH = Path(__file__).with_name("fall_2026_sections.json")
PARTIAL_OUTPUT_PATH = Path(__file__).with_name("fall_2026_sections.partial.json")
REQUEST_TIMEOUT_SECONDS = 30
TOP_SCHEDULES_TO_DISPLAY = 10


def require_success(response: Any, step: str) -> None:
    """Raise a concise error when OSU does not accept a request."""
    import requests

    try:
        response.raise_for_status()
    except requests.HTTPError as error:
        preview = response.text[:500].strip()
        raise RuntimeError(f"{step} failed ({response.status_code}): {preview}") from error


def make_unique_session_id() -> str:
    """Match the browser's non-persistent search-ID shape."""
    base36 = "0123456789abcdefghijklmnopqrstuvwxyz"
    random_prefix = "".join(secrets.choice(base36) for _ in range(5))
    return random_prefix + str(int(time.time() * 1_000))


def initialize_search(session: Any, unique_session_id: str) -> None:
    """Establish the public, temporary search context required by OSU."""
    response = session.get(
        f"{BASE_URL}/term/termSelection",
        params={"mepCode": "OSU", "mode": "search"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    require_success(response, "Term selection")

    response = session.post(
        f"{BASE_URL}/term/search",
        params={"mode": "search"},
        data={"term": TERM, "uniqueSessionId": unique_session_id},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    require_success(response, "Term search context")


def fetch_page(session: Any, unique_session_id: str, offset: int) -> dict:
    """Fetch one result page using the initialized temporary session."""
    import requests

    response = session.get(
        f"{BASE_URL}/searchResults/searchResults",
        params={
            "txt_term": TERM,
            "startDatepicker": "",
            "endDatepicker": "",
            "uniqueSessionId": unique_session_id,
            "pageOffset": offset,
            "pageMaxSize": REQUESTED_PAGE_SIZE,
            "sortColumn": "subjectDescription",
            "sortDirection": "asc",
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    require_success(response, f"Search-results page at offset {offset}")
    try:
        return response.json()
    except requests.JSONDecodeError as error:
        raise RuntimeError("OSU returned a non-JSON search response.") from error


def load_partial_sections() -> list[dict]:
    """Load an interrupted download so the next run can resume."""
    if not PARTIAL_OUTPUT_PATH.exists():
        return []

    try:
        payload = json.loads(PARTIAL_OUTPUT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Could not read {PARTIAL_OUTPUT_PATH.name}.") from error

    if not isinstance(payload, dict):
        raise RuntimeError(f"{PARTIAL_OUTPUT_PATH.name} has an invalid format.")
    if payload.get("term") != TERM or not isinstance(payload.get("sections"), list):
        raise RuntimeError(f"{PARTIAL_OUTPUT_PATH.name} does not match the configured term.")
    return payload["sections"]


def save_partial_sections(sections: list[dict], expected_total: int) -> None:
    """Atomically checkpoint successful pages without session credentials."""
    temporary_path = PARTIAL_OUTPUT_PATH.with_suffix(".tmp")
    payload = {"term": TERM, "totalCount": expected_total, "sections": sections}
    temporary_path.write_text(json.dumps(payload), encoding="utf-8")
    temporary_path.replace(PARTIAL_OUTPUT_PATH)


def fetch_all_sections() -> list[dict]:
    """Download and return every section from OSU's public search."""
    import requests

    with requests.Session() as session:
        session.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "*/*"})
        unique_session_id = make_unique_session_id()
        sections = load_partial_sections()
        offset = len(sections)
        expected_total: int | None = None

        initialize_search(session, unique_session_id)
        if sections:
            print(f"Resuming from {offset:,} checkpointed sections.")

        while True:
            payload = fetch_page(session, unique_session_id, offset)
            if expected_total is None:
                expected_total = int(payload.get("totalCount") or 0)
                print(f"OSU reports {expected_total:,} sections.")

            page = payload.get("data") or []
            if not page:
                break

            sections.extend(page)
            offset += len(page)
            print(f"Downloaded {len(sections):,} of {expected_total:,} sections.")
            save_partial_sections(sections, expected_total)
            if len(sections) >= expected_total:
                break

        if expected_total is not None and len(sections) != expected_total:
            raise RuntimeError(
                f"Expected {expected_total:,} sections but received {len(sections):,}. "
                "No output file was written."
            )
        return sections


def load_sections(path: Path | None = None) -> list[dict]:
    """Load cached section data and explain common file errors clearly."""
    path = path or OUTPUT_PATH
    try:
        with path.open(encoding="utf-8") as file:
            sections = json.load(file)
    except FileNotFoundError:
        raise SystemExit(f"Course data not found. Place {path.name} next to this script.")
    except json.JSONDecodeError:
        raise SystemExit(f"Could not read {path.name}: invalid JSON.")

    if not isinstance(sections, list):
        raise SystemExit(f"Could not read {path.name}: expected a list of sections.")
    return sections


def format_time(raw_time: str | None) -> str | None:
    """Convert a four-digit time such as '1330' to '1:30 PM'."""
    if not isinstance(raw_time, str) or len(raw_time) < 4:
        return None

    try:
        hour = int(raw_time[:2])
    except (TypeError, ValueError):
        return None

    minute = raw_time[2:]
    if hour == 0:
        hour = 12
        period = "AM"
    elif hour < 12:
        period = "AM"
    elif hour == 12:
        period = "PM"
    else:
        hour -= 12
        period = "PM"
    return f"{hour}:{minute} {period}"


def normalize_course_request(course: str) -> str:
    """Normalize 'cs 1113' and 'CS1113' to the same lookup value."""
    return "".join(course.upper().split())


def get_course_requests() -> list[str]:
    """Prompt until the user enters DONE and return normalized courses."""
    courses: list[str] = []
    print("Enter the courses you want to take in the format: CS 1113.")
    print("Enter DONE when finished.\n")

    while True:
        course = normalize_course_request(input("Course: "))
        if course == "DONE":
            return courses
        if course:
            courses.append(course)


def professor_names(section: dict) -> str:
    """Return the listed professor names for a section."""
    faculty = section.get("faculty") or []
    return ", ".join(person.get("displayName") or "TBA" for person in faculty) or "TBA"


def location_name(meeting_time: dict) -> str:
    """Return a readable building and room label."""
    building = meeting_time.get("buildingDescription") or meeting_time.get("building")
    room = meeting_time.get("room")
    if building and room:
        return f"{building}, Room {room}"
    return building or room or "TBA"


def schedule_calendar(schedule: tuple[dict, ...]) -> dict[str, list[tuple[int, str]]]:
    """Build chronologically sortable calendar entries for a schedule."""
    calendar: dict[str, list[tuple[int, str]]] = {day: [] for day, _ in DAY_LABELS}
    for section in schedule:
        course = section.get("subjectCourse") or "Course TBA"
        title = section.get("courseTitle") or "Title TBA"
        crn = section.get("courseReferenceNumber", "TBA")
        professor = professor_names(section)
        for meeting in section.get("meetingsFaculty") or []:
            meeting_time = meeting.get("meetingTime") or {}
            start = time_to_minutes(meeting_time.get("beginTime"))
            end = time_to_minutes(meeting_time.get("endTime"))
            start_text = format_time(meeting_time.get("beginTime")) or "TBA"
            end_text = format_time(meeting_time.get("endTime")) or "TBA"
            meeting_type = (
                meeting_time.get("meetingTypeDescription")
                or MEETING_TYPE_NAMES.get(meeting.get("category"), "Meeting")
            )
            details = (
                f"{start_text} - {end_text} | {course} {title} | "
                f"{meeting_type} | {location_name(meeting_time)} | "
                f"Professor: {professor} | CRN: {crn}"
            )
            sort_start = start if start is not None else 24 * 60
            for day, _ in DAY_LABELS:
                if meeting_time.get(day):
                    calendar[day].append((sort_start, details))

    for entries in calendar.values():
        entries.sort(key=lambda entry: entry[0])
    return calendar


def display_schedules(schedules: list[tuple[dict, ...]]) -> None:
    """Print every schedule as a full weekly calendar, best score first."""
    ranked_schedules = rank_schedules(schedules)
    schedules_to_display = ranked_schedules[:TOP_SCHEDULES_TO_DISPLAY]
    print(
        f"\nTop {len(schedules_to_display)} schedules "
        f"(of {len(ranked_schedules)}, best score first):"
    )

    for number, schedule in enumerate(schedules_to_display, start=1):
        total_gap = calculate_total_gap(schedule)
        class_days = count_class_days(schedule)
        score = score_schedule(schedule)
        print("\n" + "=" * 90)
        print(
            f"Schedule {number} | Score: {score} | "
            f"Total gap: {total_gap} minutes | Class days: {class_days}"
        )
        print("=" * 90)

        calendar = schedule_calendar(schedule)
        for day, _ in DAY_LABELS:
            print(f"{day.title()}:")
            entries = calendar[day]
            if not entries:
                print("  No classes")
                continue
            for _, details in entries:
                print(f"  {details}")


def meeting_days(meeting_time: dict) -> str:
    """Return a compact meeting-day label such as MWF or TR."""
    return "".join(
        label for day, label in DAY_LABELS if meeting_time.get(day)
    ) or "TBA"


def display_course_section(section: dict) -> None:
    """Print one course section in a readable terminal format."""
    print("CRN:", section.get("courseReferenceNumber", "TBA"))
    seats = section.get("seatsAvailable", "TBA")
    enrollment = section.get("enrollment", "TBA")
    print(f"{seats}/{enrollment} Seats Available")

    meetings = section.get("meetingsFaculty") or []
    if not meetings:
        print("Meeting Times and Locations: TBA")

    for meeting in meetings:
        meeting_time = meeting.get("meetingTime") or {}
        start = format_time(meeting_time.get("beginTime")) or "TBA"
        end = format_time(meeting_time.get("endTime")) or "TBA"
        location_parts = (meeting_time.get("building"), meeting_time.get("room"))
        location = " ".join(part for part in location_parts if part) or "TBA"
        meeting_type = MEETING_TYPE_NAMES.get(meeting.get("category"), "meeting")
        print(
            "Meeting Times and Locations: "
            f"{meeting_days(meeting_time)} | {start} - {end} "
            f"{meeting_type} in {location}"
        )

    faculty = section.get("faculty") or []
    professors = ", ".join(
        person.get("displayName") or "TBA" for person in faculty
    ) or "TBA"
    print("Professor:", professors)
    print()


def display_course_options(
    requested_courses: list[str], course_options: list[list[dict]]
) -> None:
    """Print verification counts followed by all matching sections."""
    print("\nSections found for each requested course:")
    for course, sections in zip(requested_courses, course_options):
        print(f"{course}: {len(sections)} matching sections")

    print()


def main() -> None:
    """Run the interactive course lookup workflow."""
    all_sections = load_sections()
    courses = get_course_requests()
    course_options = build_course_options(all_sections, courses)
    display_course_options(courses, course_options)

    all_schedules = generate_schedules(course_options)
    valid_schedules = remove_conflicting_schedules(all_schedules)
    print(f"Possible schedules: {len(all_schedules):,}")
    print(f"Conflict-free schedules: {len(valid_schedules):,}")
    display_schedules(valid_schedules)


if __name__ == "__main__":
    main()
