from dotenv import load_dotenv
import os

from src.script_logic import StepikReset


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(
            f"Переменная окружения {name} не найдена! Проверьте наличие файла .env и его содержимое!"
        )
    return value


load_dotenv()

login = _required("LOGIN")
password = _required("PASSWORD")
course_name = _required("COURSE_ID")

if __name__ == "__main__":
    stepik_reset = StepikReset(login=login, password=password, course=course_name)
    stepik_reset.progress_reset()
