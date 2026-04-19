import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from bs4 import BeautifulSoup
import datetime
import time

def update_unique_stock_data(stock_code, sheet_name):
    # 1. 구글 시트 연결 설정
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open(sheet_name)
        sheet = spreadsheet.get_worksheet(0)
    except Exception as e:
        print(f"구글 시트 연결 실패: {e}")
        return

    # 2. 시트에 이미 기록된 날짜들 가져오기 (중복 체크용)
    # A열의 모든 값을 가져와서 리스트로 만듭니다.
    existing_dates = sheet.col_values(1) 

    # 3. 네이버 증권에서 최근 일별 시세 가져오기 (최근 약 한 달치 = 3페이지)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    new_records = []
    
    print(f"[{stock_code}] 최근 한 달간의 데이터를 확인 중입니다...")
    
    for page in range(3, 0, -1): # 과거 페이지(3)부터 현재(1) 순으로 훑음
        url = f"https://finance.naver.com/item/sise_day.naver?code={stock_code}&page={page}"
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.find_all('tr', {'onmouseover': 'mouseOver(this)'})
        
        for row in rows:
            cols = row.find_all('span')
            if len(cols) > 1:
                date = cols[0].text.strip().replace("-", ".") # 형식 통일 (2026.04.19)
                price = cols[1].text.strip().replace(",", "")
                
                # 중복 확인: 시트에 없는 날짜만 추가 목록에 넣음
                if date not in existing_dates:
                    new_records.append([date, int(price)])
                    existing_dates.append(date) # 이번 실행 중에 추가된 것도 중복 방지
        time.sleep(0.3)

    # 4. 새로운 데이터가 있다면 시트에 한꺼번에 추가
    if new_records:
        # 날짜순으로 정렬 (오래된 날짜가 위로 가게)
        new_records.sort(key=lambda x: x[0])
        
        # append_rows를 사용하면 여러 줄을 한 번에 추가하여 속도가 빠릅니다.
        sheet.append_rows(new_records)
        print(f"총 {len(new_records)}건의 새로운 기록이 추가되었습니다.")
    else:
        print("이미 모든 데이터가 최신 상태입니다. 추가할 새로운 날짜가 없습니다.")

# 실행
STOCK_CODE = "0144L0"
SHEET_NAME = "KODEX 미국성장커버드콜액티브 종가 기록"

update_unique_stock_data(STOCK_CODE, SHEET_NAME)