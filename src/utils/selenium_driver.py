from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def create_driver(headless: bool = False) -> webdriver.Chrome:
    """
    Создаёт и настраивает экземпляр Chrome WebDriver.
    :param headless: Запускать браузер в фоновом режиме
    :return: Объект Chrome WebDriver
    """
    options = Options()

    if headless:
        options.add_argument("--headless")

    # Общие аргументы
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    options.add_argument("--window-size=1920,1080")

    # Скрываем факт автоматизации
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Настройка user-agent
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Дополнительная маскировка
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            });
        """
    })

    return driver

