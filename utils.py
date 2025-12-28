def Event_ID_IH(clubno:int,grades:set,gender:str):
    """
    Generate Event ID for Interhouse events.
    Format: IH{CLUB_NO:2}{GRADE_RANGE_HEX}{GENDER}
    
    Args:
        clubno: Club number (will be padded to 2 digits)
        grades: Set of eligible grades (will use min-max range)
        gender: Gender restriction ('G', 'B', or 'A')
    
    Returns:
        Event ID string (e.g., 'IH015-CA' for Club 1, Grades 5-12, All genders)
    """
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
    """
    Generate Event ID for Interschool events.
    Format: IS{NEXT_NO:4}{GENDER}${GRADES}{$MAIN_EVENT}
    
    Args:
        n: Next event number (will be padded to 4 digits)
        grades: List of eligible grade numbers (will be converted to hex string)
        gender: Gender restriction ('G', 'B', or 'A')
        main_event: Optional main event name if this is a sub-event
    
    Returns:
        Event ID string (e.g., 'IS0001A$123456789ABC' for Event 1, All grades, All genders)
    """
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
