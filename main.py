from script_logic import StepikReset

login = input('Введите логин аккаунт Stepik: ')
password = input('Введите пароль аккаунт Stepik: ')
course_name = input('Введите название курса для которого вы желаете сбросить прогресс: ')



if __name__ == '__main__':
    stepik_reset = StepikReset(login=login, password=password, course=course_name)
    stepik_reset.progress_reset()