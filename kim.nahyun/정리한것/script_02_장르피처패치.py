import json

nb_path = 'c:/Users/82109/OneDrive/바탕 화면/study_git/SKAX/06.이탈예측.ipynb'

with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# 1. 장르 비율 로드 셀 (현재 셀 33 markdown "2-5" 뒤, 셀 34 code 앞에 삽입)
genre_cell_code = """# ── 2-5-0. 장르 비율 피처 (DB에서 로드) ──────────────────────────────
import sqlite3

db_path = 'integrated_analysis_통합본.db'
conn = sqlite3.connect(db_path)
genre_cols = ['uid', 'USER_ID',
              'ratio_action_violent', 'ratio_family_drama', 'ratio_kids',
              'ratio_romance', 'ratio_thriller', 'ratio_documentary',
              'ratio_comedy', 'ratio_etc']
genre_feat = conn.execute(
    f"SELECT {', '.join(genre_cols)} FROM user_mapping"
).fetchall()
conn.close()

genre_feat = __import__('pandas').DataFrame(genre_feat, columns=genre_cols)
genre_feat['USER_ID'] = genre_feat['USER_ID'].astype(int)

ratio_cols = [c for c in genre_cols if c.startswith('ratio_')]
print(f'장르 비율 피처 로드 완료: {genre_feat.shape}')
print('결측치:', genre_feat[ratio_cols].isnull().sum().sum())
"""

genre_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": genre_cell_code
}

# 현재 셀 구조: ... [33]markdown 2-5 [34]code merge [35]code empty
# 삽입 위치: 34 앞에 (현재 셀 33 바로 뒤)
nb['cells'].insert(34, genre_cell)

# 2. 셀 34(→35로 밀림)의 최종 병합 코드에 genre merge 추가
merge_cell = nb['cells'][35]
old_src = ''.join(merge_cell['source'])

# view_feat 다음에 genre_feat merge 추가
old_merge_line = "feature_df = feature_df.merge(view_feat, on='USER_ID', how='left')"
new_merge_lines = """feature_df = feature_df.merge(view_feat, on='USER_ID', how='left')
feature_df = feature_df.merge(genre_feat[['USER_ID'] + ratio_cols], on='USER_ID', how='left')"""

new_src = old_src.replace(old_merge_line, new_merge_lines)

# ratio 컬럼 fillna 추가 (cold_start fillna 앞에)
old_fillna = "feature_df['cold_start'] = feature_df['cold_start'].fillna(0).astype(int)"
new_fillna = """for col in ratio_cols:
    feature_df[col] = feature_df[col].fillna(0)
feature_df['cold_start'] = feature_df['cold_start'].fillna(0).astype(int)"""

new_src = new_src.replace(old_fillna, new_fillna)

merge_cell['source'] = new_src

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("패치 완료")
print(f"총 셀 수: {len(nb['cells'])}")
