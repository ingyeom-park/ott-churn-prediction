import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('c:/Users/82109/OneDrive/바탕 화면/study_git/SKAX/06.이탈예측.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

cells = nb['cells']

# 1. 셀 34 삭제 (DB ratio 로드)
del cells[34]

# 2. 장르 피처 md + code 삽입
genre_md_src = '### 2-5-0. 장르 빈도 피처 (integrated_user_data 기반)\n'
genre_code_src = '\n'.join([
    '# (USER_ID, MOVIE_ID) 중복 제거 후 장르별 등장 횟수 / 고유 영화 수 = 빈도 비율',
    'import sqlite3',
    '',
    "conn = sqlite3.connect('integrated_analysis_통합본.db')",
    'raw_genre = pd.read_sql(',
    "    'SELECT USER_ID, MOVIE_ID, GENRE FROM integrated_user_data WHERE GENRE IS NOT NULL',",
    '    conn',
    ')',
    'conn.close()',
    '',
    'TARGET_GENRES = [',
    "    '드라마', '액션', '스릴러', '코미디', '로맨스',",
    "    '다큐멘터리', '공포', '범죄', 'SF', '판타지',",
    "    '가족', '애니메이션', '역사', '전쟁'",
    ']',
    '',
    "movies_g = raw_genre.drop_duplicates(subset=['USER_ID','MOVIE_ID']).copy()",
    "movies_g['genre_list'] = movies_g['GENRE'].str.split(',')",
    "exploded_g = movies_g.explode('genre_list')",
    "exploded_g['genre_list'] = exploded_g['genre_list'].str.strip()",
    "exploded_g = exploded_g[exploded_g['genre_list'].isin(TARGET_GENRES)]",
    '',
    "genre_count = exploded_g.groupby(['USER_ID','genre_list']).size().unstack(fill_value=0)",
    "genre_count.columns = ['genre_' + c for c in genre_count.columns]",
    "total_movies_g = movies_g.groupby('USER_ID')['MOVIE_ID'].nunique()",
    "genre_ratio = genre_count.div(total_movies_g, axis=0).fillna(0).reset_index()",
    "genre_cols = [c for c in genre_ratio.columns if c.startswith('genre_')]",
    '',
    "print(f'장르 피처 생성 완료: {genre_ratio.shape}')",
    'print(genre_ratio.head(2))',
]) + '\n'

cells.insert(34, {'cell_type':'code','execution_count':None,'metadata':{},'outputs':[],'source':genre_code_src})
cells.insert(34, {'cell_type':'markdown','metadata':{},'source':genre_md_src})

# 3. merge 셀 수정 (셀 36)
src = ''.join(cells[36]['source'])
src = src.replace(
    "feature_df = feature_df.merge(genre_feat, on='USER_ID', how='left')",
    "feature_df = feature_df.merge(genre_ratio, on='USER_ID', how='left')"
)
src = src.replace(
    'for col in ratio_cols:\n    feature_df[col] = feature_df[col].fillna(0)',
    'for col in genre_cols:\n    feature_df[col] = feature_df[col].fillna(0)'
)
cells[36]['source'] = src

with open('c:/Users/82109/OneDrive/바탕 화면/study_git/SKAX/06.이탈예측.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print('완료. 총 셀 수:', len(cells))
for i in [33,34,35,36]:
    c = cells[i]
    s = c['source'] if isinstance(c['source'], str) else ''.join(c['source'])
    print(f'[{i}] ({c["cell_type"]}) {s[:70]}')
