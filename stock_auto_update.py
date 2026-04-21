import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from bs4 import BeautifulSoup
import datetime
import time
import os
import json

def update_unique_stock_data(stock_code, sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # --- 핵심 수정 부분: GitHub Secrets 또는 로컬 파일에서 인증 정보 가져오기 ---
    google_auth_json = os.environ.get('GOOGLE_AUTH')
    
    if google_auth_json:
        # GitHub Actions에서 실행될 때 (Secrets 사용)
        info = json.loads(google_auth_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
    else:
        # 내 컴퓨터에서 실행될 때 (파일 사용)
        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    
    try:
        client = gspread.authorize(creds)
        spreadsheet = client.open(sheet_name)
        sheet = spreadsheet.get_worksheet(0)
    except Exception as e:
        print(f"연결 실패: {e}")
        return

    # 이후 크롤링 및 업데이트 로직은 이전과 동일합니다.
    existing_dates = sheet.col_values(1)
    headers = {'User-Agent': 'Mozilla/5.0'}
    new_records = []
    
    for page in range(1, 3): # 최근 2페이지 확인
        url = f"https://finance.naver.com/item/sise_day.naver?code={stock_code}&page={page}"
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.find_all('tr', {'onmouseover': 'mouseOver(this)'})
        
        for row in rows:
            cols = row.find_all('span')
            if len(cols) > 1:
                date = cols[0].text.strip().replace("-", ".")
                price = cols[1].text.strip().replace(",", "")
                if date not in existing_dates:
                    new_records.append([date, int(price)])
        time.sleep(0.3)

    if new_records:
        new_records.sort(key=lambda x: x[0])
        sheet.append_rows(new_records)
        print(f"{len(new_records)}건 추가 완료!")
    else:
        print("최신 상태입니다.")

STOCK_CODE = "0144L0"
SHEET_NAME = "KODEX 미국성장커버드콜액티브 종가 기록"
update_unique_stock_data(STOCK_CODE, SHEET_NAME)
