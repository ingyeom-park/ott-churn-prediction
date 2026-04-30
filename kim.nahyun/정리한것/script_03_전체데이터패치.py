import json, sys

nb_path = 'c:/Users/82109/OneDrive/바탕 화면/study_git/SKAX/06.이탈예측.ipynb'

with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

cells = nb['cells']
print(f'패치 전 셀 수: {len(cells)}')

# ── 현재 셀 인덱스 파악 ──
# 패치 대상:
#  [28] code  cold_start
#  [29] md    "2-4. RFM 피처"          → "2-3-1. 주차별" md 삽입 + week code 삽입
#  [30] code  sub_days RFM             → recency_days 로 교체
#  [31] md    "2-5. 최종 피처"
#  [32] code  final merge              → genre 로드 셀 삽입 + merge 수정

# ─── Step 1: 셀 29(md RFM) 앞에 주차별 셀 2개 삽입 ───────────────────────────
# 삽입 위치 찾기: "2-4. RFM 피처" markdown 셀
rfm_md_idx = None
for i, c in enumerate(cells):
    if c['cell_type'] == 'markdown' and 'RFM' in ''.join(c['source']):
        rfm_md_idx = i
        break

if rfm_md_idx is None:
    print('ERROR: RFM markdown 셀을 찾을 수 없음')
    sys.exit(1)

print(f'RFM markdown 셀 인덱스: {rfm_md_idx}')

# 주차별 markdown 셀
week_md = {
    "cell_type": "markdown",
    "metadata": {},
    "source": "### 2-3-1. 주차별 시청 시간 & 리텐션 피처\n"
}

# 주차별 code 셀
week_code = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": (
        "# 가입일 기준 W1(1~7일) / W2(8~14일) / W3(15~21일) 시청 시간 및 리텐션\n"
        "uid_reg = membership_c.merge(\n"
        "    user_mapping_c[['uid', 'USER_ID']], left_on='user_no', right_on='uid', how='left')\n"
        "uid_reg = uid_reg[['user_no', 'USER_ID', 'reg_date']].dropna(subset=['USER_ID']).copy()\n"
        "uid_reg['reg_date'] = pd.to_datetime(uid_reg['reg_date'])\n"
        "uid_reg['USER_ID'] = uid_reg['USER_ID'].astype(int)\n"
        "\n"
        "vh_w = view_history.copy()\n"
        "vh_w['watch_date'] = pd.to_datetime(vh_w['WATCH_DAY'].astype(str), format='%Y%m%d')\n"
        "vh_w = vh_w.merge(uid_reg[['USER_ID', 'reg_date']], on='USER_ID', how='left')\n"
        "vh_w = vh_w.dropna(subset=['reg_date'])\n"
        "vh_w['days_since_reg'] = (vh_w['watch_date'] - vh_w['reg_date']).dt.days\n"
        "\n"
        "vh_w['week'] = pd.cut(\n"
        "    vh_w['days_since_reg'],\n"
        "    bins=[-1, 7, 14, 21, 9999],\n"
        "    labels=['w1', 'w2', 'w3', 'w4+']\n"
        ")\n"
        "\n"
        "week_dur = (\n"
        "    vh_w.groupby(['USER_ID', 'week'])['DURATION']\n"
        "    .sum()\n"
        "    .unstack(fill_value=0)\n"
        "    .reindex(columns=['w1', 'w2', 'w3', 'w4+'], fill_value=0)\n"
        ")\n"
        "week_dur.columns = ['dur_w1', 'dur_w2', 'dur_w3', 'dur_w4plus']\n"
        "week_dur = week_dur.reset_index()\n"
        "\n"
        "week_feat_base = uid_reg[['user_no', 'USER_ID']].merge(week_dur, on='USER_ID', how='left')\n"
        "for col in ['dur_w1', 'dur_w2', 'dur_w3']:\n"
        "    week_feat_base[col] = week_feat_base[col].fillna(0)\n"
        "week_feat_base['retention_w2'] = (week_feat_base['dur_w2'] > 0).astype(int)\n"
        "week_feat_base['retention_w3'] = (week_feat_base['dur_w3'] > 0).astype(int)\n"
        "\n"
        "print(f'주차별 피처: {week_feat_base.shape}')\n"
        "print(week_feat_base[['dur_w1','dur_w2','dur_w3','retention_w2','retention_w3']].describe().round(1))\n"
    )
}

