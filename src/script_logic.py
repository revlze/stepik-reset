import re
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Page


class StepikReset:
    LOGIN_PAGE = "https://stepik.org/learn/courses?auth=login"

    def __init__(self, login: str, password: str, course: str) -> None:
        self.login = login
        self.password = password
        self.course_id = self._extract_course_id(course)

    @staticmethod
    def _extract_course_id(course: str) -> str:
        match = re.search(r"/course/(\d+)", course)
        if match:
            return match.group(1)
        if course.isdigit():
            return course
        raise ValueError(
            f"Не удалось извлечь ID курса из значения: {course!r}. "
            "Укажите полную ссылку (например, https://stepik.org/course/100707) или числовой ID (например, 100707)."
        )

    def progress_reset(self) -> None:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            browser_context = browser.new_context()
            # https://medium.com/@minekayaa/scraping-101-anti-bot-tactics-in-playwright-vs-selenium-795c16cc352f
            browser_context.add_init_script("""
                                            // Hide Automation Traces
                                            Object.defineProperty(navigator, 'webdriver', { get: () => undefined })
                                            // Spoof Browser Identity
                                            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                                            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
                                            """)
            # Block Tracking & Analytics Requests
            browser_context.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if any(t in route.request.url for t in ["analytics", "datadome"])
                    else route.continue_()
                ),
            )
            page = browser_context.new_page()
            try:
                self._run(page)
            except KeyboardInterrupt:
                print("\nПрервано пользователем.")
            finally:
                browser.close()
    
    def _simulate_human_movements(self, page: Page) -> None:
        '''Случайно выбирает между разными имитациями.'''
        choice = random.choice([self._simulate_scroll, self._simulate_mouse_movements])
        choice(page)
    
    def _simulate_scroll(self, page: Page) -> None:
        delta_y = random.randint(100, 400)
        page.mouse.wheel(0, delta_y)
        page.wait_for_timeout(random.randint(200, 500))
        page.mouse.wheel(0, -delta_y)
        page.wait_for_timeout(random.randint(200, 500))

    def _simulate_mouse_movements(self, page: Page) -> None:
        x = random.randint(0, 1280)
        y = random.randint(0, 900)
        page.mouse.move(x, y, steps=random.randint(5, 15))
    
    # пока не используется
    def _simulate_typing(self, page: Page) -> None:
        bait = page.locator(".comments-input__bait")
        if bait.count() == 0:
            return
        bait.first.click()
        
        text = ["Интересный урок!", "Спасибо за материал!", "Отлично объяснено!", "Очень полезно!", "Круто!"]
        try:
            editor = page.locator(".comments-input__editor [contenteditable='true']").first
            editor.wait_for(state="visible", timeout=3000)
            editor.press_sequentially(random.choice(text), delay=random.randint(100, 200))
        except :
            raise PlaywrightTimeoutError("Не удалось напечатать текст в поле комментария. Возможно, изменился интерфейс сайта или возникла временная проблема.")

        # отменяем наш коммент
        try:
            page.locator('.comments-input__btns button.white:has-text("Отменить")').click(timeout=10_000)
        except PlaywrightTimeoutError:
            raise PlaywrightTimeoutError("Не удалось найти кнопку отмены комментария после имитации набора текста.")


    def _run(self, page: Page) -> None:
        page.set_viewport_size({"width": 1280, "height": 900})
        page.goto(self.LOGIN_PAGE)

        # авторизация
        try:
            page.locator("#id_login_email").wait_for(state="visible", timeout=60_000)
            page.locator("#id_login_email").fill(self.login)
            page.locator("#id_login_password").fill(self.password)
            page.wait_for_timeout(random.randint(200, 400))
            page.locator('button:has-text("Войти")').click()
        except PlaywrightTimeoutError:
            print("Сервера Stepik в данный момент недоступны, попробуйте позже")
            raise PlaywrightTimeoutError("Что-то пошло не так на этапе авторизации. Проверьте правильность введенных данных и доступность сайта.")


        # поиск нужного курса
        selector = f'a.item-tile__title-link[href*="/course/{self.course_id}"]'
        found = False
        for _ in range(100):
            if page.locator(selector).count() > 0:
                try:
                    page.locator(selector).first.click(timeout=5_000)
                    found = True
                    break
                except PlaywrightTimeoutError:
                    raise PlaywrightTimeoutError("Курс найден, но не удалось кликнуть по нему. Возможно, изменился интерфейс сайта.")
            page.evaluate("window.scrollBy(0, 6000)")
            page.wait_for_timeout(random.randint(200, 400))

        if not found:
            print(
                "Введеный курс не найден. Проверьте его наличие в вашей библиотеке курсов."
            )
            return

        # первый урок
        try:
            page.locator("a.lesson-widget__title-text").first.click(timeout=60_000)
        except PlaywrightTimeoutError:
            print("Что-то пошло не так, прогресс курса не был сброшен до конца.")
            return

        # сброс прогресса
        while True:
            # пробуем найти кнопку "Следующий шаг", если её нет - значит мы в конце курса или возникла какая-то ошибка
            try:
                next_step = page.locator('span:has-text("Следующий шаг")')
                next_step.wait_for(state="visible", timeout=60_000)
            except PlaywrightTimeoutError:
                print(
                    "Программа успешно завершена, прогресс курса сброшен или произошла ошибка, советую проверить корректность."
                )
                break

            it_is_question = False
            try:
                page.locator("h3.quiz__typename").wait_for(state="visible", timeout=500)
                it_is_question = True
            except PlaywrightTimeoutError:
                pass

            if it_is_question:
                it_is_solved = False
                try:
                    page.locator('button:has-text("Отправить")').wait_for(
                        state="visible", timeout=500
                    )
                    it_is_solved = True
                except PlaywrightTimeoutError:
                    pass

                if not it_is_solved:
                    try:
                        again = page.locator("button.again-btn.white")
                        again.wait_for(state="visible", timeout=1_500)
                        page.wait_for_timeout(random.randint(200, 700))
                        again.click()
                    except PlaywrightTimeoutError:
                        pass

            self._simulate_human_movements(page)

            try:
                page.wait_for_timeout(random.randint(200, 700))
                next_step.click(timeout=5_000)
            except PlaywrightTimeoutError:
                try:
                    page.locator('a:has-text("Найти новый курс")').wait_for(
                        state="visible", timeout=500
                    )
                    print("Программа успешно завершена, прогресс курса сброшен.")
                    break
                except PlaywrightTimeoutError:
                    pass
                print("Что-то пошло не так, прогресс курса не был сброшен до конца.")
                return
