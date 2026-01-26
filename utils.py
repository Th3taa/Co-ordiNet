import datetime

def Event_ID_IH(clubno:int,grades:set,gender:str):
    club_no_padded = f'{clubno:02d}'
    
    min_grade = min(grades)
    max_grade = max(grades)

    min_hex = hex(min_grade)[-1].upper()
    max_hex = hex(max_grade)[-1].upper()
    
    event_ID = f'IH{club_no_padded}{min_hex}-{max_hex}{gender[0].upper()}'

    return event_ID

def Event_ID_IS(n:int,grades:list,gender:str,main_event:str=None):
    event_no_padded = f'{n:04d}'
    grade_hex_map = {i: hex(i)[-1].upper() for i in range(1, 13)}
    grade_string = ''.join([grade_hex_map[g] for g in sorted(grades)])
    
    event_ID = f'IS{event_no_padded}{gender[0].upper()}${grade_string}'

    if main_event:
        event_ID += f'${main_event}'

    return event_ID

def age_from_dob(dob: datetime.date):
    current_date = datetime.date.today()
    age = current_date - dob
    age_years = age.days // 365
    
    return age_years   

def email_create(name: str, id:int, domain: str = "school.com"):
    id_padded = f"{id:04d}"
    name = name.split()[0]
    email = f"{name.lower()}{id_padded}@{domain}"
    return email

def tgt_name(first_name: str, middle_name: str | None, last_name: str):
    first = first_name.strip()
    last = last_name.strip()
    if middle_name:
        middle = middle_name.strip()
        return f"{first} {middle} {last}"
    return f"{first} {last}"

def name_parts(full_name: str):
    parts = full_name.partition(' ')
    first_name = parts[0]
    parts = parts[2].rpartition(' ')
    last_name = parts[2]
    middle_name = parts[0].strip() if parts[0].strip() else None
    return first_name, middle_name, last_name
