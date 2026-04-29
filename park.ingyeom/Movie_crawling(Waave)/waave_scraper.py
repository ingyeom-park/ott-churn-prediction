import json
import time
import random
import urllib.request
import urllib.parse
import csv
import os
import sys

# ─────────────────────────────────────────────
# 설정 (필요 시 수정)
# ─────────────────────────────────────────────
INPUT_FILE   = r"Movie_crawling(Waave)/movie_list_unique.txt"        # 제목 리스트 파일 경로
OUTPUT_CSV   = r"Movie_crawling(Waave)/wavve_movies.csv"        # 결과 CSV 파일 경로
NOTFOUND_TXT = r"Movie_crawling(Waave)/wavve_notfound.txt"      # 검색 0건 제목 목록
CHECKPOINT   = r"Movie_crawling(Waave)/wavve_checkpoint.json"  # 중간 저장 파일 (재시작 시 이어서 진행)
DELAY_MIN    = 0.6                       # 요청 간 최소 딜레이 (초)
DELAY_MAX    = 1.3                       # 요청 간 최대 딜레이 (초)
MAX_RESULTS  = 20                        # 제목 하나당 최대 검색 결과 수
 
# ─────────────────────────────────────────────
# API 공통 설정
# ─────────────────────────────────────────────
BASE_PARAMS = (
    "apikey=E5F3E0D30947AA5440556471321BB6D9"
    "&device=pc&partner=pooq&region=kor&targetage=all"
    "&pooqzone=none&guid=4abffc45-33d6-11f1-b6da-82dc0bcbe019"
    "&drm=wm&client_version=7.2.60"
)
HEADERS = {
    "accept": "application/json",
    "origin": "https://www.wavve.com",
    "referer": "https://www.wavve.com/",
    "authorization": "Bearer none",
    "wavve-credential": "none",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    ),
}
 
CSV_COLUMNS = [
    "query_title", "movieid", "title", "grouptitle", "origintitle",
    "releasedate", "originalreleaseyear", "country", "targetage",
    "playtime_sec", "genre", "tags", "directors", "actors",
    "issubtitle", "subtitles", "audios", "ismultiaudiotrack", "isatmos",
    "qualities", "downloadable", "drms", "moviemarks",
    "previewstarttime", "previewendtime", "creditstarttime", "creditendtime",
    "kmrbcode", "image", "synopsis", "price",
]
 
# ─────────────────────────────────────────────
# 유틸리티
# ─────────────────────────────────────────────
def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if attempt == retries - 1:
                print(f"    [ERROR] {url[:80]}... → {e}")
                return None
            wait = 2 ** attempt + random.uniform(0, 1)
            time.sleep(wait)
 
def search_movie(title):
    kw = urllib.parse.quote(title)
    movieids = []
    for mtype in ("svod", "ppv"):
        url = (
            f"https://apis.wavve.com/fz/search/band.js?{BASE_PARAMS}"
            f"&keyword={kw}&type=movie&mtype={mtype}&orderby=score"
            f"&limit={MAX_RESULTS}&offset=0&data=catalog"
        )
        data = fetch(url)
        if not data:
            continue
        for cell in data.get("band", {}).get("celllist", []):
            for ev in cell.get("event_list", []):
                if ev.get("type") == "on-navigation":
                    parsed = urllib.parse.parse_qs(
                        urllib.parse.urlparse(ev["url"]).query
                    )
                    mid = parsed.get("movieid", [None])[0]
                    if mid and mid not in movieids:
                        movieids.append(mid)
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
    return movieids
 
def get_detail(movieid):
    url = f"https://apis.wavve.com/fz/movie/contents/{movieid}?{BASE_PARAMS}"
    return fetch(url)
 
def join_list(obj):
    if isinstance(obj, dict) and "list" in obj:
        return "|".join(item.get("text", "") for item in obj["list"])
    return ""
 
