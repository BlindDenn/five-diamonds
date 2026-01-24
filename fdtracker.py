import sys
import os
from enum import Enum
import csv
from datetime import date, timedelta


class SessionState(Enum):
    APP_INIT = "app_init"
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
            new_sets_reps = self._console.get_reps(self.sessions[-1].date)
            next_date = self.sessions[-1].date + timedelta(days=1)
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

    def analyze_current_state(self) -> SessionState:
        if not self.sessions:
            return SessionState.NO_SESSIONS
        elif self._today == self.sessions[-1].date:
            return SessionState.TODAY_EXIST
        elif (self._today - self.sessions[-1].date).days == 1:
            return SessionState.YESTERDAY_EXIST
        else:
            return SessionState.MISSING_DAYS

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
        if not self.sessions[-1]:
            sys.exit("Нет данных для обработки")
        self._current_state = self.analyze_current_state()
       

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


class Console:
    def __init__(self):
        self.line_len = 100

    _TEMPLATES = {
        SessionState.NO_SESSIONS: {
            "main_message": "В базе данных нет записей о выполненных упражнениях",
            "next_session_message": None

        },
        SessionState.TODAY_EXIST: {
            "main_message": lambda data: (f"В базу данных внесена запись за сегодня.\n"
                f"Подходов: {data.reps}. " 
                f"Непрерывная серия: {data.streak}."),
            "next_session_message": lambda penalty_state: f"Допустим ли пропуск завтра: {penalty_state}",
            "next_session_required_reps": lambda required_reps: f"Рекомендуется повторов завтра: {required_reps}"
        }, 
        SessionState.YESTERDAY_EXIST: {
            "main_message": lambda data: (f"В базе данных есть запись за вчера, "
                f"{Console.humanize_date(data.date)}. \n"
                f"Подходов: {data.reps}. " 
                f"Непрерывная серия: {data.streak}."),
            "next_session_message": lambda penalty_state: f"Допустим ли пропуск сегодня: {penalty_state}",
            "next_session_required_reps": lambda required_reps: f"Рекомендуется повторов: {required_reps}"

        },
        SessionState.MISSING_DAYS: {
            "main_message": lambda data: (f"В базе отсутвуют записи за несколько дней. "
                f"Последняя запись за {Console.humanize_date(data.date)}. \n"
                f"Подходов: {data.reps}. "
                f"Непрерывная серия: {data.streak}."),
            "next_session_message": lambda penalty_state: f"Допустим ли пропуск на следующий день: {penalty_state},",
            "next_session_required_reps": lambda required_reps: f"Рекомендуется повторов: {required_reps}"


        } 
    }

    def display (self, state, session, penalty_state, required_reps):
        template = self._TEMPLATES[state]["main_message"](session) + "\n" + self._TEMPLATES[state]["next_session_message"](penalty_state) + "\n" + self._TEMPLATES[state]["next_session_required_reps"](required_reps)
        self.print_hline()
        print(template)
        self.print_hline()
        # if state == SessionState.MISSING_DAYS or state == SessionState.YESTERDAY_EXIST:
        #     new_sets_reps = self.get_sets_rep(session.date + timedelta(days=1))
        #     return(new_sets_reps)
        
    def get_reps(self, date):
        new_sets_reps = self.get_sets_rep(date + timedelta(days=1))
        return new_sets_reps

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
        # self.print_hline()

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
        print(f"Сессия: {Console.humanize_date(session.date)}, подходов: {session.reps}. Непрерывная серия: {session.streak}")

    def print_sessions(self, sessions):
        for session in sessions:
            print(f"Сессия: {Console.humanize_date(session.date)}, подходов: {session.reps}")

    def get_sets_rep(self, date):
        try:
            reps = int(input(f"Введите количество подходов для сессии {Console.humanize_date(date)}: "))
            self.print_hline
        except ValueError:    
            sys.exit("Количество должно быть числом")
        except KeyboardInterrupt:
            sys.exit("\nПрограмма прервана пользователем")
        return reps
    
    def print_hline(self):
        print("-" * self.line_len)
    
    def print_double_hline(self):
        print("=" * self.line_len)
            

class RepsRules:
    _SAFE_STREAK_DAYS = 6
    _LEVELUP_STREAK = 3
    _MAX_REPS = 21
    _MIN_REPS = 3
    _PENALTY_DICREMENT_COUNT = 2 
    _LEVELUP_REPS_COUNT = 2
    
    @classmethod
    def is_next_day_miss_allowed(cls, sessions):
        result = False
        if sessions[-1].streak >= cls._SAFE_STREAK_DAYS:
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
                penalty_reps_count += cls._PENALTY_DICREMENT_COUNT
                current_session = current_session.previous
            else:
                if current_session.streak >= 6:
                    penalty_reps_count -= cls._PENALTY_DICREMENT_COUNT
        next_session_reps -= penalty_reps_count
        return next_session_reps
        
    @classmethod
    def _set_next_session_reps(cls, sessions):
        first_nonzero_session = cls._find_first_nonzero_session(sessions)
        next_session_reps = first_nonzero_session.reps
        if RepsRules._is_levelup_streak_completed(first_nonzero_session) and next_session_reps < RepsRules._MAX_REPS:
            next_session_reps += RepsRules._LEVELUP_REPS_COUNT
        return next_session_reps
        
    @classmethod
    def _is_levelup_streak_completed(cls, current_session):
        levelup_streak_counter = 1
        zero_counter = 0
        target_reps = current_session.reps
        while levelup_streak_counter < cls._LEVELUP_STREAK:
            next_session = current_session.previous
            while next_session.reps == 0: 
                next_session = next_session.previous
                zero_counter += 1
                if zero_counter > 1:
                    return False
            if not next_session.reps == target_reps:
                return False
            else:
                current_session = next_session
                levelup_streak_counter += 1
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
