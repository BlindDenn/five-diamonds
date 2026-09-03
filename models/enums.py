from enum import Enum

class SessionState(Enum):
    APP_INIT = "app_init"
    NO_SESSIONS = "no_sessions"
    TODAY_EXIST = "today_exist"
    YESTERDAY_EXIST = "yesterday_exist"
    MISSING_DAYS = "missing_days"
