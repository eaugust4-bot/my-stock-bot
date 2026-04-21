import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from bs4 import BeautifulSoup
import datetime
import time
import os
import json

def update_unique_stock_data(stock_code, sheet_name):
    # 1. 구글 시트 연결 설정 (범위 설정)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # --- [수정된 부분] GitHub Secrets와 내 컴퓨터 파일 모두 대응 가능하게 함 ---
    google_auth_json = os.environ.get('GOOGLE_AUTH')
    
    try:
        if google_auth_json:
            # GitHub Actions에서 실행될 때 (Secrets에 저장한 JSON 사용)
            info = json.loads(google_auth_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
        else:
            # 내 컴퓨터에서 실행될 때 (기존 방식: 파일 사용)
            creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
            
        client = gspread.authorize(creds)
        spreadsheet = client.open(sheet_name)
        sheet = spreadsheet.get_worksheet(0)
    except Exception as e:
        print(f"연결 실패: {e}")
        return

    # 2. 시트에 이미 기록된 날짜들 가져오기
    existing_dates = sheet.col_values(1) 

    # 3. 네이버 증권 데이터 가져오기
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    new_records = []
    
    print(f"[{stock_code}] 데이터를 확인 중입니다...")
    
    for page in range(3, 0, -1): 
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
                    existing_dates.append(date)
        time.sleep(0.3)

    # 4. 데이터 추가
    if new_records:
        new_records.sort(key=lambda x: x[0])
        sheet.append_rows(new_records)
        print(f"성공: {len(new_records)}건의 데이터가 시트에 기록되었습니다.")
    else:
        print("최신 상태: 추가할 데이터가 없습니다.")

# 실행 설정
STOCK_CODE = "0144L0"
SHEET_NAME = "KODEX 미국성장커버드콜액티브 종가 기록"

update_unique_stock_data(STOCK_CODE, SHEET_NAME)
