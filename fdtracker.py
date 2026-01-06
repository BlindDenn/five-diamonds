import sys
import os
from enum import Enum
import csv
from datetime import date, timedelta


class SessionState(Enum):
    NO_SESSIONS = "no_sessions"
    TODAY_EXIST = "today_exist"
    YESTERDAY_EXIST = "yesterday_exist"
    MISSING_DAYS = "missing_days"


class Tracker_Manager:
    def __init__(self, model, console):
        self._model = model
        self._console = console
        self._current_state = SessionState.NO_SESSIONS

        self.records = self._model.get_records()
        self._unchained_sessions = [Session.get_session_from_dict(record) for record in self.records]

        self._today = date.today()
        self._sessions = []
        
        self._console.show_welcome_message(self._today)

        self.sessions = self._unchained_sessions

        self.get_current_state()

        self._console.display(self.current_state, self.sessions[-1])
    
        # === Работающий код! ===

        # while self.sessions[-1].date != self._today:
        #     self.check_last_session()
        #     self._console.print_last_session(self.sessions, self.get_delta())
        #     self.add_new_session(self.sessions[-1].date + timedelta(days=1))
        #     model.write_record(self.sessions[-1].get_session_to_dict())

        # self._console.print_last_session(self.sessions[-1])
        # self.curren_streak = self.calculate_streak(self.sessions[-1])
        # self._console.print_session(self.sessions[-1], self.curren_streak)

        # ===========================

    
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
            # self._console.print_session(session)
            self._sessions.append(session)

    def analyze_current_state(self) -> SessionState:
        if not self.sessions:
            return SessionState.NO_SESSIONS
        elif self._today == self.sessions[-1].date:
            return SessionState.TODAY_EXIST
        elif (self._today - self.sessions[-1].date).days == 1:
            return SessionState.YESTERDAY_EXIST
        else:
            return SessionState.MISSING_DAYS

    def add_new_session(self, date):
        self.sessions.append(Session(date, self._console.get_sets_number(date)))
        self.sessions[-1].previous = self.sessions[-2]
        self.sessions[-1].streak = self.calculate_streak(self.sessions[-1])
        self._model.write_record(self.sessions[-1].get_session_to_dict())

    # def get_delta(self):
    #     return (self._today - self.sessions[-1].date).days
    
    # def calculate_streak(self, current_session):
    #     streak = 0
    #     while current_session.number != 0:
    #         streak += 1
    #         current_session = current_session.previous
    #     return streak
    
    def calculate_streak(self, session):
        session.streak = 0
        if session.number != 0:
            session.streak = (session.previous.streak if session.previous else 0) + 1
        return session.streak

    def get_current_state(self):
        if not self.sessions[-1]:
            sys.exit("Нет данных для обработки")

        # session = self.sessions[-1]
        self._current_state = self.analyze_current_state()
        # match (self._today - session.date).days:
        #     case 0:
        #         print(self._session_state.value)
        #         print("Есть запись сегодня")
        #         self._console.print_session(session)
        #     case 1:
        #         print(self._session_state.value)
        #         print("Есть запись вчера, следует внести запись за сегодня")
        #         self.add_new_session(self._today)
        #         self._console.print_session(self.sessions[-1])
        #     case _:
        #         print(self._session_state.value)
        #         print("Есть пропущенные записи")
        #         self.add_new_session(session.date + timedelta(days=1))
        #         self.process_last_session()

        


    # def get_todays_session(self):
    #     if self._sessions[-1].date == self._today:
    #         return self._sessions[-1]
    #     else:
    #         return False
        
    # def check_sessions_continuity(self):
    #     delta = self.sessions[-1].date - self.sessions[-2].date 
    #     print(type(delta), delta)
        
    # def print_recent_session(self):
    #     self._console.print_session(self._sessions[-1])
       

class SCVDataManager:
    def __init__(self):
        self.records = []
        self.load_records()
 
    def load_records(self):
        with open("exersizes.csv", 'r', newline="", encoding="utf-8") as f:
            self.reader = csv.DictReader(f)
            for row in self.reader:
                self.records.append({"date": row["date"], "number": row["number"]})

    def write_record(self, record: dict):
        with open("exersizes.csv", "a", newline="", encoding="UTF-8") as f:
            fieldnames = ["date", "number"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerow(record)
    
    def get_records(self):
        return self.records

            
class Session:
    def __init__(self, session_date, sets_number,  previous_session = None, streak = 0, min_amount_complited = False):
        self.date = session_date
        self.number = int(sets_number)
        self.previous = previous_session
        self.streak = streak
        self.min_amount_complited = min_amount_complited

    def __str__(self):
        return f"{self.date}, {self.number}"
    
    @classmethod
    def get_session_from_dict(cls, dict):
        if dict:
            return Session(dict["date"], dict["number"])
        else:
            return None
        
    
    def get_session_to_dict(self):
        return {"date": self.date, "number": self.number}
        
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
    def number(self):
        return self._number
    
    @number.setter
    def number(self, number):
        self._number = number


class Console:
    def __init__(self):
        self.line_len = 60

    _TEMPLATES = {
        SessionState.NO_SESSIONS: {
            "title": "В базе данных нет записей о выполненных упражнениях",
            "data": None
        },
        SessionState.TODAY_EXIST: {
            "title": f"В базе данных есть запись об упражнениях, выполненных сегодня",
            "data": f"Сессия есть{60}"
        },
        SessionState.YESTERDAY_EXIST: {
            "title": lambda data: f"В базе данных есть запись об упражнениях, сделанных вчера, {data.date}. Было сделано подходов: {data.number}",
            "data": None
        },
        SessionState.MISSING_DAYS: {
            "title": "В базе данных нет записей о нескольких последних днях",
            "data": None
        } 
    }

    def display (self, state, session):
        template = self._TEMPLATES[state]["title"](session)
        print(template)

    @classmethod
    def humanize_date(cls, date):
        weekdays = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
        weekday = weekdays[date.weekday()]
        match date.weekday():
            case 1:
                weekday = "вторник" 
        return date.strftime(f"%d.%m.%Y, {weekday}")
    
    def show_welcome_message(self, today_date):
        os.system('cls')
        self.print_double_hline()
        print("Это персональный трекер \"Пять Тибетских Жемчужин\"")
        self.print_double_hline()
        print(f"Сегодня {Console.humanize_date(today_date)}\n")
        self.print_hline()

    def print_last_session(self, sessions, delta = 0):
        match delta:
            case 0:
                self.print_hline()
                print("На сегодня запись существует")
            case 1:
                print("Cегодня еще нет записи о выполненном упражении")
            case _:
                print(f"Отсутствует запись за {Console.humanize_date(sessions[-1].date + timedelta(days=1))}")

    def print_session(self, session):
        print(f"Сессия: {Console.humanize_date(session.date)}, подходов: {session.number}. Непрерывная серия: {session.streak}")

    def print_sessions(self, sessions):
        for session in sessions:
            print(f"Сессия: {Console.humanize_date(session.date)}, подходов: {session.number}")

    def get_sets_number(self, date):
        try:
            number = int(input(f"Введите количество подходов для сессии {Console.humanize_date(date)}: "))
        except ValueError:    
            sys.exit("Количество должно быть числом")
        return number
    
    def print_hline(self):
        print("-" * self.line_len)
    
    def print_double_hline(self):
        print("=" * self.line_len)
            

def main():
    csv_data_manager = SCVDataManager()
    console = Console()
    tracker_manager = Tracker_Manager(csv_data_manager, console)


if __name__ == "__main__":
    main()
