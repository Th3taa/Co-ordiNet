'''Úser class'''

import json
from datetime import date


with open('Student.json', 'r', encoding='utf-8') as file:
    StudentData = json.load(file)

class user():

    def __init__(self,name:str,email:str,birthday:date,gender:str):
        self.name = name
        self.email = email
        self.birthday = birthday
        self.gender = gender
        self.permissions = {
                            'Register':False,
                            'Unregister':False,
                            'Host Event':False,
                            'Post Notice':False,
                            'h':False
                            }


class student(user):

    def __init__(self,AdmnNo):

        self.AdmissionNumber = AdmnNo
        self.grade = StudentData['Grade']
        self.section = StudentData['Section']
        self.house = StudentData['House']
        self.loginattributes = {}
        self.title:str = "Student"
        self.permissions['Register']=True
        self.permissions['Unregister']=True
        self.iscouncil = False
        self.club = None
        self.role = None
        self.captain = False
        self.vice_captain = False
        self.event_coord = False
        self.editor = False
        self.prefect = False
        self.vice_prefect = False





class council(student):
        
    def __init__(self):
            
        self.iscouncil = True

class club_member(council):

    def __init__(self, role:str, club:str):

        self.club = club
        self.role = role

class house_leader(council):

    def __init__(self, captain=False, vice_captain=False):

        if captain:
            self.captain = True
        elif vice_captain:
            self.vice_captain = True

class event_coordinator(council):

    def __init__(self):

        self.event_coord = True

class student_editor(council):

    def __init__(self):

        self.editor = True

class prefect(council):

    def __init__(self, prefect=False, vice_prefect=False):

        if prefect:
            self.prefect = True
        elif vice_prefect:
            self.vice_prefect = True
            
