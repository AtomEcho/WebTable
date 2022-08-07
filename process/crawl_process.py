from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import pyppeteer
import asyncio


def crawler_html(url):
    html = requests.get(url=url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/72.0.3626.119 Safari/537.36'}, verify=False)
    html = html.content.decode('utf-8', 'ignore')
    return html


def crawler_html_selenium(url):
    options = Options()
    options.set_capability("acceptInsecureCerts", True)
    options.add_argument('headless')
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    driver.implicitly_wait(10)
    driver.get(url)
    js = "var q=document.documentElement.scrollTop=100000"
    driver.execute_script(js)
    html = driver.page_source
    return html


async def crawler_html_pyppeteer(url):
    browser = await pyppeteer.launch(headless=True, args=['--disable-infobars'], ignoreHTTPSErrors=True)
    page = await browser.newPage()
    await page.setViewport({'width': 1920, 'height': 1080})
    await page.evaluateOnNewDocument('Object.defineProperty(navigator,"webdriver",{get:()=>undefined})')

    await page.goto(url)
    # await page.evaluate('_ => {window.scrollBy(0, window.innerHeight);}')
    await page.evaluate('_ => {window.scrollBy(0, 20000);}')
    await asyncio.sleep(10)
    html = await page.content()
    await browser.close()
    return html
