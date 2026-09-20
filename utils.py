import datetime


def Event_ID_IH(clubno: int, grades: set[int], gender: str) -> str:
    """Create an interhouse ID using the agreed IH01$5-C$A convention."""
    if not grades:
        raise ValueError("At least one eligible grade is required.")
    club_no_padded = f"{clubno:02d}"
    min_grade = min(grades)
    max_grade = max(grades)
    min_hex = hex(min_grade)[-1].upper()
    max_hex = hex(max_grade)[-1].upper()
    return f"IH{club_no_padded}${min_hex}-{max_hex}${gender[0].upper()}"


def Event_ID_IS(n: int, grades: list[int], gender: str, main_event: str | None = None) -> str:
    # Generate Event ID in format: IS{event_no}{gender}{grade_string}${main_event}
    # Eg. IS0002A$9ABCD$TEST for event number 2 grades 9,10,11,12 for all genders and main event 'TEST'
    event_no_padded = str(n).zfill(4)
    grade_hex_map = {i: hex(i)[-1].upper() for i in range(1, 13)}
    grade_string = "".join([grade_hex_map[g] for g in sorted(grades)])

    event_id = f"IS{event_no_padded}{gender[0].upper()}${grade_string}"

    if main_event:
        event_id += f"${main_event}"

    return event_id


def age_from_dob(dob: datetime.date, reference_date: datetime.date | None = None) -> int:
    """Calculate age on the event date, not an approximate number of days."""
    reference_date = reference_date or datetime.date.today()
    return reference_date.year - dob.year - ((reference_date.month, reference_date.day) < (dob.month, dob.day))


def email_create(name: str, id: int, domain: str = "school.com") -> str:
    # Create email id for student with first name and student id
    id_padded = f"{id:04d}"
    first_name = name.split()[0]
    return f"{first_name.lower()}{id_padded}@{domain}"


def tgt_name(first_name: str, middle_name: str | None, last_name: str) -> str:
    # Generate full name from first, middle (optional), and last names
    first_name = first_name.strip()
    last_name = last_name.strip()
    if middle_name:
        middle_name = middle_name.strip()
        return f"{first_name} {middle_name} {last_name}"
    return f"{first_name} {last_name}"


def name_parts(full_name: str) -> tuple[str, str | None, str]:
    # Split full name into first, middle (optional), and last names
    parts = full_name.partition(" ")
    first_name = parts[0]
    parts = parts[2].rpartition(" ")
    last_name = parts[2]
    middle_name = parts[0].strip() if parts[0].strip() else None
    return first_name, middle_name, last_name
