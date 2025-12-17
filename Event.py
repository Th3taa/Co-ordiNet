from datetime import date

interhouse,interschool={},{}

EventData = {}
EventData.update(interhouse)
EventData.update(interschool)

class event():

#IH ##(CLUB NO.) then 1-12 hexadecimal (6-8, 9-C) GBA
#IS #### then 1-12 in hexa GBA followed by $'main event name'

    def __init__(self,event_date:date,event_name:str,grades:set,gender ):
        self.name = event_name
        self.date = event_date
        self.grades = grades
        self,gender = gender
        event_ID = 'abcd'
        if event_ID not in EventData:
            pass#add event
        else:
            raise EventError

class placeholder():

    def __init__(self, name, event_set:set[event], ):
        pass
    
class EventError(LookupError):

    def __init__(self, name, message="Event Already Exists:"):
        super().__init__(f"{message}{name}")


class interhouse(event):
    pass

class interschool(event):
    pass
