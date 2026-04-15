"""
Google Maps 중랑구 공원 리뷰 크롤러
방법: Google Places API (공식) + Selenium fallback

[사전 준비]
pip install requests googlemaps selenium webdriver-manager pandas

Google Places API 사용 시:
- https://console.cloud.google.com 에서 API 키 발급
- Places API 활성화 필요
- 무료 한도: 월 $200 크레딧 (약 5,000건 detail 조회)
"""

import requests
import time
import json
import pandas as pd
from datetime import datetime

# # ──────────────────────────────────────────
# # 방법 1: Google Places API (공식, 안정적)
# # 리뷰 최대 5개 / 장소 — 텍스트 마이닝엔 부족할 수 있음
# # ──────────────────────────────────────────

# GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"  # 여기에 API 키 입력

# # 중랑구 중심 좌표
# JUNGNANG_LAT = 37.6066
# JUNGNANG_LNG = 127.0925
# SEARCH_RADIUS = 5000  # 5km (중랑구 전체 커버)


# def search_parks_nearby(lat, lng, radius, api_key):
#     """Places API - Nearby Search로 공원 목록 수집"""
#     url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
#     parks = []
#     next_page_token = None

#     while True:
#         params = {
#             "location": f"{lat},{lng}",
#             "radius": radius,
#             "type": "park",
#             "language": "ko",
#             "key": api_key,
#         }
#         if next_page_token:
#             params["pagetoken"] = next_page_token
#             time.sleep(2)  # pagetoken은 2초 대기 필요

#         resp = requests.get(url, params=params)
#         data = resp.json()

#         if data.get("status") not in ("OK", "ZERO_RESULTS"):
#             print(f"[오류] {data.get('status')}: {data.get('error_message', '')}")
#             break

#         parks.extend(data.get("results", []))
#         next_page_token = data.get("next_page_token")

#         if not next_page_token:
#             break

#     return parks


# def get_place_reviews(place_id, api_key):
#     """Places Details API로 리뷰 최대 5개 수집"""
#     url = "https://maps.googleapis.com/maps/api/place/details/json"
#     params = {
#         "place_id": place_id,
#         "fields": "name,rating,user_ratings_total,reviews,formatted_address,geometry",
#         "language": "ko",
#         "reviews_sort": "newest",
#         "key": api_key,
#     }
#     resp = requests.get(url, params=params)
#     return resp.json().get("result", {})


# def crawl_google_maps_official(api_key=GOOGLE_API_KEY):
#     """공식 API로 중랑구 공원 리뷰 전체 수집"""
#     print("🔍 중랑구 공원 목록 검색 중...")
#     parks = search_parks_nearby(JUNGNANG_LAT, JUNGNANG_LNG, SEARCH_RADIUS, api_key)
#     print(f"  → {len(parks)}개 공원 발견")

#     all_reviews = []

#     for i, park in enumerate(parks):
#         place_id = park["place_id"]
#         park_name = park.get("name", "")
#         print(f"  [{i+1}/{len(parks)}] {park_name} 리뷰 수집 중...")

#         detail = get_place_reviews(place_id, api_key)
#         reviews = detail.get("reviews", [])

#         for r in reviews:
#             all_reviews.append({
#                 "park_name": park_name,
#                 "place_id": place_id,
#                 "address": detail.get("formatted_address", ""),
#                 "park_rating": detail.get("rating", ""),
#                 "total_ratings": detail.get("user_ratings_total", 0),
#                 "reviewer": r.get("author_name", ""),
#                 "rating": r.get("rating", ""),
#                 "text": r.get("text", ""),
#                 "time": datetime.fromtimestamp(r.get("time", 0)).strftime("%Y-%m-%d"),
#                 "source": "google_maps_api",
#             })

#         time.sleep(0.2)  # API 요청 간격

#     df = pd.DataFrame(all_reviews)
#     output_path = f"jungnang_google_reviews_{datetime.now().strftime('%Y%m%d')}.csv"
#     df.to_csv(output_path, index=False, encoding="utf-8-sig")
#     print(f"\n✅ 저장 완료: {output_path} ({len(df)}개 리뷰)")
#     return df