# rfm_md_idx 위치에 삽입 (그 앞에)
cells.insert(rfm_md_idx, week_code)
cells.insert(rfm_md_idx, week_md)
print(f'주차별 셀 2개 삽입 완료 (위치 {rfm_md_idx})')

# ─── Step 2: RFM 코드 셀을 recency_days 버전으로 교체 ───────────────────────
# 삽입 후 RFM code 셀 위치 = rfm_md_idx + 2 + 1
rfm_code_idx = rfm_md_idx + 3  # md(RFM) + 1
rfm_code_cell = cells[rfm_code_idx]
rfm_src = ''.join(rfm_code_cell['source'])
if 'sub_days' in rfm_src or 'RFM' in rfm_src:
    print(f'RFM code 셀 인덱스: {rfm_code_idx}')
    new_rfm_src = (
        "# R (Recency)   = recency_days: 마지막 시청 경과 일수 (sub_days 변별력 없어 교체)\n"
        "# F (Frequency) = watch_count\n"
        "# M (Monetary)  = amount_krw\n"
        "\n"
        "vh_r = view_history.copy()\n"
        "vh_r['watch_date'] = pd.to_datetime(vh_r['WATCH_DAY'].astype(str), format='%Y%m%d')\n"
        "ref_date = vh_r['watch_date'].max()\n"
        "last_watch = vh_r.groupby('USER_ID')['watch_date'].max().rename('last_watch_date')\n"
        "\n"
        "ms_uid_r = membership_c.merge(user_mapping_c, left_on='user_no', right_on='uid', how='left')\n"
        "ms_uid_r = ms_uid_r.merge(last_watch, on='USER_ID', how='left')\n"
        "ms_uid_r['last_watch_date'] = pd.to_datetime(ms_uid_r['last_watch_date'])\n"
        "ms_uid_r['recency_days'] = (ref_date - ms_uid_r['last_watch_date']).dt.days\n"
        "\n"
        "max_recency = ms_uid_r['recency_days'].max()\n"
        "ms_uid_r['recency_days'] = ms_uid_r['recency_days'].fillna(max_recency + 1)\n"
        "\n"
        "recency_feat = ms_uid_r[['user_no', 'recency_days']].drop_duplicates('user_no')\n"
        "print(f'recency_feat: {recency_feat.shape}')\n"
        "print(recency_feat['recency_days'].describe().round(1))\n"
    )
    rfm_code_cell['source'] = new_rfm_src
    print('RFM 코드 교체 완료')
else:
    print(f'WARNING: 셀 {rfm_code_idx} 내용 예상과 다름')
    print(rfm_src[:100])

# ─── Step 3: 장르 로드 셀 삽입 + 최종 merge 수정 ────────────────────────────
# 최종 merge md 찾기
merge_md_idx = None
for i, c in enumerate(cells):
    if c['cell_type'] == 'markdown' and '2-5' in ''.join(c['source']):
        merge_md_idx = i
        break

if merge_md_idx is None:
    print('ERROR: 2-5 markdown 셀을 찾을 수 없음')
