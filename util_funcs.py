'''Event ID Creation'''

#create club no.s and add club no. validator
#setup Interschool Event numbers method

def Event_ID_IH(clubno:int,grades:set,gender:str):

    #IH ##(CLUB NO.) then 1-12 hexadecimal (6-8, 9-C) GBA

    a,b = str(hex(min(grades)))[-1],str(hex(max(grades)))[-1]
    event_ID = f'IH${clubno}${a}-{b}${gender[0].upper()}'

    return event_ID

def IS_number(Data):
    
    n = max(Data.keys(),key = lambda x:x[2:6])
    n = n[:2] + str(int(n[2:])+1)

    return n

def Event_ID_IS(n:int,grades:set,gender:str,main_event:str=None):

    #IS #### then grades(T/F) followed by $'main event name'
    #Map later

    event_ID = f'IS${n}${grades}${gender[0].upper()}'

    if main_event:
        event_ID += f'${main_event}'

    return event_ID

three = {'IS'+str(i):i**(1/2) for i in range(1000,4869)}

print(IS_number(three))

