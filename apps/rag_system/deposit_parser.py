import os
import pandas as pd

from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


BASE_URL = "https://www.banki.ru/products/deposits/?type=14&special[]=14&sort=efficient_rate&order=desc"

def parse_deposits(): 

    firefox_options = Options()
    firefox_options.add_argument("--headless")
    driver = webdriver.Firefox(options=firefox_options)

    driver.get(BASE_URL)
    html = driver.page_source

    soup = BeautifulSoup(html, 'html.parser')

    driver.quit()

    bank_name = [x.text for x in soup.find_all('div', class_="Text__sc-vycpdy-0 cIWZzu")]
    rate = [x.text for x in soup.find_all('div', class_="Text__sc-vycpdy-0 gwvMGj")]

    periods = soup.find_all('div', class_="resultItemSummarystyled__StyledDepositColumn-sc-1dxdkfw-1 leoBvK")
    periods = [x.find('div', class_="Text__sc-vycpdy-0 grPHnF").text for x in periods]

    amount = soup.find_all('div', class_="resultItemSummarystyled__StyledDepositColumn-sc-1dxdkfw-1 egxKuY")
    amount = [x.find('div', class_="Text__sc-vycpdy-0 grPHnF").text for x in amount]

    df = pd.DataFrame(
        data={
            "bank_name": bank_name, 
            "rate": rate, 
            "periods": periods, 
            "amount": amount
        }
    )

    return df