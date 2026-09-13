import unittest

from scheduler import (
    build_course_options,
    calculate_total_gap,
    generate_schedules,
    rank_schedules,
    remove_conflicting_schedules,
    score_schedule,
)


def meeting(start, end, **days):
    return {"meetingTime": {"beginTime": start, "endTime": end, **days}}


def section(course, crn, meetings):
    return {
        "subjectCourse": course,
        "courseReferenceNumber": crn,
        "scheduleTypeDescription": "Lecture",
        "meetingsFaculty": [
            {**meeting_record, "meetingTime": {**meeting_record["meetingTime"], "campusDescription": "Stillwater"}}
            for meeting_record in meetings
        ],
    }


class SchedulerTests(unittest.TestCase):
    def test_course_options_keep_one_list_per_requested_course(self):
        data = [
            section("CS1113", "A", [meeting("0900", "0950", monday=True)]),
            section("MATH2143", "B", [meeting("1000", "1050", monday=True)]),
        ]
        options = build_course_options(data, ["MATH2143", "CS1113"])
        self.assertEqual([[item["courseReferenceNumber"] for item in group] for group in options], [["B"], ["A"]])

    def test_overlapping_schedules_are_removed(self):
        first = section("CS1113", "A", [meeting("0900", "1000", monday=True)])
        overlap = section("MATH2143", "B", [meeting("0950", "1050", monday=True)])
        back_to_back = section("MATH2143", "C", [meeting("1000", "1050", monday=True)])
        schedules = remove_conflicting_schedules([(first, overlap), (first, back_to_back)])
        self.assertEqual(schedules, [(first, back_to_back)])

    def test_gap_does_not_cross_weekdays(self):
        monday = section("CS1113", "A", [meeting("0900", "1000", monday=True)])
        tuesday = section("MATH2143", "B", [meeting("1500", "1600", tuesday=True)])
        self.assertEqual(calculate_total_gap((monday, tuesday)), 0)

    def test_ranking_uses_lowest_score_first(self):
        early = section("CS1113", "A", [meeting("0900", "1000", monday=True)])
        close = section("MATH2143", "B", [meeting("1030", "1100", monday=True)])
        far = section("MATH2143", "C", [meeting("1300", "1400", monday=True)])
        ranked = rank_schedules([(early, far), (early, close)])
        self.assertEqual(ranked, [(early, close), (early, far)])
        self.assertLess(score_schedule(ranked[0]), score_schedule(ranked[1]))

    def test_common_exams_are_ignored(self):
        class_meeting = meeting("0900", "0950", monday=True)
        exam_meeting = meeting(
            "1800",
            "1900",
            monday=True,
            meetingType="EXCE",
            meetingTypeDescription="Common Exam",
        )
        first = section("CS1113", "A", [class_meeting, exam_meeting])
        second = section("MATH2143", "B", [meeting("1800", "1900", monday=True)])

        self.assertEqual(remove_conflicting_schedules([(first, second)]), [(first, second)])
        self.assertEqual(calculate_total_gap((first,)), 0)


if __name__ == "__main__":
    unittest.main()
