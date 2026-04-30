import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

nb_path = 'c:/Users/82109/OneDrive/바탕 화면/study_git/SKAX/06.이탈예측.ipynb'

with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

cells = nb['cells']
new_cells = []
inserted = False

GENRE_CODE = (
    "# (USER_ID, MOVIE_ID) 중복 제거 후 장르별 등장 횟수 / 고유 영화 수 = 빈도 비율\n"
    "import sqlite3\n\n"
    "conn = sqlite3.connect('integrated_analysis_통합본.db')\n"
    "raw_genre = pd.read_sql(\n"
    "    'SELECT USER_ID, MOVIE_ID, GENRE FROM integrated_user_data WHERE GENRE IS NOT NULL',\n"
    "    conn\n"
    ")\n"
    "conn.close()\n\n"
    "TARGET_GENRES = [\n"
    "    '드라마','액션','스릴러','코미디','로맨스',\n"
    "    '다큐멘터리','공포','범죄','SF','판타지',\n"
    "    '가족','애니메이션','역사','전쟁'\n"
    "]\n"
    "movies_g = raw_genre.drop_duplicates(subset=['USER_ID','MOVIE_ID']).copy()\n"
    "movies_g['genre_list'] = movies_g['GENRE'].str.split(',')\n"
    "exploded_g = movies_g.explode('genre_list')\n"
    "exploded_g['genre_list'] = exploded_g['genre_list'].str.strip()\n"
    "exploded_g = exploded_g[exploded_g['genre_list'].isin(TARGET_GENRES)]\n"
    "genre_count = exploded_g.groupby(['USER_ID','genre_list']).size().unstack(fill_value=0)\n"
    "genre_count.columns = ['genre_' + c for c in genre_count.columns]\n"
    "total_movies_g = movies_g.groupby('USER_ID')['MOVIE_ID'].nunique()\n"
    "genre_ratio = genre_count.div(total_movies_g, axis=0).fillna(0).reset_index()\n"
    "genre_cols = [c for c in genre_ratio.columns if c.startswith('genre_')]\n"
    "print(f'장르 피처 생성 완료: {genre_ratio.shape}')\n"
    "print(genre_ratio.head(2))\n"
)

for c in cells:
    s = c['source'] if isinstance(c['source'], str) else ''.join(c['source'])

    # 제거: 구버전 DB ratio 로드 셀 (ratio_cols + sqlite3 + user_mapping)
    if 'ratio_cols' in s and 'sqlite3' in s and 'user_mapping' in s:
        print(f'삭제 (구버전 DB ratio): {s[:50]}')
        continue

    # 제거: 빈 셀
    if s.strip() == '':
        print('빈셀 삭제')
        continue

    # 제거: 중복 장르 빈도 셀
    if '장르 빈도 피처' in s and inserted:
        print(f'삭제 (중복 장르): {s[:50]}')
        continue
    if 'integrated_user_data' in s and 'GENRE' in s and inserted:
        print(f'삭제 (중복 장르코드): {s[:50]}')
        continue

    # 삽입 위치: "2-5. 최종 피처" markdown 뒤
    if '2-5. 최종 피처' in s and not inserted:
        new_cells.append(c)
        new_cells.append({
            'cell_type': 'markdown', 'metadata': {},
            'source': '### 2-5-0. 장르 빈도 피처 (integrated_user_data 기반)\n'
        })
        new_cells.append({
            'cell_type': 'code', 'execution_count': None,
            'metadata': {}, 'outputs': [],
            'source': GENRE_CODE
        })
        inserted = True
        continue

    # merge 셀 수정
    if 'genre_feat' in s or 'ratio_cols' in s:
        s = s.replace(
            "feature_df = feature_df.merge(genre_feat, on='USER_ID', how='left')",
            "feature_df = feature_df.merge(genre_ratio, on='USER_ID', how='left')"
        )
        s = s.replace(
            'for col in ratio_cols:\n    feature_df[col] = feature_df[col].fillna(0)',
            'for col in genre_cols:\n    feature_df[col] = feature_df[col].fillna(0)'
        )
        c['source'] = s

    new_cells.append(c)

nb['cells'] = new_cells

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f'\n완료. 총 셀: {len(new_cells)}')
for i, c in enumerate(new_cells):
    s = c['source'] if isinstance(c['source'], str) else ''.join(c['source'])
    if any(k in s for k in ['2-5', '장르', 'genre_ratio', 'membership_c 기준']):
        print(f'[{i}] ({c["cell_type"]}) {s[:75]}')