def flatten(detail, query_title):
    d = detail
    return {
        "query_title":        query_title,
        "movieid":            d.get("movieid", ""),
        "title":              d.get("title", ""),
        "grouptitle":         d.get("grouptitle", ""),
        "origintitle":        d.get("origintitle", ""),
        "releasedate":        d.get("releasedate", ""),
        "originalreleaseyear": d.get("originalreleaseyear", ""),
        "country":            d.get("country", ""),
        "targetage":          d.get("targetage", ""),
        "playtime_sec":       d.get("playtime", ""),
        "genre":              join_list(d.get("genre", {})),
        "tags":               join_list(d.get("tags", {})),
        "directors":          join_list(d.get("directors", {})),
        "actors":             join_list(d.get("actors", {})),
        "issubtitle":         d.get("issubtitle", ""),
        "subtitles":          "|".join(
                                  s.get("subtitleLang", "")
                                  for s in d.get("subtitles", [])
                              ),
        "audios":             "|".join(
                                  a.get("audioLang", "")
                                  for a in d.get("audios", [])
                              ),
        "ismultiaudiotrack":  d.get("ismultiaudiotrack", ""),
        "isatmos":            d.get("isatmos", ""),
        "qualities":          "|".join(
                                  q.get("id", "")
                                  for q in d.get("qualities", {}).get("list", [])
                              ),
        "downloadable":       d.get("downloadable", ""),
        "drms":               d.get("drms", ""),
        "moviemarks":         "|".join(d.get("moviemarks", [])),
        "previewstarttime":   d.get("previewstarttime", ""),
        "previewendtime":     d.get("previewendtime", ""),
        "creditstarttime":    d.get("creditstarttime", ""),
        "creditendtime":      d.get("creditendtime", ""),
        "kmrbcode":           d.get("kmrbcode", ""),
        "image":              d.get("image", ""),
        "synopsis":           d.get("synopsis", "").replace("\n", " "),
        "price":              d.get("price", ""),
    }
 
# ─────────────────────────────────────────────
# 체크포인트 로드 / 저장
# ─────────────────────────────────────────────
def load_checkpoint():
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"done_titles": [], "not_found": []}
 
def save_checkpoint(done_titles, not_found):
    with open(CHECKPOINT, "w", encoding="utf-8") as f:
        json.dump({"done_titles": done_titles, "not_found": not_found}, f, ensure_ascii=False)
 
# ─────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    titles = [line.strip() for line in f if line.strip() and line.strip() != "TITLE"]
 
checkpoint = load_checkpoint()
done_set   = set(checkpoint["done_titles"])
not_found  = checkpoint["not_found"]
 
csv_exists  = os.path.exists(OUTPUT_CSV)
csv_file    = open(OUTPUT_CSV, "a", encoding="utf-8-sig", newline="")
writer      = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
if not csv_exists:
    writer.writeheader()
 
notfound_file = open(NOTFOUND_TXT, "a", encoding="utf-8")
 
total      = len(titles)
processed  = len(done_set)
api_calls  = 0
 
print(f"총 제목: {total}개 | 이미 완료: {processed}개 | 남은 것: {total - processed}개")
print("─" * 60)
 
for i, title in enumerate(titles, 1):
    if title in done_set:
        continue
 
    movieids = search_movie(title)
    api_calls += 1
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
 
    if not movieids:
        not_found.append(title)
        notfound_file.write(title + "\n")
        notfound_file.flush()
        done_set.add(title)
        print(f"[{i:05d}/{total}] ✗ 0건  {title}")
    else:
        found_count = 0
        for mid in movieids:
            detail = get_detail(mid)
            api_calls += 1
            if detail and detail.get("movieid"):
                row = flatten(detail, title)
                writer.writerow(row)
                csv_file.flush()
                found_count += 1
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
        done_set.add(title)
        print(f"[{i:05d}/{total}] ✓ {found_count}건  {title}")
 
    # 100개마다 체크포인트 저장
    if i % 100 == 0:
        save_checkpoint(list(done_set), not_found)
        print(f"  >>> 체크포인트 저장 완료 (API 누적 호출: {api_calls}회)")
 
csv_file.close()
notfound_file.close()
save_checkpoint(list(done_set), not_found)
 
print("─" * 60)
print(f"완료. CSV: {OUTPUT_CSV} | 미발견: {NOTFOUND_TXT} ({len(not_found)}개)")