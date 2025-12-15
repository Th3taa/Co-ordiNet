import json
from datetime import date

with open('Events.json', 'r', encoding='utf-8') as file:
    EventData = json.load(file)


class event():

    def __init__(event_date:date,event_name:str,grades:set,):
        if event not in EventData:
            pass


class interhouse(event)

class interschool(event)