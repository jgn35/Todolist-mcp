"""
Minimal iCalendar (RFC 5545) VTODO serializer/parser.

Only the subset needed to persist Task entities on a CalDAV server
(Radicale) is implemented: one VTODO per VCALENDAR, with UID, DTSTAMP,
CREATED, LAST-MODIFIED, SUMMARY, DESCRIPTION, DUE, PRIORITY and STATUS.
"""

from datetime import UTC

from todolist_mcp.domain.entities import Priority, Task, TaskStatus

_PRIORITY_TO_ICAL = {
    Priority.CRITICAL: 1,
    Priority.HIGH: 3,
    Priority.MEDIUM: 5,
    Priority.LOW: 9,
}

_ICAL_TO_PRIORITY = {value: key for key, value in _PRIORITY_TO_ICAL.items()}

_STATUS_TO_ICAL = {
    TaskStatus.PENDING: "NEEDS-ACTION",
    TaskStatus.COMPLETED: "COMPLETED",
    TaskStatus.CANCELLED: "CANCELLED",
}

_ICAL_TO_STATUS = {value: key for key, value in _STATUS_TO_ICAL.items()}


def _escape_text(value: str) -> str:
    """Escape a TEXT property value per RFC 5545 section 3.3.11."""
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _unescape_text(value: str) -> str:
    """Unescape a TEXT property value per RFC 5545 section 3.3.11."""
    result = []
    i = 0
    while i < len(value):
        char = value[i]
        if char == "\\" and i + 1 < len(value):
            nxt = value[i + 1]
            if nxt in ("n", "N"):
                result.append("\n")
            elif nxt in ("\\", ";", ","):
                result.append(nxt)
            else:
                result.append(nxt)
            i += 2
        else:
            result.append(char)
            i += 1
    return "".join(result)


def _fold_line(line: str) -> list[str]:
    """Fold a content line to at most 75 octets per RFC 5545 section 3.1."""
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return [line]
    parts: list[str] = []
    current = ""
    current_len = 0
    limit = 75
    for char in line:
        char_len = len(char.encode("utf-8"))
        if current_len + char_len > limit:
            parts.append(current)
            current = char
            current_len = char_len
            # Continuation lines start with a space, leaving 74 octets.
            limit = 74
        else:
            current += char
            current_len += char_len
    if current:
        parts.append(current)
    # Continuation lines must begin with a single SPACE (RFC 5545 section 3.1).
    return [parts[0]] + [f" {part}" for part in parts[1:]]


def _unfold(text: str) -> list[str]:
    """Unfold content lines (continuation lines start with SPACE/HTAB)."""
    lines: list[str] = []
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw_line.startswith((" ", "\t")) and lines:
            lines[-1] += raw_line[1:]
        else:
            lines.append(raw_line)
    return [line for line in lines if line]


def _to_ical_datetime(value: str | None) -> str | None:
    """Convert 'YYYY-MM-DD HH:MM:SS' to iCalendar 'YYYYMMDDTHHMMSS'."""
    if not value:
        return None
    cleaned = value.strip().replace("-", "").replace(":", "").replace(" ", "T")
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1]
    if "T" not in cleaned:
        cleaned = cleaned + "T000000"
    return cleaned[:15] if len(cleaned) >= 15 else cleaned


def _from_ical_datetime(value: str) -> str | None:
    """Convert iCalendar date/date-time to 'YYYY-MM-DD HH:MM:SS'."""
    cleaned = value.strip().rstrip("Zz")
    if "T" in cleaned:
        date_part, time_part = cleaned.split("T", 1)
        time_part = (time_part + "000000")[:6]
    else:
        date_part, time_part = cleaned, "000000"
    if len(date_part) != 8 or len(time_part) != 6:
        return None
    return (
        f"{date_part[0:4]}-{date_part[4:6]}-{date_part[6:8]} "
        f"{time_part[0:2]}:{time_part[2:4]}:{time_part[4:6]}"
    )