else:
    print(f'2-5 merge markdown 셀 인덱스: {merge_md_idx}')
    merge_code_idx = merge_md_idx + 1

    # 장르 로드 셀 삽입 (merge md 바로 뒤, merge code 앞)
    genre_load_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": (
            "# ── 2-5-0. 장르 비율 피처 (DB에서 로드) ──────────────────────\n"
            "import sqlite3\n"
            "\n"
            "db_path = 'integrated_analysis_통합본.db'\n"
            "conn = sqlite3.connect(db_path)\n"
            "ratio_cols = ['ratio_action_violent', 'ratio_family_drama', 'ratio_kids',\n"
            "              'ratio_romance', 'ratio_thriller', 'ratio_documentary',\n"
            "              'ratio_comedy', 'ratio_etc']\n"
            "genre_feat = pd.read_sql(\n"
            "    f\"SELECT USER_ID, {', '.join(ratio_cols)} FROM user_mapping\",\n"
            "    conn\n"
            ")\n"
            "conn.close()\n"
            "\n"
            "genre_feat['USER_ID'] = genre_feat['USER_ID'].astype(int)\n"
            "print(f'장르 비율 피처: {genre_feat.shape}')\n"
            "print('결측치:', genre_feat[ratio_cols].isnull().sum().sum())\n"
        )
    }
    cells.insert(merge_code_idx, genre_load_cell)
    print(f'장르 로드 셀 삽입 완료 (위치 {merge_code_idx})')

    # merge code 셀 (장르 삽입 후 +1 밀림)
    final_merge_idx = merge_code_idx + 1
    final_merge_cell = cells[final_merge_idx]
    old_src = ''.join(final_merge_cell['source'])

    # view_feat merge 뒤에 genre merge 추가
    old_line = "feature_df = feature_df.merge(view_feat, on='USER_ID', how='left')"
    new_lines = (
        "feature_df = feature_df.merge(view_feat, on='USER_ID', how='left')\n"
        "feature_df = feature_df.merge(genre_feat, on='USER_ID', how='left')"
    )
    new_src = old_src.replace(old_line, new_lines, 1)

    # recency_feat merge 추가 (cold_feat merge 뒤에)
    old_cold = "    cold_feat[['USER_ID','days_to_first_watch'"
    if 'recency_feat' not in new_src:
        # week_feat_base merge가 있는지 확인
        if 'week_feat_base' not in new_src:
            # cold_feat merge 줄 찾아서 뒤에 recency, week 추가
            old_cold_block = (
                "feature_df = feature_df.merge(\n"
                "    cold_feat[['USER_ID','days_to_first_watch'"
            )
            # 패턴이 다를 수 있으니 단순 append 방식
            # fillna 블록 앞에 삽입
            fillna_marker = "view_cols = ["
            recency_week_merge = (
                "feature_df = feature_df.merge(recency_feat, on='user_no', how='left')\n"
                "feature_df = feature_df.merge(\n"
                "    week_feat_base[['user_no','dur_w1','dur_w2','dur_w3','retention_w2','retention_w3']],\n"
                "    on='user_no', how='left')\n\n"
            )
            new_src = new_src.replace(fillna_marker, recency_week_merge + fillna_marker, 1)

    # ratio_cols fillna 추가
    old_fillna_cold = "feature_df['cold_start'] = feature_df['cold_start'].fillna(0).astype(int)"
    if "ratio_cols" not in new_src and old_fillna_cold in new_src:
        new_src = new_src.replace(
            old_fillna_cold,
            "for col in ratio_cols:\n"
            "    feature_df[col] = feature_df[col].fillna(0)\n"
            + old_fillna_cold,
            1
        )

    # dur_w1~w3 fillna (없으면 추가)
    if "for col in ['dur_w1'" not in new_src:
        watch_per_day_line = "feature_df['watch_per_day'] ="
        new_src = new_src.replace(
            watch_per_day_line,
            "for col in ['dur_w1', 'dur_w2', 'dur_w3']:\n"
            "    feature_df[col] = feature_df[col].fillna(0)\n"
            "feature_df['retention_w2'] = (feature_df['dur_w2'] > 0).astype(int)\n"
            "feature_df['retention_w3'] = (feature_df['dur_w3'] > 0).astype(int)\n"
            + watch_per_day_line,
            1
        )

    final_merge_cell['source'] = new_src
    print('최종 merge 셀 수정 완료')

nb['cells'] = cells
with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f'\n패치 후 총 셀 수: {len(nb["cells"])}')
print('완료')
