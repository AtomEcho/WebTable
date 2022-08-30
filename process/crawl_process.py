import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import pyppeteer
import asyncio
from selenium.webdriver.common.by import By


def crawler_html(url, proxies=None):
    if proxies is not None:
        if isinstance(proxies, list):
            proxy = str(random.choice(proxies))
        else:
            proxy = str(proxies)
        req_proxies = {
            "http": proxy,
            "https": proxy
        }
    else:
        req_proxies = None

    html = requests.get(url=url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/72.0.3626.119 Safari/537.36'}, verify=False, proxies=req_proxies)
    html = html.content.decode('utf-8', 'ignore')
    return html


def crawler_html_selenium(url, proxies=None):
    options = Options()
    options.set_capability("acceptInsecureCerts", True)
    options.add_argument('headless')

    if proxies is not None:
        if isinstance(proxies, list):
            proxy = str(random.choice(proxies))
        else:
            proxy = str(proxies)
        proxy = '--proxy-server=' + proxy
        options.add_argument(proxy)

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    driver.implicitly_wait(10)
    driver.get(url)
    js = "var q=document.documentElement.scrollTop=100000"
    driver.execute_script(js)
    if len(driver.find_elements(by=By.TAG_NAME, value="iframe")):
        driver.switch_to.frame(driver.find_elements(by=By.TAG_NAME, value="iframe")[0])
    html = driver.page_source
    return html


async def crawler_html_pyppeteer(url: str, proxies=None):
    username = password = ''
    if proxies is not None:
        if isinstance(proxies, list):
            proxy = str(random.choice(proxies))
        else:
            proxy = str(proxies)
        if 'socks5://' in proxy:
            proxy = proxy.replace('socks5://', '')
            proxy_mode = 'sock5://'
        else:
            proxy = proxy.replace('http://', '')
            proxy_mode = 'http://'
        if '@' in proxy:
            username = proxy.split('@')[0].split(':')[0]
            password = proxy.split('@')[0].split(':')[1]
            proxy = proxy.split('@')[1]
        browser = await pyppeteer.launch(headless=True,
                                         args=['--disable-infobars', f'--proxy-server={proxy_mode}{proxy}'],
                                         ignoreHTTPSErrors=True)
    else:
        browser = await pyppeteer.launch(headless=True, args=['--disable-infobars'], ignoreHTTPSErrors=True)
    page = await browser.newPage()
    if username != '' or password != '':
        await page.authenticate({
            "username": username,
            "password": password
        })
    await page.setViewport({'width': 1920, 'height': 1080})
    await page.evaluateOnNewDocument('Object.defineProperty(navigator,"webdriver",{get:()=>undefined})')
    await page.goto(url)
    # await page.evaluate('_ => {window.scrollBy(0, window.innerHeight);}')
    await page.evaluate('_ => {window.scrollBy(0, 20000);}')
    await asyncio.sleep(10)
    html = await page.content()
    await browser.close()
    return html
