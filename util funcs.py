'''Event ID Creation'''

#create club no.s and add club no. validator
#setup Interschool Event numbers method

def Event_ID_IH(clubno:int,grades:set,gender:str):

    #IH ##(CLUB NO.) then 1-12 hexadecimal (6-8, 9-C) GBA

    a,b = str(hex(min(grades)))[-1],str(hex(max(grades)))[-1]
    event_ID = f'IH{clubno}{a}-{b}{gender[0].upper()}'

    return event_ID

def Event_ID_IS(n:int,grades:dict,gender:str,main_event:str=None):

    #IS ## then grades(T/F) followed by $'main event name'

    grade_set = ['T' if grades[i] else 'F' for i in range(1,13)]
    event_ID = f'IS{n}{grade_set}{gender[0].upper()}'

    if main_event:
        event_ID += f'${main_event}'

    return event_ID

