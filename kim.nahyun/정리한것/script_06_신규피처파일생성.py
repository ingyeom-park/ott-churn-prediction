import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

nb_path = 'c:/Users/82109/OneDrive/바탕 화면/study_git/SKAX/07.신규피처EDA.ipynb'

def md(src):   return {"cell_type":"markdown","metadata":{},"source":src}
def code(src): return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":src}

cells = [
  md("# 07. 신규 피처 EDA\n\n## 분석 대상 피처\n- **Recency** : `recency_days`\n- **주차별 시청** : `dur_w1`, `dur_w2`, `dur_w3`, `dur_w4plus`\n- **리텐션** : `retention_w2`, `retention_w3`\n- **장르 비율** : `ratio_action_violent` 등 8개\n"),

  code("import pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nfrom matplotlib import rc\n\nrc('font', family='Malgun Gothic')\nplt.rcParams['axes.unicode_minus'] = False\n\ndf = pd.read_csv('features.csv')\nprint(f'shape: {df.shape}')\nprint(f'이탈 비율: {df[\"is_churn\"].mean():.1%}')\n\nchurn = df[df['is_churn'] == 1]\nstay  = df[df['is_churn'] == 0]\nprint(f'이탈: {len(churn):,}명 / 잔류: {len(stay):,}명')\n"),

  code("# dur_w4plus: 22일 이후(4주차+) 시청 시간\nvh = pd.read_csv('View_History.csv')\nvh['watch_date'] = pd.to_datetime(vh['WATCH_DAY'].astype(str), format='%Y%m%d')\n\nmembership_c   = pd.read_csv('Membership_전처리.csv')\nuser_mapping_c = pd.read_csv('User_Mapping_전처리.csv')\nuid_reg = membership_c.merge(user_mapping_c, left_on='user_no', right_on='uid', how='left')\nuid_reg = uid_reg[['user_no','USER_ID','reg_date']].dropna(subset=['USER_ID']).copy()\nuid_reg['reg_date'] = pd.to_datetime(uid_reg['reg_date'])\nuid_reg['USER_ID'] = uid_reg['USER_ID'].astype(int)\n\nvh_m = vh.merge(uid_reg[['USER_ID','user_no','reg_date']], on='USER_ID', how='left').dropna(subset=['reg_date'])\nvh_m['days_since_reg'] = (vh_m['watch_date'] - vh_m['reg_date']).dt.days\nw4 = vh_m[vh_m['days_since_reg'] > 21].groupby('user_no')['DURATION'].sum().rename('dur_w4plus')\n\ndf = df.merge(w4, on='user_no', how='left')\ndf['dur_w4plus'] = df['dur_w4plus'].fillna(0)\nchurn = df[df['is_churn'] == 1]\nstay  = df[df['is_churn'] == 0]\nprint('dur_w4plus 계산 완료')\nprint(df[['dur_w1','dur_w2','dur_w3','dur_w4plus']].describe().round(1))\n"),

  md("---\n## 1. Recency (마지막 시청 경과 일수)\n"),

  code("fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n\naxes[0].hist(stay['recency_days'],  bins=30, alpha=0.6, label='잔류', color='steelblue')\naxes[0].hist(churn['recency_days'], bins=30, alpha=0.6, label='이탈', color='tomato')\naxes[0].set_title('recency_days 분포 (이탈 vs 잔류)')\naxes[0].set_xlabel('마지막 시청 경과 일수')\naxes[0].set_ylabel('유저 수')\naxes[0].legend()\n\ndf['recency_bin'] = pd.cut(df['recency_days'], bins=[0,7,14,21,28,37],\n                            labels=['0-7일','8-14일','15-21일','22-28일','29일+'])\nbychurn = df.groupby('recency_bin', observed=True)['is_churn'].mean()\nbychurn.plot(kind='bar', ax=axes[1], color='coral', edgecolor='black')\naxes[1].set_title('구간별 이탈률')\naxes[1].set_ylabel('이탈률')\naxes[1].set_ylim(0, 0.6)\nfor p in axes[1].patches:\n    axes[1].annotate(f'{p.get_height():.1%}',\n                     (p.get_x()+p.get_width()/2, p.get_height()+0.01), ha='center', fontsize=11)\naxes[1].tick_params(axis='x', rotation=0)\nplt.tight_layout()\nplt.show()\nprint('이탈/잔류 recency_days 평균')\nprint(df.groupby('is_churn')['recency_days'].mean().round(1))\n"),

  md("---\n## 2. 주차별 시청 시간 (dur_w1 / dur_w2 / dur_w3 / dur_w4+)\n"),

  code("week_cols = ['dur_w1', 'dur_w2', 'dur_w3', 'dur_w4plus']\nweek_labels_ko = ['1주차(1~7일)', '2주차(8~14일)', '3주차(15~21일)', '4주차+(22일~)']\n\nmeans = pd.DataFrame({\n    '잔류': stay[week_cols].mean(),\n    '이탈': churn[week_cols].mean()\n})\nmeans.index = week_labels_ko\n\nfig, axes = plt.subplots(1, 2, figsize=(16, 5))\n\nmeans.plot(kind='bar', ax=axes[0], color=['steelblue','tomato'], edgecolor='black')\naxes[0].set_title('주차별 평균 시청 시간 (이탈 vs 잔류)')\naxes[0].set_ylabel('평균 시청 시간(분)')\naxes[0].set_xticklabels(week_labels_ko, rotation=15)\naxes[0].legend()\n\nweek_labels_short = ['1주차', '2주차', '3주차', '4주차+']\naxes[1].plot(week_labels_short, stay[week_cols].mean().values,\n             marker='o', label='잔류', color='steelblue', linewidth=2)\naxes[1].plot(week_labels_short, churn[week_cols].mean().values,\n             marker='o', label='이탈', color='tomato', linewidth=2)\naxes[1].set_title('주차별 시청 시간 추이')\naxes[1].set_ylabel('평균 시청 시간(분)')\naxes[1].legend()\naxes[1].grid(alpha=0.3)\nplt.tight_layout()\nplt.show()\nprint(means.round(1))\n"),

  md("---\n## 3. 리텐션 (retention_w2 / retention_w3)\n"),

  code("fig, axes = plt.subplots(1, 2, figsize=(12, 5))\n\nfor ax, col, label in zip(axes, ['retention_w2','retention_w3'], ['2주차 리텐션','3주차 리텐션']):\n    ret_churn = df.groupby(col)['is_churn'].mean()\n    counts    = df[col].value_counts().sort_index()\n    bars = ax.bar(['미시청(0)','시청(1)'], ret_churn.values, color=['lightcoral','steelblue'], edgecolor='black')\n    ax.set_title(f'{label}별 이탈률')\n    ax.set_ylabel('이탈률')\n    ax.set_ylim(0, 0.6)\n    for bar, val, cnt in zip(bars, ret_churn.values, counts.values):\n        ax.annotate(f'{val:.1%}\\n(n={cnt:,})',\n                    (bar.get_x()+bar.get_width()/2, bar.get_height()+0.01), ha='center', fontsize=11)\n\nplt.tight_layout()\nplt.show()\nprint('retention_w2 이탈률:', df.groupby('retention_w2')['is_churn'].mean().round(3))\nprint('retention_w3 이탈률:', df.groupby('retention_w3')['is_churn'].mean().round(3))\n"),

  md("---\n## 4. 장르 비율별 이탈률\n"),

  code("genre_cols = ['ratio_action_violent','ratio_family_drama','ratio_kids',\n              'ratio_romance','ratio_thriller','ratio_documentary',\n              'ratio_comedy','ratio_etc']\n\ngenre_labels = {\n    'ratio_action_violent':'액션/폭력', 'ratio_family_drama':'가족/드라마',\n    'ratio_kids':'키즈', 'ratio_romance':'로맨스', 'ratio_thriller':'스릴러',\n    'ratio_documentary':'다큐', 'ratio_comedy':'코미디', 'ratio_etc':'기타'\n}\n\nresults = []\nfor col in genre_cols:\n    viewers = df[df[col] > 0]\n    results.append({\n        '장르': genre_labels[col],\n        '시청 유저 수': len(viewers),\n        '이탈률': viewers['is_churn'].mean(),\n        '전체 평균 비율': df[col].mean()\n    })\n\nresult_df = pd.DataFrame(results).sort_values('이탈률', ascending=False)\n\nfig, axes = plt.subplots(1, 2, figsize=(15, 5))\nbars = axes[0].barh(result_df['장르'], result_df['이탈률'], color='tomato', edgecolor='black')\naxes[0].axvline(df['is_churn'].mean(), color='navy', linestyle='--',\n                label=f'전체 평균 {df[\"is_churn\"].mean():.1%}')\naxes[0].set_title('장르별 이탈률 (해당 장르 시청 유저)')\naxes[0].set_xlabel('이탈률')\naxes[0].legend()\nfor bar, val in zip(bars, result_df['이탈률']):\n    axes[0].annotate(f'{val:.1%}', (val+0.003, bar.get_y()+bar.get_height()/2), va='center', fontsize=10)\n\nbars2 = axes[1].barh(result_df['장르'], result_df['전체 평균 비율'], color='steelblue', edgecolor='black')\naxes[1].set_title('장르별 평균 시청 비율')\naxes[1].set_xlabel('평균 비율')\nfor bar, val in zip(bars2, result_df['전체 평균 비율']):\n    axes[1].annotate(f'{val:.1%}', (val+0.002, bar.get_y()+bar.get_height()/2), va='center', fontsize=10)\n\nplt.tight_layout()\nplt.show()\nprint(result_df.to_string(index=False))\n"),

  md("---\n## 5. 주력 장르 (최대 비율 장르) 기준 이탈률\n"),

  code("df_watch = df[df[genre_cols].sum(axis=1) > 0].copy()\ndf_watch['main_genre'] = df_watch[genre_cols].idxmax(axis=1).map(genre_labels)\n\nchurn_by_genre = df_watch.groupby('main_genre').agg(\n    유저수=('is_churn','count'),\n    이탈률=('is_churn','mean')\n).sort_values('이탈률', ascending=False).reset_index()\n\nfig, ax = plt.subplots(figsize=(10, 5))\nbars = ax.bar(churn_by_genre['main_genre'], churn_by_genre['이탈률'], color='coral', edgecolor='black')\nax.axhline(df_watch['is_churn'].mean(), color='navy', linestyle='--',\n           label=f'전체 평균 {df_watch[\"is_churn\"].mean():.1%}')\nax.set_title('주력 장르별 이탈률')\nax.set_ylabel('이탈률')\nax.set_ylim(0, 0.6)\nfor bar, row in zip(bars, churn_by_genre.itertuples()):\n    ax.annotate(f'{row.이탈률:.1%}\\n(n={row.유저수:,})',\n                (bar.get_x()+bar.get_width()/2, bar.get_height()+0.01), ha='center', fontsize=10)\nax.legend()\nplt.tight_layout()\nplt.show()\nprint(churn_by_genre.to_string(index=False))\n"),

  md("---\n## 6. 신규 피처 상관관계 (이탈과의 관계)\n"),

  code("new_feat_cols = ['recency_days','dur_w1','dur_w2','dur_w3','dur_w4plus',\n                 'retention_w2','retention_w3'] + genre_cols\n\ncorr = df[new_feat_cols + ['is_churn']].corr()['is_churn'].drop('is_churn').sort_values()\n\nfig, ax = plt.subplots(figsize=(10, 7))\ncolors = ['tomato' if v > 0 else 'steelblue' for v in corr.values]\nbars = ax.barh(corr.index, corr.values, color=colors, edgecolor='black')\nax.axvline(0, color='black', linewidth=0.8)\nax.set_title('신규 피처와 이탈(is_churn)의 상관관계')\nax.set_xlabel('Pearson 상관계수')\nfor bar, val in zip(bars, corr.values):\n    offset = 0.002 if val >= 0 else -0.002\n    ha = 'left' if val >= 0 else 'right'\n    ax.annotate(f'{val:.3f}', (val+offset, bar.get_y()+bar.get_height()/2), va='center', ha=ha, fontsize=9)\nplt.tight_layout()\nplt.show()\n"),

  md("---\n## 7. 종합 요약\n"),

  code("print('=== 신규 피처 이탈률 요약 ===')\nprint()\nprint('[Recency]')\nprint(f'  이탈 평균: {churn[\"recency_days\"].mean():.1f}일 | 잔류 평균: {stay[\"recency_days\"].mean():.1f}일')\nprint()\nprint('[주차별 시청 시간 평균]')\nfor col in ['dur_w1','dur_w2','dur_w3','dur_w4plus']:\n    print(f'  {col}: 이탈={churn[col].mean():.1f}분 | 잔류={stay[col].mean():.1f}분')\nprint()\nprint('[리텐션]')\nfor col in ['retention_w2','retention_w3']:\n    r0 = df[df[col]==0]['is_churn'].mean()\n    r1 = df[df[col]==1]['is_churn'].mean()\n    print(f'  {col}: 미시청={r0:.1%} | 시청={r1:.1%} (차이: {abs(r0-r1):.1%}p)')\nprint()\nprint('[장르별 이탈률 (시청 유저 기준)]')\nfor _, row in result_df.iterrows():\n    print(f'  {row[\"장르\"]}: {row[\"이탈률\"]:.1%} (n={int(row[\"시청 유저 수\"]):,})')\n")
]

nb = {
  "cells": cells,
  "metadata": {
    "kernelspec": {"display_name":"Python 3","language":"python","name":"python3"},
    "language_info": {"name":"python","version":"3.11.0"}
  },
  "nbformat": 4,
  "nbformat_minor": 4
}

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print('완료. 총 셀 수:', len(cells))
for i, c in enumerate(cells):
    print(f'[{i}] ({c["cell_type"]}) {c["source"][:60]}')
