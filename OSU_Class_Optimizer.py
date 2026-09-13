"""Download OSU's public Spring 2027 class-search results to a local JSON file."""

import json
import secrets
import time
from pathlib import Path
from tracemalloc import start

import requests


BASE_URL = "https://studentregistrationssb.okstate.edu/StudentRegistrationSsb/ssb"
TERM = "202660"  # Spring 2026
REQUESTED_PAGE_SIZE = 1_000
OUTPUT_PATH = Path(__file__).with_name("fall_2026_sections.json")
PARTIAL_OUTPUT_PATH = Path(__file__).with_name("fall_2026_sections.partial.json")
REQUEST_TIMEOUT_SECONDS = 30


def require_success(response: requests.Response, step: str) -> None:
    """Raise a concise error when OSU does not accept a request."""
    try:
        response.raise_for_status()
    except requests.HTTPError as error:
        preview = response.text[:500].strip()
        raise RuntimeError(f"{step} failed ({response.status_code}): {preview}") from error


def make_unique_session_id() -> str:
    """Match the browser's non-persistent search-ID shape."""
    base36 = "0123456789abcdefghijklmnopqrstuvwxyz"
    return "".join(secrets.choice(base36) for _ in range(5)) + str(int(time.time() * 1000))


def initialize_search(session: requests.Session, unique_session_id: str) -> None:
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


def fetch_page(session: requests.Session, unique_session_id: str, offset: int) -> dict:
    """Fetch one result page using the initialized temporary session."""
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
    """Load an interrupted download so the next run can resume at its offset."""
    if not PARTIAL_OUTPUT_PATH.exists():
        return []
    try:
        payload = json.loads(PARTIAL_OUTPUT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Could not read {PARTIAL_OUTPUT_PATH.name}.") from error
    if payload.get("term") != TERM or not isinstance(payload.get("sections"), list):
        raise RuntimeError(f"{PARTIAL_OUTPUT_PATH.name} does not match the configured term.")
    return payload["sections"]


def save_partial_sections(sections: list[dict], expected_total: int) -> None:
    """Atomically checkpoint successful pages without saving session credentials."""
    temporary_path = PARTIAL_OUTPUT_PATH.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps({"term": TERM, "totalCount": expected_total, "sections": sections}),
        encoding="utf-8",
    )
    temporary_path.replace(PARTIAL_OUTPUT_PATH)


def fetch_all_sections() -> list[dict]:
    """Return every section, advancing by the count actually returned."""
    with requests.Session() as session:
        session.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "*/*"})
        unique_session_id = make_unique_session_id()
        initialize_search(session, unique_session_id)
        sections = load_partial_sections()
        offset = len(sections)
        expected_total: int | None = None
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
                "No output file was written.")
        return sections

def format_time(time):
    if time is None:
        return None

    hour = int(time[:2])
    minute = time[2:]

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

def findCourseSections(sections: list[dict], courseRequest: str) -> list[dict]:
    """Return all sections matching the requested course."""
    matching_sections = []
    for section in sections:
        subject = section.get("subjectCourse", "").upper()
        if courseRequest == subject and section.get("scheduleTypeDescription") != "LAB" and section["meetingsFaculty"][0]["meetingTime"]["campusDescription"] == "Stillwater":
            matching_sections.append(section)
    return matching_sections

def displayCourseSections(sections: list[dict], matching_sections: list[dict]) -> None:
    for section in matching_sections:

        for section in matching_sections:
            if section["meetingsFaculty"][0]["meetingTime"]["monday"] and section["meetingsFaculty"][0]["meetingTime"]["wednesday"] and section["meetingsFaculty"][0]["meetingTime"]["friday"]:
                meeting_days = "MWF"
            elif section["meetingsFaculty"][0]["meetingTime"]["tuesday"] and section["meetingsFaculty"][0]["meetingTime"]["thursday"]:
                meeting_days = "TR"
        
            lecture_time = None
            lab_time = None
        
            for meeting in section["meetingsFaculty"]:
                category = meeting["category"]
                start = meeting["meetingTime"]["beginTime"]
                end = meeting["meetingTime"]["endTime"]
        
                if category == "01":
                    lecture_time = f"{format_time(start)} - {format_time(end)}"
                    lecture_location = meeting["meetingTime"]["building"] + " " + meeting["meetingTime"]["room"]
        
                elif category == "02":
                    lab_time = f"{format_time(start)} - {format_time(end)}"
                    lab_location = meeting["meetingTime"]["building"] + " " + meeting["meetingTime"]["room"]

        print("CRN:", section.get("courseReferenceNumber"))
        
        print(f"{section.get('seatsAvailable')}/{section.get('enrollment')} Seats Available")

        print("Meeting Times: ", meeting_days, "|", lecture_time, "lecture in " + lecture_location, "|" if lab_time else "", lab_time if lab_time else "", "lab in " + lab_location if lab_time else "") 
    
        print("Professor: " + section["faculty"][0]["displayName"])

        print()

def main() -> None:
    '''
    print("Starting OSU Class Optimizer...")
    try:
        sections = fetch_all_sections()
        print(f"\nSaved {len(sections):,} sections to {OUTPUT_PATH.name}.")
    except requests.RequestException as error:
        raise SystemExit(f"Network request failed: {error}") from error
    except RuntimeError as error:
        raise SystemExit(error) from error

    if not sections:
        print(
            "OSU returned no sections for Fall 2026. The term may not be published "
            "in public class search yet."
        )
        return
    '''

    with open("fall_2026_sections.json", "r") as file:
        sections = json.load(file)

    OUTPUT_PATH.write_text(json.dumps(sections, indent=2), encoding="utf-8")
    first = sections[0]

    courseRequest = input("What course would you like to search for? (e.g., CS1113, MATH3013, ENGL)2345: ").strip().upper()
    print()

    displayCourseSections(sections, findCourseSections(sections, courseRequest))    


if __name__ == "__main__":
    main()
