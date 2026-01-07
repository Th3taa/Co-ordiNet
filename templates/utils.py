import datetime

def Event_ID_IH(clubno:int,grades:set,gender:str):
    
    #Format: IH{CLUB_NO:2}{GRADE_RANGE_HEX}{GENDER}

    # Pad club number to 2 digits
    club_no_padded = f'{clubno:02d}'
    
    min_grade = min(grades)
    max_grade = max(grades)

    # Convert to hex and get last character (handles 1-9 as is, 10=a, 11=b, 12=c)
    min_hex = hex(min_grade)[-1].upper()
    max_hex = hex(max_grade)[-1].upper()
    
    event_ID = f'IH{club_no_padded}{min_hex}-{max_hex}{gender[0].upper()}'

    return event_ID

def Event_ID_IS(n:int,grades:list,gender:str,main_event:str=None):

    #Format: IS{NEXT_NO:4}{GENDER}${GRADES}{$MAIN_EVENT}

    # Pad event number to 4 digits
    event_no_padded = f'{n:04d}'
    
    # Convert grades to hexadecimal characters
    # Grade mapping: 1=1, 2=2, ..., 9=9, 10=A, 11=B, 12=C
    grade_hex_map = {i: hex(i)[-1].upper() for i in range(1, 13)}
    grade_string = ''.join([grade_hex_map[g] for g in sorted(grades)])
    
    event_ID = f'IS{event_no_padded}{gender[0].upper()}${grade_string}'

    if main_event:
        event_ID += f'${main_event}'

    return event_ID


def test(message: str = "-------"):

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('test_log.txt', 'a') as f:
        f.write(f'[{timestamp}] {message}\n')

def DB_log(message: str = "-------"):

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('db_log.txt', 'a') as f:
        f.write(f'[{timestamp}] {message}\n')

def register_log(message: str = "-------"):

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('registration_log.txt', 'a') as f:
        f.write(f'[{timestamp}] {message}\n')

def session_log(message: str = "-------"):

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('session_log.txt', 'a') as f:
        f.write(f'[{timestamp}] {message}\n')

def age_from_dob(dob: datetime.date):
    current_date = datetime.now().date()
    age = current_date - dob
    age_years = age.days // 365
    
    return age_years    