# ──────────────────────────────────────────
# 방법 2: Selenium 브라우저 자동화
# 리뷰 수 제한 없음, 단 구글 봇 감지 주의
# pip install selenium webdriver-manager
# ──────────────────────────────────────────

def crawl_google_maps_selenium(park_urls: list, max_reviews_per_park=50):
    """
    Selenium으로 구글 맵 리뷰 스크래핑
    
    park_urls: 구글 맵 공원 URL 리스트
    예) ["https://maps.google.com/?cid=XXXXXXX", ...]
    
    ※ 주의: Google ToS 위반 소지 있음. 연구 목적 단발성으로만 사용 권장.
    """
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # 브라우저 창 숨기려면 주석 해제
    options.add_argument("--lang=ko-KR")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    all_reviews = []

    for url in park_urls:
        try:
            driver.get(url)
            wait = WebDriverWait(driver, 10)

            # 공원 이름 추출
            park_name = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.DUwDvf"))
            ).text

            # 리뷰 탭 클릭
            review_tab = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@aria-label, '리뷰')]")
                )
            )
            review_tab.click()
            time.sleep(1.5)

            # 스크롤로 리뷰 더 불러오기
            scrollable = driver.find_element(By.CSS_SELECTOR, "div.m6QErb.DxyBCb")
            collected = 0
            prev_count = 0

            while collected < max_reviews_per_park:
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable
                )
                time.sleep(1.5)

                # "더보기" 버튼 클릭 (긴 리뷰 펼치기)
                for btn in driver.find_elements(By.CSS_SELECTOR, "button.w8nwRe"):
                    try:
                        btn.click()
                    except Exception:
                        pass

                review_elements = driver.find_elements(By.CSS_SELECTOR, "div.jJc9Ad")
                collected = len(review_elements)

                if collected == prev_count:
                    break  # 더 이상 새 리뷰 없음
                prev_count = collected

            # 리뷰 파싱
            review_elements = driver.find_elements(By.CSS_SELECTOR, "div.jJc9Ad")
            for elem in review_elements[:max_reviews_per_park]:
                try:
                    reviewer = elem.find_element(By.CSS_SELECTOR, "div.d4r55").text
                    rating_elem = elem.find_element(By.CSS_SELECTOR, "span.kvMYJc")
                    rating = rating_elem.get_attribute("aria-label").replace("별점 ", "").replace("점", "")
                    text_elems = elem.find_elements(By.CSS_SELECTOR, "span.wiI7pd")
                    text = text_elems[0].text if text_elems else ""
                    date_elems = elem.find_elements(By.CSS_SELECTOR, "span.rsqaWe")
                    date = date_elems[0].text if date_elems else ""

                    all_reviews.append({
                        "park_name": park_name,
                        "reviewer": reviewer,
                        "rating": rating,
                        "text": text,
                        "date": date,
                        "source": "google_maps_selenium",
                        "url": url,
                    })
                except Exception as e:
                    continue

            print(f"  ✅ {park_name}: {len(review_elements)}개 리뷰 수집")

        except Exception as e:
            print(f"  ❌ 오류 ({url}): {e}")
        finally:
            time.sleep(2)

    driver.quit()

    df = pd.DataFrame(all_reviews)
    output_path = f"jungnang_google_selenium_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n✅ 저장 완료: {output_path} ({len(df)}개 리뷰)")
    return df


# ──────────────────────────────────────────
# 실행 예시
# ──────────────────────────────────────────

if __name__ == "__main__":
    # 방법 1: 공식 API
    # df = crawl_google_maps_official(api_key=GOOGLE_API_KEY)

    # 방법 2: Selenium (URL 직접 입력)
    # 구글 맵에서 공원 검색 후 URL 복사
    park_urls = [
        "https://www.google.com/maps/place/중랑캠핑숲",
        "https://www.google.com/maps/place/용마폭포공원",
        "https://www.google.com/maps/place/중랑천",
        # 필요한 공원 URL 추가...
    ]
    # df = crawl_google_maps_selenium(park_urls, max_reviews_per_park=100)

    print("api_key 또는 park_urls를 설정한 후 주석을 해제하고 실행하세요.")
