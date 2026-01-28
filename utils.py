import datetime

def Event_ID_IH(clubno:int,grades:set,gender:str):
    #Generate Event ID in format: IH{club_no}{min_grade}-{max_grade}{gender}
    #Eg. IH00049-CA for club number 4 grades 9-12 for all genders
    club_no_padded = f'{clubno:02d}'
    
    min_grade = min(grades)
    max_grade = max(grades)

    min_hex = hex(min_grade)[-1].upper()
    max_hex = hex(max_grade)[-1].upper()
    
    event_ID = f'IH{club_no_padded}{min_hex}-{max_hex}{gender[0].upper()}'

    return event_ID

def Event_ID_IS(n:int,grades:list,gender:str,main_event:str=None):
    #Generate Event ID in format: IS{event_no}{gender}{grade_string}${main_event}
    #Eg. IS0002A$9ABCD$TEST for event number 2 grades 9,10,11,12 for all genders and main event 'TEST'
    event_no_padded = f'{n:04d}'
    grade_hex_map = {i: hex(i)[-1].upper() for i in range(1, 13)}
    grade_string = ''.join([grade_hex_map[g] for g in sorted(grades)])
    
    event_ID = f'IS{event_no_padded}{gender[0].upper()}${grade_string}'

    if main_event:
        event_ID += f'${main_event}'

    return event_ID

def age_from_dob(dob: datetime.date):
    #Calculate age in years from date of birth
    current_date = datetime.date.today()
    age = current_date - dob
    age_years = int(age.days // 365.25)
    
    return age_years   

def email_create(name: str, id:int, domain: str = "school.com"):
    #Create email id for student with first name and student id
    id_padded = f"{id:04d}"
    name = name.split()[0]
    email = f"{name.lower()}{id_padded}@{domain}"
    return email

def tgt_name(first_name: str, middle_name: str | None, last_name: str):
    #Generate full name from first, middle (optional), and last names
    first = first_name.strip()
    last = last_name.strip()
    if middle_name:
        middle = middle_name.strip()
        return f"{first} {middle} {last}"
    return f"{first} {last}"

def name_parts(full_name: str):
    #Split full name into first, middle (optional), and last names
    parts = full_name.partition(' ')
    first_name = parts[0]
    parts = parts[2].rpartition(' ')
    last_name = parts[2]
    middle_name = parts[0].strip() if parts[0].strip() else None
    return first_name, middle_name, last_name
