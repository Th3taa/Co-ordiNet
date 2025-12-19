from datetime import date
from utils import util_funcs as fns

interhouse,interschool={},{}


class event():

#IH ##(CLUB NO.) then 1-12 hexadecimal (6-8, 9-C) GBA
#IS #### then 1-12 in hexa GBA followed by $'main event name'

    def __init__(self,event_date:date,event_name:str,grades:set,gender ):
        self.name = event_name
        self.date = event_date
        self.grades = grades
        self,gender = gender


class placeholder():

    def __init__(self, name, event_set:set[event], ):
        pass
    
class EventError(LookupError):

    def __init__(self, name, message="Event Already Exists:"):
        super().__init__(f"{message}{name}")


class interhouse(event):

    def __init__(event_date:date,event_name:str,grades:set,gender:str):

        super().__init__(event_date,event_name,grades,gender)
        event_ID = fns.Event_ID_IS(41,grades,gender)

        if event_ID in interhouse:
            del self
            raise EventError

        interhouse[event_ID] = {'Date':event_date,
                                'Name':event_name,
                                'Grades':grades,
                                'Gender':gender}

class interschool(event):

    def __init__(event_date:date,event_name:str,grades:set,gender:str,n=fns.IS_number(interschool)):

        super().__init__(event_date,event_name,grades,gender)
        event_ID = fns.Event_ID_IS(n,grades,gender,None) # deal w dis later

        if event_ID in interschool:
            del self
            raise EventError

        interschool[event_ID] = {'Date':event_date,
                                'Name':event_name,
                                'Grades':grades,
                                'Gender':gender}