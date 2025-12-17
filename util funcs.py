

def Event_ID_IH(clubno:int,grades:set,gender:str):
    #IH ##(CLUB NO.) then 1-12 hexadecimal (6-8, 9-C) GBA
    #IS #### then 1-12 in hexa GBA followed by $'main event name'
    a,b=str(hex(min(grades)))[-1],str(hex(max(grades)))[-1]
    event_ID=f'IH{clubno}{a}-{b}{gender[0].upper()}'
    return event_ID

def Event_ID_IS(n,grades):

    event_ID=f'IS{n}{gender}[0].upper()}'




