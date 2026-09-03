import sys
import os
from enum import Enum
import csv
from datetime import date, timedelta
from ui.console import Console
from models.enums import SessionState

class Tracker_Manager:
    def __init__(self, model, console):
        self._model = model
        self._console = console
        self._current_state = SessionState.NO_SESSIONS

        self.records = self._model.get_records()
        self._unchained_sessions = [Session.get_session_from_dict(record) for record in self.records]
        self._sessions = []

        self._today = date.today()
        
        self._console.show_welcome_message(self._today)

        # Calculate full sessions object thru @sessions.setter
        self.sessions = self._unchained_sessions

        self.get_current_state()

        while not self.current_state == SessionState.TODAY_EXIST:
            penalty_state = RepsRules.is_next_day_miss_allowed(self.sessions)
            required_reps = RepsRules.next_day_required_reps(self.sessions)
            self._console.display(self.current_state, self.sessions[-1], penalty_state, required_reps)

            next_date = self.sessions[-1].date + timedelta(days=1)
            is_today = (next_date == self._today)

            new_sets_reps = self._console.get_reps(next_date, is_today)
            self.add_new_session(next_date, new_sets_reps)
            self.get_current_state()
        else:
            penalty_state = RepsRules.is_next_day_miss_allowed(self.sessions)
            required_reps = RepsRules.next_day_required_reps(self.sessions)
            self._console.display(self.current_state, self.sessions[-1], penalty_state, required_reps)
       
    @property
    def sessions(self):
        return self._sessions
    
    @property
    def current_state(self):
        return self._current_state
    
    @sessions.setter
    def sessions(self, inbound_sessions):
        for i, session in enumerate(inbound_sessions):
            session.previous = inbound_sessions[i - 1] if i > 0 else None
            session.streak = self.calculate_streak(session)
            self._sessions.append(session)


    def add_new_session(self, date, sets_rep):
        self.sessions.append(Session(date, sets_rep))
        self.sessions[-1].previous = self.sessions[-2]
        self.sessions[-1].streak = self.calculate_streak(self.sessions[-1])
        self._model.write_record(self.sessions[-1].get_session_to_dict())
    
    def calculate_streak(self, session):
        session.streak = 0
        if session.reps != 0:
            session.streak = (session.previous.streak if session.previous else 0) + 1
        return session.streak

    def get_current_state(self):
        if not self.sessions or not self.sessions[-1]:
            sys.exit("Нет данных для обработки")
        self._current_state = self.analyze_current_state()
    
    def analyze_current_state(self) -> SessionState:
        if not self.sessions:
            return SessionState.NO_SESSIONS
        elif self._today == self.sessions[-1].date:
            return SessionState.TODAY_EXIST
        elif (self._today - self.sessions[-1].date).days == 1:
            return SessionState.YESTERDAY_EXIST
        else:
            return SessionState.MISSING_DAYS
       

class SCVDataManager:
    def __init__(self):
        self.records = []
        self.load_records()
 
    def load_records(self):
        with open("exersizes.csv", 'r', newline="", encoding="utf-8") as f:
            self.reader = csv.DictReader(f)
            for row in self.reader:
                self.records.append({"date": row["date"], "reps": row["reps"]})

    def write_record(self, record: dict):
        with open("exersizes.csv", "a", newline="", encoding="UTF-8") as f:
            fieldnames = ["date", "reps"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerow(record)
    
    def get_records(self):
        return self.records

            
class Session:
    def __init__(self, session_date, sets_rep,  previous_session = None, streak = 0):
        self.date = session_date
        self.reps = int(sets_rep)
        self.previous = previous_session
        self.streak = streak

    def __str__(self):
        return f"{self.date}, {self.reps}"
    
    @classmethod
    def get_session_from_dict(cls, dict):
        if dict:
            return Session(dict["date"], dict["reps"])
        else:
            return None
            
    def get_session_to_dict(self):
        return {"date": self.date, "reps": self.reps}
        
    @property
    def date(self):
        return self._date
    
    @date.setter
    def date(self, input):
        if not isinstance(input, date):
            self._date = date.fromisoformat(input)
        else: 
            self._date = input
    
    @property
    def reps(self):
        return self._rep
    
    @reps.setter
    def reps(self, reps):
        self._rep = reps


class RepsRules:
    _SAFE_STREAK = 6
    _LEVELUP_STREAK = 3
    _MAX_REPS = 21
    _MIN_REPS = 3
    _PENALTY_DICREMENT_REPS = 2 
    _LEVELUP_REPS = 2
    
    @classmethod
    def is_next_day_miss_allowed(cls, sessions):
        result = False
        if sessions[-1].streak >= cls._SAFE_STREAK:
            result = True
        return result
    
    @classmethod
    def next_day_required_reps(cls, sessions):
        penalty_reps_count = 0
        current_session = sessions[-1]
        next_session_reps = cls._set_next_session_reps(sessions)
        if current_session.reps == 0:
            zero_reps_count = 0 
            while current_session.reps == 0:
                zero_reps_count += 1 
                penalty_reps_count += cls._PENALTY_DICREMENT_REPS
                current_session = current_session.previous
            else:
                if current_session.streak >= 6:
                    penalty_reps_count -= cls._PENALTY_DICREMENT_REPS
        next_session_reps -= penalty_reps_count
        return next_session_reps
        
    @classmethod
    def _set_next_session_reps(cls, sessions):
        first_nonzero_session = cls._find_first_nonzero_session(sessions)
        next_session_reps = first_nonzero_session.reps
        if RepsRules._is_levelup_streak_completed(first_nonzero_session) and next_session_reps < RepsRules._MAX_REPS:
            next_session_reps += RepsRules._LEVELUP_REPS
        return next_session_reps
        
    @classmethod
    def _is_levelup_streak_completed(cls, current_session):
        # Быстрая проверка через streak — серия слишком короткая
        if current_session.streak < cls._LEVELUP_STREAK:
            return False
        
        # Проверяем одинаковость повторов в серии
        target_reps = current_session.reps
        previous = current_session.previous
        levelup_streak_counter = 1

        while levelup_streak_counter < cls._LEVELUP_STREAK:
            if previous is None or previous.reps == 0:
                return False
            if previous.reps != target_reps:
                return False
            levelup_streak_counter += 1
            previous = previous.previous

        return True
        
    @classmethod
    def _find_first_nonzero_session(cls, sessions):
        current_session = sessions[-1]
        while current_session.reps == 0:
            current_session = current_session.previous
        return current_session
    

def main():
    csv_data_manager = SCVDataManager()
    console = Console()
    tracker_manager = Tracker_Manager(csv_data_manager, console)


if __name__ == "__main__":
    main()
