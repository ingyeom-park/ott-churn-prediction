import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

nb_path = 'c:/Users/82109/OneDrive/바탕 화면/study_git/SKAX/07.신규피처EDA.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

cells = nb['cells']

# 1. 셀 1(import/load) 뒤에 dur_w4plus 계산 셀 삽입
w4_code = (
    "# dur_w4plus: 22일 이후(4주차+) 시청 시간 — View_History에서 직접 계산\n"
    "import sqlite3\n\n"
    "vh = pd.read_csv('View_History.csv')\n"
    "vh['watch_date'] = pd.to_datetime(vh['WATCH_DAY'].astype(str), format='%Y%m%d')\n\n"
    "membership_c = pd.read_csv('Membership_전처리.csv')\n"
    "user_mapping_c = pd.read_csv('User_Mapping_전처리.csv')\n"
    "uid_reg = membership_c.merge(user_mapping_c, left_on='user_no', right_on='uid', how='left')\n"
    "uid_reg = uid_reg[['user_no','USER_ID','reg_date']].dropna(subset=['USER_ID']).copy()\n"
    "uid_reg['reg_date'] = pd.to_datetime(uid_reg['reg_date'])\n"
    "uid_reg['USER_ID'] = uid_reg['USER_ID'].astype(int)\n\n"
    "vh_w4 = vh.merge(uid_reg[['USER_ID','user_no','reg_date']], on='USER_ID', how='left').dropna(subset=['reg_date'])\n"
    "vh_w4['days_since_reg'] = (vh_w4['watch_date'] - vh_w4['reg_date']).dt.days\n"
    "w4 = vh_w4[vh_w4['days_since_reg'] > 21].groupby('user_no')['DURATION'].sum().rename('dur_w4plus')\n\n"
    "df = df.merge(w4, on='user_no', how='left')\n"
    "df['dur_w4plus'] = df['dur_w4plus'].fillna(0)\n"
    "churn = df[df['is_churn'] == 1]\n"
    "stay  = df[df['is_churn'] == 0]\n"
    "print('dur_w4plus 계산 완료')\n"
    "print(df[['dur_w1','dur_w2','dur_w3','dur_w4plus']].describe().round(1))\n"
)

w4_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": w4_code
}
cells.insert(2, w4_cell)

# 2. 셀 4(markdown 2.) 제목 수정
cells[4]['source'] = "---\n## 2. 주차별 시청 시간 (dur_w1 / dur_w2 / dur_w3 / dur_w4+)\n"

# 3. 셀 5(주차별 코드) 수정 — 4주차 포함
cells[5]['source'] = (
    "week_cols = ['dur_w1', 'dur_w2', 'dur_w3', 'dur_w4plus']\n"
    "week_labels_ko = ['1주차\n(1~7일)', '2주차\n(8~14일)', '3주차\n(15~21일)', '4주차+\n(22일~)']\n\n"
    "means = pd.DataFrame({\n"
    "    '잔류': stay[week_cols].mean(),\n"
    "    '이탈': churn[week_cols].mean()\n"
    "})\n"
    "means.index = week_labels_ko\n\n"
    "fig, axes = plt.subplots(1, 2, figsize=(15, 5))\n\n"
    "means.plot(kind='bar', ax=axes[0], color=['steelblue','tomato'], edgecolor='black')\n"
    "axes[0].set_title('주차별 평균 시청 시간 (이탈 vs 잔류)')\n"
    "axes[0].set_ylabel('평균 시청 시간(분)')\n"
    "axes[0].set_xticklabels(week_labels_ko, rotation=0)\n"
    "axes[0].legend()\n\n"
    "week_labels_short = ['1주차', '2주차', '3주차', '4주차+']\n"
    "axes[1].plot(week_labels_short, stay[week_cols].mean().values,  marker='o', label='잔류', color='steelblue', linewidth=2)\n"
    "axes[1].plot(week_labels_short, churn[week_cols].mean().values, marker='o', label='이탈', color='tomato',    linewidth=2)\n"
    "axes[1].set_title('주차별 시청 시간 추이')\n"
    "axes[1].set_ylabel('평균 시청 시간(분)')\n"
    "axes[1].legend()\n"
    "axes[1].grid(alpha=0.3)\n\n"
    "plt.tight_layout()\n"
    "plt.show()\n\n"
    "print(means.round(1))\n"
)

# 4. 종합 요약 셀에서도 4주차 추가
for cell in cells:
    if cell['cell_type'] == 'code' and '주차별 시청 시간 평균' in ''.join(cell['source'] if isinstance(cell['source'], list) else [cell['source']]):
        src = cell['source'] if isinstance(cell['source'], str) else ''.join(cell['source'])
        src = src.replace(
            "for col in ['dur_w1','dur_w2','dur_w3']:",
            "for col in ['dur_w1','dur_w2','dur_w3','dur_w4plus']:"
        )
        cell['source'] = src

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print('패치 완료. 총 셀 수:', len(nb['cells']))
