from app.data.loader import (
    get_academic_calendar,
    get_course_by_code,
    get_courses,
    get_faculty,
    get_formulas,
    get_mcp_servers,
    search_courses,
    search_faculty,
    search_formulas,
)


def test_courses_loaded_with_expected_shape():
    courses = get_courses()
    assert len(courses) == 33
    assert all(c.code and c.name and c.term for c in courses)


def test_get_course_by_code():
    c = get_course_by_code("BMC-501E")
    assert c is not None
    assert "Information Technology" in c.name


def test_search_courses_by_professor():
    results = search_courses("Gaurav Dixit")
    assert results
    assert all("gaurav dixit" in r.professor.lower() for r in results)


def test_faculty_loaded_with_expected_shape():
    faculty = get_faculty()
    assert len(faculty) == 28
    assert all(f.name and f.email for f in faculty)


def test_search_faculty_by_area():
    results = search_faculty(area="ops")
    assert results
    assert all(f.area == "ops" and not f.tag for f in results)


def test_formulas_loaded():
    formulas = get_formulas()
    assert len(formulas) == 30
    npv = next(f for f in formulas if f.name == "NPV")
    assert "Net Present Value" in npv.description


def test_search_formulas_by_query():
    results = search_formulas("IRR")
    assert any(f.name == "IRR" for f in results)


def test_academic_calendar_dates_parse():
    events = get_academic_calendar()
    assert len(events) == 28
    for key in events:
        year, month, day = key.split("-")
        assert year.isdigit() and month.isdigit() and day.isdigit()


def test_mcp_servers_present():
    servers = get_mcp_servers()
    assert set(servers.keys()) == {"mospi", "indeed", "consensus", "morningstar"}
    assert all(url.startswith("https://") for url in servers.values())
