from app.security.sanitize import escape_html, validate_upload


def test_escape_html_neutralises_script_tags():
    payload = '<img src=x onerror="alert(1)">'
    escaped = escape_html(payload)
    assert "<img" not in escaped
    assert "&lt;img" in escaped


def test_escape_html_handles_empty_and_none():
    assert escape_html("") == ""
    assert escape_html(None) == ""


def test_validate_upload_rejects_wrong_type():
    result = validate_upload("malware.exe", "application/x-msdownload", 1024)
    assert not result.ok
    assert "type" in result.reason.lower()


def test_validate_upload_rejects_oversized_file():
    result = validate_upload("huge.pdf", "application/pdf", 11 * 1024 * 1024)
    assert not result.ok
    assert "large" in result.reason.lower()


def test_validate_upload_rejects_empty_file():
    result = validate_upload("empty.pdf", "application/pdf", 0)
    assert not result.ok


def test_validate_upload_accepts_valid_pdf():
    result = validate_upload("notes.pdf", "application/pdf", 2 * 1024 * 1024)
    assert result.ok


def test_validate_upload_accepts_valid_image():
    result = validate_upload("scan.png", "image/png", 500_000)
    assert result.ok