def _parse_content_line(line: str) -> tuple[str, dict[str, str], str] | None:
    """Parse a content line into (name, params, value)."""
    # Split name/params from value at the first ':' that is not inside quotes.
    in_quotes = False
    split_at = -1
    for idx, char in enumerate(line):
        if char == '"':
            in_quotes = not in_quotes
        elif char == ":" and not in_quotes:
            split_at = idx
            break
    if split_at == -1:
        return None
    head, value = line[:split_at], line[split_at + 1:]
    segments = head.split(";")
    name = segments[0].upper()
    params: dict[str, str] = {}
    for segment in segments[1:]:
        if "=" in segment:
            key, _, val = segment.partition("=")
            params[key.upper()] = val.strip('"')
    return name, params, value


def task_to_vtodo_ical(task: Task, dtstamp: str | None = None) -> str:
    """Serialize a Task entity to a VCALENDAR document containing one VTODO."""
    from datetime import datetime

    if dtstamp is None:
        dtstamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//todolist-mcp//EN",
        "BEGIN:VTODO",
        f"UID:{task.id}",
        f"DTSTAMP:{dtstamp}",
    ]
    created = _to_ical_datetime(task.created_at)
    if created:
        lines.append(f"CREATED:{created}")
    modified = _to_ical_datetime(task.updated_at)
    if modified:
        lines.append(f"LAST-MODIFIED:{modified}")
    lines.append(f"SUMMARY:{_escape_text(task.title)}")
    if task.description:
        lines.append(f"DESCRIPTION:{_escape_text(task.description)}")
    due = _to_ical_datetime(task.due_date)
    if due:
        lines.append(f"DUE:{due}")
    if task.priority is not None:
        lines.append(f"PRIORITY:{_PRIORITY_TO_ICAL.get(task.priority, 5)}")
    if task.status is not None:
        lines.append(f"STATUS:{_STATUS_TO_ICAL.get(task.status, 'NEEDS-ACTION')}")
    lines.extend(["END:VTODO", "END:VCALENDAR"])

    folded: list[str] = []
    for line in lines:
        folded.extend(_fold_line(line))
    return "\r\n".join(folded) + "\r\n"


def parse_vtodo_ical(ical_text: str) -> Task | None:
    """Parse a VCALENDAR document and return the first VTODO as a Task."""
    props: dict[str, tuple[dict[str, str], str]] = {}
    in_vtodo = False
    for line in _unfold(ical_text):
        parsed = _parse_content_line(line)
        if parsed is None:
            continue
        name, params, value = parsed
        if name == "BEGIN" and value.upper() == "VTODO":
            in_vtodo = True
            continue
        if name == "END" and value.upper() == "VTODO":
            break
        if in_vtodo:
            props[name] = (params, value)

    if "UID" not in props:
        return None

    uid = props["UID"][1].strip()
    summary = _unescape_text(props["SUMMARY"][1]) if "SUMMARY" in props else ""
    description = (
        _unescape_text(props["DESCRIPTION"][1]) if "DESCRIPTION" in props else None
    )

    due_raw = props["DUE"][1] if "DUE" in props else None
    due_date = _from_ical_datetime(due_raw) if due_raw else None

    priority = None
    if "PRIORITY" in props:
        try:
            priority = _ICAL_TO_PRIORITY.get(int(props["PRIORITY"][1].strip()))
        except ValueError:
            priority = None

    status = None
    if "STATUS" in props:
        status = _ICAL_TO_STATUS.get(props["STATUS"][1].strip().upper())

    created_at = None
    if "CREATED" in props:
        created_at = _from_ical_datetime(props["CREATED"][1])
    updated_at = None
    if "LAST-MODIFIED" in props:
        updated_at = _from_ical_datetime(props["LAST-MODIFIED"][1])
    if updated_at is None and "DTSTAMP" in props:
        updated_at = _from_ical_datetime(props["DTSTAMP"][1])

    return Task(
        title=summary,
        description=description,
        due_date=due_date,
        priority=priority,
        status=status,
        task_id=_safe_uuid(uid),
        created_at=created_at,
        updated_at=updated_at,
    )


def _safe_uuid(value: str):
    from uuid import UUID

    try:
        return UUID(value)
    except ValueError:
        from uuid import NAMESPACE_URL, uuid5

        return uuid5(NAMESPACE_URL, value)
