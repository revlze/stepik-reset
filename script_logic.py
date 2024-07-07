import time
from selenium import webdriver

from selenium.webdriver import Keys

from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


from selenium.webdriver.chrome.service import Service as ChromiumService


class StepikReset:
    """Класс предназначен для сброса прогресса курса на сайте Stepik. При создании экзампляра класса передаются пароль,
    логин и название курса для которого необходимо сбросить прогресс. Логика скрипта реализована в методе "progress_reset".
    """

    LOGIN_PAGE = "https://stepik.org/learn/courses?auth=login"

    # options = webdriver.ChromeOptions()
    # options.add_argument('maxi')
    # options.add_argument('--headless')

    def __init__(self, login: str, password: str, course: str) -> None:
        self.login = login
        self.password = password
        self.course = course

    def progress_reset(self) -> None:
        with webdriver.Chrome() as driver:
            driver.get(url=self.LOGIN_PAGE)
            driver.maximize_window()

            '''авторизация'''
            try:
                WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.ID, 'id_login_email'))).send_keys(self.login)
                WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.ID, 'id_login_password'))).send_keys(
                    self.password)
                WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//button[text()="Войти"]'))).click()
            except Exception:
                print('Сервера Stepik в данный момент недоступны, попробуйте позже')
                exit()

            # '''поиск нужного курса'''
            # WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//button[text()="Понятно"]'))).click()
            # WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.ID, "ember445"))).click()
            # WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//span[text()="Прохожу"]'))).click()

            for _ in range(100):
                try:
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f'''//a[text()='{self.course}']'''))).click()
                    break
                except Exception:
                    driver.execute_script("window.scrollBy(0, 6000)")
            else:
                print('Введеный курс не найден. Проверьте его наличие в вашей библиотеке курсов.')
                exit()

            '''сброс прогресса'''
            WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable((By.XPATH, '//a[@class="lesson-widget__title-text"]'))).click()

            while True:
                try:
                    next_step = WebDriverWait(driver, 60).until(
                        EC.element_to_be_clickable((By.XPATH, '//span[text()="Следующий шаг"]')))
                except Exception:
                    print('Программа успешно завершена, прогресс курса сброшен.')
                    break

                try:
                    it_is_question = WebDriverWait(driver, 0.5, poll_frequency=0.01).until(
                        EC.element_to_be_clickable((By.XPATH, '//h3[@class="quiz__typename"]')))
                except Exception:
                    it_is_question = None

                if it_is_question:
                    try:
                        it_is_decided = WebDriverWait(driver, 0.5, poll_frequency=0.01).until(
                            EC.element_to_be_clickable((By.XPATH, '//button[text()="Отправить"]')))
                    except:
                        it_is_decided = None

                if it_is_question and not it_is_decided:
                    try:
                        WebDriverWait(driver, 1.5, poll_frequency=0.01).until(
                            EC.element_to_be_clickable((By.XPATH, '//button[@class="again-btn white"]'))).click()

                    except:
                        pass

                try:
                    next_step.click()
                except:
                    try:
                        WebDriverWait(driver, 0.5, poll_frequency=0.01).until(EC.element_to_be_clickable((By.XPATH,
                            '//a[text()="Найти новый курс"]')))
                        print('Программа успешно завершена, прогресс курса сброшен.')
                        break
                    except:
                        pass
                    print('Что-то пошло не так, прогресс курса не был сброшен до конца.')
                    exit()