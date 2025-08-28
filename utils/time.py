import os
from datetime import datetime
import pytz


def now_tz() -> datetime:
    """
    Retorna la hora actual en la zona horaria configurada.
    Usa la variable de entorno TZ, por defecto 'America/Bogota'.
    """
    tz_name = os.getenv("TZ", "America/Bogota")
    tz = pytz.timezone(tz_name)
    return datetime.now(tz)
