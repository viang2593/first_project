from flask import Flask, render_template, request
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3

app = Flask(__name__)

# 步驟 1：定義資料庫結構並創建資料庫引擎
engine = create_engine('sqlite:///stock_data.db', echo=True)
Base = declarative_base()

class StockData(Base):
    __tablename__ = 'StockData'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String)
    company_name = Column(String)
    volume = Column(String)
    final_price = Column(String)
    open_price = Column(String)
    high_price = Column(String)
    low_price = Column(String)
    yesterday_close_price = Column(String)
    change = Column(String)
    change_rate = Column(String)
    updated_time = Column(DateTime, default=datetime.now)

# 確保資料庫初始化
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# 步驟 2：爬取和存儲數據
def get_stock_data(stock_code):
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless")
    browser = webdriver.Chrome(options=chrome_options)
    browser.get(f"https://tw.stock.yahoo.com/quote/{stock_code}")

    wait = WebDriverWait(browser, 10)
    element = wait.until(EC.presence_of_element_located((By.ID, "layout-col1")))

    html_source = browser.page_source
    element_soup = BeautifulSoup(html_source, 'html.parser')

    code = element_soup.find('div', {'id': 'layout-col1'}).find('span', class_='C($c-icon) Fz(24px) Mend(20px)').text
    company_name = element_soup.find('div', {'id': 'layout-col1'}).find('h1').text
    volume1 = element_soup.find('div', {'id': 'layout-col1'}).find('div', class_='D(f) Fld(c) Ai(c) Fw(b) Pend(8px) Bdendc($bd-primary-divider) Bdends(s) Bdendw(1px)')
    volume2 = volume1.find('span', class_='Fz(16px) C($c-link-text) Mb(4px)').text
    price_li_tags = element_soup.find('ul', {'class': 'D(f) Fld(c) Flw(w) H(192px) Mx(-16px)'}).find_all('li', {'class': 'price-detail-item'})
    final = price_li_tags[0]
    fina2 = final.text
    open1 = price_li_tags[1]
    open2 = open1.text
    hight1 = price_li_tags[2]
    hight2 = hight1.text
    low1 = price_li_tags[3]
    low2 = low1.text
    yester1 = price_li_tags[6]
    yester2 = yester1.text
    tread1 = price_li_tags[8]
    tread2 = tread1.text.replace('漲跌', '').strip()
    tread3 = element_soup.select('span[class*="Fz(20px) Fw(b) Lh(1.2) Mend(4px) D(f) Ai(c)"]')
    if 'C($c-trend-up)' in tread3[0].attrs['class']:
        change = '+' + tread2
    elif 'C($c-trend-down)' in tread3[0].attrs['class']:
        change = '-' + tread2
    else:
        change = tread2
    rate1 = price_li_tags[7]
    rate2 = rate1.text.replace('漲跌幅', '').strip()
    rate3 = element_soup.select('span[class*="Jc(fe) Fz(20px) Lh(1.2) Fw(b) D(f) Ai(c)"]')
    if 'C($c-trend-up)' in rate3[0].attrs['class']:
        rate = '+' + rate2
    elif 'C($c-trend-down)' in rate3[0].attrs['class']:
        rate = '-' + rate2
    else:
        rate = rate2
    time1 = element_soup.find('div', {'id': 'layout-col1'}).find('span', class_='C(#6e7780) Fz(12px) Fw(b)')
    time2 = time1.text.replace('開盤 |', '').replace('收盤 |', '').strip()

    browser.quit()

    # 創建 StockData 對象並添加到資料庫
    stock_data = StockData(
        code=code,
        company_name=company_name,
        volume=volume2,
        final_price=fina2,
        open_price=open2,
        high_price=hight2,
        low_price=low2,
        yesterday_close_price=yester2,
        change=change,
        change_rate=rate,
        updated_time=datetime.now()
    )
    session.add(stock_data)
    session.commit()

    # 調試用：確認資料被正確寫入資料庫
    print(f"Stock data saved to database: {stock_data}")

    return {
        'code': code,
        'company_name': company_name,
        'volume': volume2,
        'final_price': fina2,
        'open_price': open2,
        'high_price': hight2,
        'low_price': low2,
        'yesterday_close_price': yester2,
        'change': change,
        'change_rate': rate,
        'updated_time': time2
    }

# 步驟 3：從資料庫中讀取並渲染數據到網頁
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        stock_codes = []
        for i in range(1, 6):  # 假設最多可以輸入五支股票代碼
            stock_code = request.form.get(f'stock_code_{i}')
            if stock_code:
                stock_codes.append(stock_code)

        stock_data_list = []
        for stock_code in stock_codes:
            stock_data = get_stock_data(stock_code)
            stock_data_list.append(stock_data)

        return render_template('index.html', stock_data_list=stock_data_list)

    # 從資料庫中讀取所有股票數據
    stock_data_list = session.query(StockData).all()

    # 調試用：確認從資料庫中讀取的資料
    print(f"Stock data retrieved from database: {stock_data_list}")

    return render_template('index.html', stock_data_list=stock_data_list)

if __name__ == '__main__':
    app.run(debug=True)
