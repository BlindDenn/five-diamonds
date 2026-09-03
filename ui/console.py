import os
import sys
from models.enums import SessionState

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
                f"Повторов: {data.reps}. " 
                f"Непрерывная серия: {data.streak}."),
            "next_session_message": lambda penalty_state: f"Допустим ли пропуск завтра: {Console.format_penalty(penalty_state)}",
            "next_session_required_reps": lambda required_reps: f"Рекомендуется повторов завтра: {required_reps}"
        }, 
        SessionState.YESTERDAY_EXIST: {
            "main_message": lambda data: (f"В базе данных есть запись за вчера, "
                f"{Console.humanize_date(data.date)}. \n"
                f"Повторов: {data.reps}. " 
                f"Непрерывная серия: {data.streak}."),
            "next_session_message": lambda penalty_state: f"Допустим ли пропуск сегодня: {Console.format_penalty(penalty_state)}",
            "next_session_required_reps": lambda required_reps: f"Рекомендуется повторов: {required_reps}"

        },
        SessionState.MISSING_DAYS: {
            "main_message": lambda data: (f"В базе отсутвуют записи за несколько дней. "
                f"Последняя запись за {Console.humanize_date(data.date)}. \n"
                f"Повторов: {data.reps}. "
                f"Непрерывная серия: {data.streak}."),
            "next_session_message": lambda penalty_state: f"Допустим ли пропуск на следующий день: {Console.format_penalty(penalty_state)}",
            "next_session_required_reps": lambda required_reps: f"Рекомендуется повторов: {required_reps}"
        } 
    }

    def display (self, state, session, penalty_state, required_reps):
        template = self._TEMPLATES[state]["main_message"](session) + "\n" + self._TEMPLATES[state]["next_session_message"](penalty_state) + "\n" + self._TEMPLATES[state]["next_session_required_reps"](required_reps)
        self.print_hline()
        print(template)
        self.print_hline()
        # if state == SessionState.MISSING_DAYS or state == SessionState.YESTERDAY_EXIST:
        #     new_sets_reps = self.get_reps(session.date + timedelta(days=1))
        #     return(new_sets_reps)

    @classmethod
    def humanize_date(cls, date):
        weekdays = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
        weekday = weekdays[date.weekday()]
        # match date.weekday():
        #     case 1:
        #         weekday = "вторник" 
        return date.strftime(f"%d.%m.%Y, {weekday}")
    
    @classmethod
    def format_penalty(cls, current_penalty_state):
        formated_str = f"{Colors.BOLD}{Colors.RED}НЕТ{Colors.RESET}"
        if current_penalty_state:
            formated_str = f"{Colors.GREEN}да{Colors.RESET}"
        return formated_str

    def show_welcome_message(self, today_date):
        # TODO: Заменить os.system на subprocess.run после завершения основного функционала
        os.system('cls')
        self.print_double_hline()
        print(f"{Colors.BOLD}{Colors.GREEN}Это персональный трекер \"Пять Тибетских Жемчужин\"{Colors.RESET}")
        self.print_double_hline()
        print(f"Сегодня {Console.humanize_date(today_date)}\n")
        # self.print_hline()

    # def print_last_session(self, sessions, delta = 0):
    #     match delta:
    #         case 0:
    #             self.print_hline()
    #             print("На сегодня запись существует")
    #         case 1:
    #             print("Cегодня еще нет записи о выполненном упражении")
    #         case _:
    #             print(f"Отсутствует запись за {Console.humanize_date(sessions[-1].date + timedelta(days=1))}")

    # def print_session(self, session):
    #     print(f"Сессия: {Console.humanize_date(session.date)}, повторов: {session.reps}. Непрерывная серия: {session.streak}")

    # def print_sessions(self, sessions):
    #     for session in sessions:
    #         print(f"Сессия: {Console.humanize_date(session.date)}, повторов: {session.reps}")

    def get_reps(self, session_date, is_today=False):
        try:
            today_addon = ", СЕГОДНЯ" if is_today else ""

            prompt_text = f"Введите количество повторов для сессии {Console.humanize_date(session_date)}{today_addon}: "

            reps = int(input(prompt_text))
            # self.print_hline
        except ValueError:    
            sys.exit("Количество должно быть числом")
        except KeyboardInterrupt:
            sys.exit("\nПрограмма прервана пользователем")
        return reps
    
    def print_hline(self):
        print("-" * self.line_len)
    
    def print_double_hline(self):
        print(Colors.GREEN, "=" * self.line_len, Colors.RESET, sep="")


class Colors:
    """ANSI escape sequences for terminal colors"""
    # Стили текста
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    HIDDEN = '\033[8m'
    
    # Основные цвета
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Яркие цвета
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Фоны
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

