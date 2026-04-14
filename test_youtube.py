"""
Лабораторная работа №5
Автоматизированное дымовое тестирование веб-сервиса YouTube.

Требования:
    pip install selenium pytest

Запуск:
    pytest test_youtube.py -v --tb=short

Примечание:
    Требуется установленный Google Chrome и chromedriver,
    совместимый с версией браузера.
"""

import pytest
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains


# ============================================================
#  Конфигурация
# ============================================================

SCREENSHOT_DIR = "screenshots"
BASE_URL = "https://www.youtube.com"
WAIT_TIMEOUT = 15  # секунд ожидания элемента


# ============================================================
#  Фикстуры
# ============================================================

@pytest.fixture(scope="module")
def driver():
    """Инициализация и завершение работы браузера."""
    # Создаём папку для скриншотов
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # раскомментировать для запуска без GUI
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--lang=ru")

    browser = webdriver.Chrome(options=chrome_options)
    browser.implicitly_wait(10)

    yield browser

    browser.quit()


def take_screenshot(driver, name):
    """Сохранение скриншота с указанным именем."""
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(path)
    print(f"  Скриншот сохранён: {path}")


# ============================================================
#  Тест 1: Загрузка главной страницы
# ============================================================

def test_01_open_main_page(driver):
    """
    Дымовой тест: главная страница YouTube загружается корректно.
    Проверяем наличие логотипа и строки поиска.
    """
    driver.get(BASE_URL)

    # Принимаем куки, если появляется баннер
    try:
        accept_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[@aria-label='Accept the use of cookies and other data for the purposes described' or "
                "contains(., 'Принять') or contains(., 'Accept all')]"
            ))
        )
        accept_btn.click()
        time.sleep(1)
    except Exception:
        pass  # Баннер может не появиться

    # Проверяем строку поиска
    search_input = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.NAME, "search_query"))
    )
    assert search_input is not None, "Строка поиска не найдена"

    # Проверяем, что title содержит YouTube
    assert "YouTube" in driver.title, f"Title страницы: {driver.title}"

    take_screenshot(driver, "01_main_page")


# ============================================================
#  Тест 2: Поиск видео (заполнение поля ввода + нажатие кнопки)
# ============================================================

def test_02_search_video(driver):
    """
    Заполнение поля поиска, нажатие кнопки поиска.
    Проверяем, что появились результаты.
    """
    # Находим поле поиска
    search_input = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.NAME, "search_query"))
    )
    search_input.clear()

    # Заполняем поле ввода
    search_query = "Selenium Python tutorial"
    search_input.send_keys(search_query)
    time.sleep(1)

    # Нажимаем Enter для выполнения поиска
    search_input.send_keys(Keys.ENTER)

    # Ждём появления результатов
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, "contents"))
    )
    time.sleep(2)

    # Проверяем, что URL содержит параметр поиска
    assert "search_query=" in driver.current_url or "results" in driver.current_url, \
        f"Не произошёл переход на страницу результатов: {driver.current_url}"

    # Проверяем, что есть хотя бы один результат
    results = driver.find_elements(By.CSS_SELECTOR, "ytd-video-renderer")
    assert len(results) > 0, "Результаты поиска не найдены"

    take_screenshot(driver, "02_search_results")


# ============================================================
#  Тест 3: Переход к видео из результатов поиска
# ============================================================

def test_03_open_video(driver):
    """
    Нажатие на первое видео из результатов поиска.
    Проверяем, что открылась страница воспроизведения.
    """
    # Кликаем на заголовок первого видео
    first_video = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((
            By.CSS_SELECTOR, "ytd-video-renderer #video-title"
        ))
    )
    first_video.click()

    # Ждём загрузки страницы видео
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "video.html5-main-video"))
    )
    time.sleep(3)

    # Проверяем URL
    assert "/watch" in driver.current_url, \
        f"Не открылась страница видео: {driver.current_url}"

    take_screenshot(driver, "03_video_page")


# ============================================================
#  Тест 4: Управление воспроизведением (пауза)
# ============================================================

def test_04_pause_video(driver):
    """
    Нажатие на кнопку паузы в плеере.
    Проверяем, что видео приостановлено.
    """
    # Наводим курсор на плеер, чтобы появились контролы
    player = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#movie_player"))
    )
    ActionChains(driver).move_to_element(player).perform()
    time.sleep(1)

    # Нажимаем на кнопку play/pause
    play_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((
            By.CSS_SELECTOR, "button.ytp-play-button"
        ))
    )
    play_button.click()
    time.sleep(2)

    # Проверяем состояние плеера
    player_state = driver.execute_script(
        "return document.querySelector('#movie_player').getPlayerState();"
    )
    # 2 = paused, 1 = playing
    # Примечание: состояние может быть 2 (пауза) или -1 (не начато)
    assert player_state != 1, \
        f"Видео всё ещё воспроизводится (state={player_state})"

    take_screenshot(driver, "04_video_paused")


# ============================================================
#  Тест 5: Скролл до секции комментариев (скролл по локатору)
# ============================================================

def test_05_scroll_to_comments(driver):
    """
    Скролл страницы до секции комментариев по локатору.
    Проверяем, что комментарии подгрузились.
    """
    # Скроллим до секции комментариев
    driver.execute_script("window.scrollBy(0, 600);")
    time.sleep(2)

    # Ждём, пока секция комментариев подгрузится
    try:
        comments_section = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-comments#comments"))
        )
        # Скроллим до элемента комментариев
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            comments_section
        )
        time.sleep(3)

        # Проверяем, что есть заголовок с количеством комментариев
        comment_count = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR, "#comments #count"
            ))
        )
        assert comment_count is not None, "Счётчик комментариев не найден"

    except Exception:
        # У некоторых видео комментарии отключены
        pytest.skip("Комментарии недоступны для данного видео")

    take_screenshot(driver, "05_comments_section")


# ============================================================
#  Тест 6: Возврат на главную страницу
# ============================================================

def test_06_navigate_home(driver):
    """
    Нажатие на логотип YouTube для возврата на главную.
    """
    # Кликаем на логотип
    logo = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "a#logo"))
    )
    logo.click()

    # Ждём загрузки главной
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-rich-grid-renderer"))
    )
    time.sleep(2)

    # Проверяем, что мы на главной
    current = driver.current_url.rstrip("/")
    assert current.endswith("youtube.com") or "youtube.com/?" in driver.current_url \
        or "youtube.com/feed" in driver.current_url, \
        f"Не вернулись на главную: {driver.current_url}"

    take_screenshot(driver, "06_back_to_home")


# ============================================================
#  Запуск
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
