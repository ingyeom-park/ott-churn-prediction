"""
EDA 차트 생성 + HTML 보고서 출력 (통합 스크립트)
실행 위치: 어디서 실행해도 동작 (pathlib 기반 절대경로 사용)
출력: kwon.donggeun/EDA/eda_report.html
"""
import sys, io, base64, json
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

ROOT     = Path(__file__).resolve().parents[3]   # ott-churn-prediction/
DATA_DIR = ROOT / '_data' / '01_raw'
OUT_HTML = Path(__file__).resolve().parents[1] / 'eda_report.html'

font_candidates = [f.name for f in fm.fontManager.ttflist if 'Malgun' in f.name]
FONT = font_candidates[0] if font_candidates else 'DejaVu Sans'
plt.rcParams['font.family'] = FONT
plt.rcParams['axes.unicode_minus'] = False
print('Font:', FONT)

BLUE   = '#2962a2'
ORANGE = '#f59e0b'
GREEN  = '#43a047'
RED    = '#e53935'
GRAY   = '#90a4ae'

# ── 데이터 로드 ────────────────────────────────────────────────
mem_raw = pd.read_csv(DATA_DIR / 'Membership.csv')
um      = pd.read_csv(DATA_DIR / 'User_Mapping.csv')
vh      = pd.read_csv(DATA_DIR / 'View_History.csv')

mem_raw['reg_date']      = pd.to_datetime(mem_raw['reg_date'])
mem_raw['end_date']      = pd.to_datetime(mem_raw['end_date'])
mem_raw['duration_days'] = (mem_raw['end_date'] - mem_raw['reg_date']).dt.days

mem = mem_raw.copy()
print(f'로드 완료: Membership {mem.shape}, User_Mapping {um.shape}, View_History {vh.shape}')

# ── 유틸 ──────────────────────────────────────────────────────
CHARTS = {}

def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

def spines_off(ax):
    ax.spines[['top', 'right']].set_visible(False)

# ════════════════════════════════════════════════════════════════
# 차트 생성
# ════════════════════════════════════════════════════════════════

# 1. 결측치 비율
fig, ax = plt.subplots(figsize=(11, 4))
miss = mem.isnull().sum().sort_values(ascending=False)
miss = miss[miss > 0]
colors_miss = [RED if v/len(mem) > 0.3 else ORANGE if v/len(mem) > 0.05 else GREEN
               for v in miss.values]
bars = ax.bar(miss.index, miss.values / len(mem) * 100, color=colors_miss)
ax.set_title('전처리 전 결측치 비율 (%)', fontsize=13, fontweight='bold', pad=10)
ax.set_ylabel('%')
ax.set_ylim(0, 95)
for bar, val in zip(bars, miss.values):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
            f'{val:,}\n({val/len(mem)*100:.1f}%)', ha='center', va='bottom', fontsize=8)
ax.tick_params(axis='x', rotation=20)
spines_off(ax)
plt.tight_layout()
CHARTS['missing'] = fig_to_b64(fig)
plt.close()
print('1. 결측치 완료')

# 2. amount 분포
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
top_amt = mem['amount'].value_counts().head(12).sort_index()
axes[0].bar(top_amt.index.astype(str), top_amt.values, color=BLUE)
axes[0].set_title('금액별 건수 (상위 12)', fontweight='bold')
axes[0].tick_params(axis='x', rotation=45)
spines_off(axes[0])
axes[1].hist(mem['amount'], bins=40, color=BLUE, edgecolor='white', linewidth=0.5)
axes[1].set_title('amount 히스토그램', fontweight='bold')
axes[1].set_yscale('log')
spines_off(axes[1])
axes[2].boxplot(mem['amount'].dropna(), vert=False, patch_artist=True,
                boxprops=dict(facecolor=BLUE, alpha=0.6),
                medianprops=dict(color='white', linewidth=2))
axes[2].set_title('amount 박스플롯', fontweight='bold')
spines_off(axes[2])
plt.suptitle('amount (결제 금액)  ※ 원화/달러 혼재', fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
CHARTS['amount'] = fig_to_b64(fig)
plt.close()
print('2. amount 완료')

# 3. age 분포
AGE_MAX = 100
fig, ax = plt.subplots(figsize=(10, 5))
verified_clean = mem[(mem['is_user_verified']=='Y') & (mem['age'] <= AGE_MAX)]['age'].dropna()
all_clean      = mem[mem['age'] <= AGE_MAX]['age'].dropna()
n_outlier      = (mem['age'] > AGE_MAX).sum()
age_bins = np.arange(10, 106, 5) - 0.5
ax.hist(all_clean,      bins=age_bins, color=ORANGE, edgecolor='white', linewidth=0.5,
        label=f'전체 (≤{AGE_MAX}세, n={len(all_clean):,})', alpha=0.85)
ax.hist(verified_clean, bins=age_bins, color=BLUE,   edgecolor='white', linewidth=0.5,
        label=f'인증 고객 (n={len(verified_clean):,})', alpha=0.7)
ax.set_xticks(range(10, 105, 5))
ax.set_title(f'age 히스토그램  ※ {AGE_MAX}세 초과 {n_outlier}건 제외', fontweight='bold', fontsize=13)
ax.set_xlabel('연령'); ax.set_ylabel('건수'); ax.legend(fontsize=10)
spines_off(ax)
plt.tight_layout()
CHARTS['age'] = fig_to_b64(fig)
plt.close()
print('3. age 완료')

# 4. concurrent_streams / reg_hour
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sc = mem['concurrent_streams'].value_counts().sort_index()
bar_colors = [RED if idx == 3 else BLUE for idx in sc.index]
axes[0].bar(sc.index.astype(str), sc.values, color=bar_colors)
for i, (idx, val) in enumerate(zip(sc.index, sc.values)):
    label = f'{val:,}\n(!!)' if idx == 3 else f'{val:,}'
    axes[0].text(i, val+50, label, ha='center', fontsize=9,
                 color=RED if idx == 3 else 'black', fontweight='bold' if idx == 3 else 'normal')
axes[0].set_title('concurrent_streams 분포  ※ 3=이상값', fontweight='bold')
spines_off(axes[0])
hour_cnt = mem['reg_hour'].value_counts().sort_index()
colors_h = [RED if h in [0,1,2,3,22,23] else BLUE for h in hour_cnt.index]
axes[1].bar(hour_cnt.index, hour_cnt.values, color=colors_h)
axes[1].set_title('가입 시간대 (reg_hour)', fontweight='bold')
spines_off(axes[1])
plt.tight_layout()
CHARTS['streams_hour'] = fig_to_b64(fig)
plt.close()
print('4. streams/hour 완료')

# 5. duration_days
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(mem['duration_days'], bins=35, color=ORANGE, edgecolor='white')
ax.axvline(0, color=RED, linestyle='--', linewidth=2, label='0일(당일해지)')
ax.set_title('duration_days 히스토그램', fontweight='bold')
ax.set_xlabel('지속 일수'); ax.set_ylabel('건수'); ax.legend()
spines_off(ax)
plt.tight_layout()
CHARTS['duration'] = fig_to_b64(fig)
plt.close()
print('5. duration 완료')

# 6. 범주형 분포
fig, axes = plt.subplots(2, 2, figsize=(16, 10))
cats = {
    'product_cd':     ('상품 코드',   axes[0][0]),
    'payment_device': ('결제 기기',   axes[0][1]),
    'billing_method': ('결제 수단',   axes[1][0]),
    'gender':         ('성별',        axes[1][1]),
}
for col, (title, ax) in cats.items():
    vc = mem[col].value_counts().head(10)
    ax.barh(vc.index.astype(str)[::-1], vc.values[::-1], color=BLUE)
    ax.set_title(title, fontweight='bold')
    spines_off(ax)
    for i, v in enumerate(vc.values[::-1]):
        ax.text(v+10, i, f'{v:,}', va='center', fontsize=9)
plt.suptitle('범주형 변수 분포', fontsize=14, fontweight='bold')
plt.tight_layout()
CHARTS['categorical'] = fig_to_b64(fig)
plt.close()
print('6. 범주형 완료')

# 7. 타겟(repurchase) 분포
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
sizes_p  = [11931, 6252]
labels_p = ['재결제(O)\n11,931 (65.6%)', '이탈(NaN)\n6,252 (34.4%)']
axes[0].pie(sizes_p, labels=labels_p, colors=[GREEN, RED], autopct='%1.1f%%',
            startangle=90, textprops={'fontsize':11},
            wedgeprops={'edgecolor':'white','linewidth':2})
axes[0].set_title('repurchase (타겟) 분포', fontweight='bold')
segs = {
    '전체':          mem,
    '프로모션 참여':  mem[mem['promotion_yn']=='O'],
    '프로모션 미참여':mem[mem['promotion_yn'].isna()],
    '해지방어':       mem[mem['is_churn_prevented']=='O'],
    '인증 고객':      mem[mem['is_user_verified']=='Y'],
}
seg_rates = {k: (v['repurchase']=='O').mean()*100 for k,v in segs.items()}
axes[1].barh(list(seg_rates.keys()), list(seg_rates.values()),
             color=[BLUE, ORANGE, GRAY, RED, GREEN])
axes[1].set_xlim(0, 100); axes[1].set_xlabel('재결제율 (%)')
axes[1].set_title('세그먼트별 재결제율', fontweight='bold')
for i, v in enumerate(seg_rates.values()):
    axes[1].text(v+0.5, i, f'{v:.1f}%', va='center', fontsize=10)
spines_off(axes[1])
plt.tight_layout()
CHARTS['target'] = fig_to_b64(fig)
plt.close()
print('7. 타겟 완료')

# 8. 프로모션 세그먼트
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
promo_y = mem[mem['promotion_yn']=='O']
promo_n = mem[mem['promotion_yn'].isna()]
for ax, col, title in [
    (axes[0], 'payment_device', '결제 기기별'),
    (axes[1], 'product_cd',     '상품별'),
]:
    top_items = mem[col].value_counts().head(6).index
    data_y = promo_y[col].value_counts().reindex(top_items, fill_value=0)
    data_n = promo_n[col].value_counts().reindex(top_items, fill_value=0)
    x = np.arange(len(top_items)); w = 0.35
    ax.bar(x-w/2, data_y.values, w, label='프로모션 참여', color=ORANGE)
    ax.bar(x+w/2, data_n.values, w, label='미참여', color=BLUE)
    ax.set_xticks(x)
    ax.set_xticklabels(top_items, rotation=20, ha='right', fontsize=9)
    ax.set_title(f'프로모션 × {title}', fontweight='bold'); ax.legend(fontsize=9)
    spines_off(ax)
plt.tight_layout()
CHARTS['promo_seg'] = fig_to_b64(fig)
plt.close()
print('8. 프로모션 완료')

# 9. 해지방어 교차
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
mem['churn_label'] = mem['is_churn_prevented'].fillna('미해당')
mem['promo_label'] = mem['promotion_yn'].fillna('미참여')
ct = pd.crosstab(mem['churn_label'], mem['promo_label'])
sns.heatmap(ct, annot=True, fmt='d', cmap='Blues', ax=axes[0], linewidths=0.5)
axes[0].set_title('해지방어 × 프로모션 교차', fontweight='bold')
churn_seg = {
    '해지방어(O)': (mem[mem['is_churn_prevented']=='O']['repurchase']=='O').mean()*100,
    '비해당(NaN)': (mem[mem['is_churn_prevented'].isna()]['repurchase']=='O').mean()*100,
}
axes[1].bar(list(churn_seg.keys()), list(churn_seg.values()), color=[RED, BLUE], width=0.4)
axes[1].set_ylim(0, 100); axes[1].set_ylabel('재결제율 (%)')
axes[1].set_title('해지방어 여부별 재결제율', fontweight='bold')
for i, v in enumerate(churn_seg.values()):
    axes[1].text(i, v+1, f'{v:.1f}%', ha='center', fontsize=12, fontweight='bold')
spines_off(axes[1])
plt.tight_layout()
CHARTS['churn_cross'] = fig_to_b64(fig)
plt.close()
print('9. 해지방어 완료')

# 10. 상품별 재결제율
fig, ax = plt.subplots(figsize=(12, 5))
top10 = mem['product_cd'].value_counts().head(10).index
prod_r = mem[mem['product_cd'].isin(top10)].groupby('product_cd').apply(
    lambda x: (x['repurchase']=='O').mean()*100).sort_values(ascending=False)
colors_p = [RED if v<50 else GREEN if v>70 else ORANGE for v in prod_r.values]
bars = ax.bar(prod_r.index, prod_r.values, color=colors_p)
ax.set_ylim(0, 100)
ax.axhline(65.6, color=GRAY, linestyle='--', linewidth=1.5, label='전체 평균 65.6%')
ax.set_ylabel('재결제율 (%)'); ax.set_title('상품별 재결제율 (상위 10개)', fontweight='bold')
for bar, val in zip(bars, prod_r.values):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5, f'{val:.1f}%', ha='center', fontsize=9)
ax.legend(); spines_off(ax)
plt.tight_layout()
CHARTS['prod_repurchase'] = fig_to_b64(fig)
plt.close()
print('10. 상품별 재결제율 완료')

# 11. 상관관계 히트맵
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
num_cols = ['amount', 'concurrent_streams', 'age', 'reg_hour', 'duration_days']
corr_all = mem[num_cols].corr()
corr_ver = mem[mem['is_user_verified']=='Y'][num_cols].corr()
for ax, corr, title in [
    (axes[0], corr_all, '전체 고객'),
    (axes[1], corr_ver, '인증 고객'),
]:
    mask = np.tril(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                ax=ax, mask=~mask, square=True, linewidths=0.5, vmin=-1, vmax=1)
    ax.set_title(f'상관관계 ({title})', fontweight='bold')
plt.suptitle('수치형 변수 상관관계', fontsize=12)
plt.tight_layout()
CHARTS['corr'] = fig_to_b64(fig)
plt.close()
print('11. 상관관계 완료')

# 12. 일별/요일별 가입 패턴
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
daily = mem.groupby('reg_date').size()
axes[0].plot(daily.index, daily.values, color=BLUE, linewidth=1.5, marker='o', markersize=3)
axes[0].fill_between(daily.index, daily.values, alpha=0.15, color=BLUE)
axes[0].set_title('일별 가입 추이', fontweight='bold')
axes[0].tick_params(axis='x', rotation=20); spines_off(axes[0])
mem['reg_weekday'] = mem['reg_date'].dt.dayofweek
day_labels = ['월','화','수','목','금','토','일']
weekday_cnt = mem['reg_weekday'].value_counts().sort_index()
colors_w = [RED if i>=5 else BLUE for i in weekday_cnt.index]
axes[1].bar(day_labels, weekday_cnt.values, color=colors_w)
axes[1].axhline(weekday_cnt.mean(), color=GRAY, linestyle='--', linewidth=1.5,
                label=f'평균 {weekday_cnt.mean():.0f}건')
axes[1].set_title('요일별 가입 건수', fontweight='bold'); axes[1].legend(fontsize=9)
spines_off(axes[1])
plt.tight_layout()
CHARTS['timeseries'] = fig_to_b64(fig)
plt.close()
print('12. 시계열 완료')

# 13. 요일×시간대 히트맵
fig, ax = plt.subplots(figsize=(14, 5))
hmap = mem.groupby(['reg_weekday', 'reg_hour']).size().unstack(fill_value=0)
hmap.index = ['월','화','수','목','금','토','일']
sns.heatmap(hmap, cmap='Blues', ax=ax, linewidths=0.3, cbar_kws={'label':'건수', 'shrink':0.8})
ax.set_title('가입 시간대 × 요일 히트맵', fontweight='bold', fontsize=13)
ax.set_xlabel('가입 시간 (0~23시)'); ax.set_ylabel('요일')
plt.tight_layout()
CHARTS['hour_weekday_heatmap'] = fig_to_b64(fig)
plt.close()
print('13. 시간×요일 히트맵 완료')

# 14. 성별×연령대 히트맵
vf_base = mem[(mem['is_user_verified']=='Y') &
              mem['gender'].isin(['F','M']) &
              (mem['age'] <= 100)].copy()
vf_base['age_bin'] = (vf_base['age'] // 5 * 5).astype(int)
seg_ga = [('전체 (인증)', vf_base),
          ('재결제(O)',   vf_base[vf_base['repurchase']=='O']),
          ('이탈(NaN)',   vf_base[vf_base['repurchase'].isna()])]
fig, axes = plt.subplots(1, 3, figsize=(20, 4))
for ax, (label, df) in zip(axes, seg_ga):
    ga = df.groupby(['gender','age_bin']).size().unstack(fill_value=0)
    sns.heatmap(ga, annot=True, fmt='d', cmap='Blues', ax=ax,
                linewidths=0.5, cbar_kws={'shrink':0.7})
    ax.set_title(f'{label}\n(n={len(df):,})', fontweight='bold', fontsize=11)
plt.suptitle('성별 × 연령대 교차표 (인증 고객)', fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
CHARTS['gender_age_heatmap'] = fig_to_b64(fig)
plt.close()
print('14. 성별×연령대 히트맵 완료')

print(f'\n차트 {len(CHARTS)}개 생성 완료')

# ════════════════════════════════════════════════════════════════
# HTML 생성
# ════════════════════════════════════════════════════════════════

def img(key, caption='', width='100%'):
    return f'''
<figure style="margin:16px 0;">
  <img src="data:image/png;base64,{CHARTS[key]}" style="width:{width};border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.10);" alt="{caption}">
  {f'<figcaption style="text-align:center;font-size:12px;color:#888;margin-top:6px;">{caption}</figcaption>' if caption else ''}
</figure>'''

STYLE = '''
<style>
  body { font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; background:#f4f6fb; color:#222; margin:0; padding:30px 0; }
  .container { max-width:1100px; margin:0 auto; background:#fff; border-radius:12px; box-shadow:0 4px 24px rgba(0,0,0,0.10); padding:40px 50px 60px; }
  h1 { font-size:26px; color:#1a3a6b; border-bottom:3px solid #2962a2; padding-bottom:10px; margin-bottom:6px; }
  .subtitle { color:#888; font-size:13px; margin-bottom:30px; }
  h2 { font-size:17px; color:#fff; background:#2962a2; padding:8px 16px; border-radius:6px; margin-top:40px; margin-bottom:12px; }
  h3 { font-size:14px; color:#1a3a6b; background:#dce8f7; padding:5px 12px; border-radius:4px; margin-top:22px; margin-bottom:10px; }
  ul { margin:6px 0 6px 20px; padding:0; } li { font-size:13px; margin-bottom:4px; line-height:1.7; }
  .warn { background:#fff8e1; border-left:4px solid #f59e0b; padding:8px 14px; border-radius:4px; font-size:13px; margin:10px 0; }
  .info { background:#e8f4fd; border-left:4px solid #2962a2; padding:8px 14px; border-radius:4px; font-size:13px; margin:10px 0; }
  .insight { background:#fffde7; border:1px solid #ffe082; border-radius:6px; padding:10px 14px; font-size:13px; margin:10px 0; }
  .insight strong { color:#e65100; }
  table { width:100%; border-collapse:collapse; font-size:12.5px; margin:10px 0 14px; }
  thead tr { background:#2962a2; color:#fff; }
  thead th { padding:7px 10px; text-align:left; font-weight:bold; }
  tbody tr:nth-child(even) { background:#f0f5ff; } tbody tr:nth-child(odd) { background:#fff; }
  tbody td { padding:6px 10px; border-bottom:1px solid #e0e8f5; vertical-align:top; }
  .tag { display:inline-block; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:bold; }
  .tag-red { background:#fde8e8; color:#c0392b; } .tag-orange { background:#fff3e0; color:#e65100; }
  .tag-green { background:#e8f5e9; color:#2e7d32; } .tag-blue { background:#e3f2fd; color:#1565c0; }
  .kpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:16px 0; }
  .kpi { background:#f0f5ff; border-radius:8px; padding:14px 16px; text-align:center; border:1px solid #c5d8f5; }
  .kpi .val { font-size:22px; font-weight:bold; color:#1a3a6b; } .kpi .lbl { font-size:11px; color:#666; margin-top:4px; }
  hr { border:none; border-top:1px solid #e0e8f5; margin:32px 0; }
  .footer { margin-top:40px; font-size:12px; color:#aaa; text-align:right; }
</style>'''

html = f'''<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><title>Membership EDA 보고서</title>{STYLE}</head>
<body><div class="container">
  <h1>Membership EDA 보고서</h1>
  <div class="subtitle">OTT 고객 이탈 예측 프로젝트 · 탐색적 데이터 분석 결과</div>

  <div class="kpi-grid">
    <div class="kpi"><div class="val">18,183</div><div class="lbl">전체 레코드</div></div>
    <div class="kpi"><div class="val">17,845</div><div class="lbl">고유 user_no</div></div>
    <div class="kpi"><div class="val" style="color:#e53935;">34.4%</div><div class="lbl">이탈률</div></div>
    <div class="kpi"><div class="val">16</div><div class="lbl">컬럼 수</div></div>
  </div>

  <h2>1. 데이터 품질 — 결측치</h2>
  <div class="info">promotion_yn / repurchase / is_churn_prevented 의 NaN은 <strong>"미해당(N)"</strong> 의미.</div>
  {img('missing', '컬럼별 결측치 비율')}
  <table>
    <thead><tr><th>컬럼</th><th>결측률</th><th>해석</th><th>전처리 방향</th></tr></thead>
    <tbody>
      <tr><td>is_churn_prevented</td><td><span class="tag tag-red">82.1%</span></td><td>NaN = 미해당</td><td>NaN→0, O→1</td></tr>
      <tr><td>promotion_yn</td><td><span class="tag tag-red">49.4%</span></td><td>NaN = 미참여</td><td>NaN→0, O→1</td></tr>
      <tr><td>repurchase</td><td><span class="tag tag-orange">34.4%</span></td><td>NaN = 이탈 <strong>(타겟)</strong></td><td>NaN→0, O→1</td></tr>
      <tr><td>is_user_verified</td><td><span class="tag tag-blue">3.3%</span></td><td>Y/N 이진값</td><td>최빈값 대체</td></tr>
      <tr><td>gender / age</td><td><span class="tag tag-green">0.9%</span></td><td>미인증 고객</td><td>Unknown 처리</td></tr>
    </tbody>
  </table>
  <hr>

  <h2>2. 타겟 변수 — repurchase</h2>
  {img('target', '왼쪽: 타겟 분포 | 오른쪽: 세그먼트별 재결제율')}
  <div class="insight"><strong>핵심:</strong> 해지방어 고객의 재결제율이 전체 평균보다 낮음 → 해지 신청 경험 자체가 이탈 위험 신호.</div>
  <hr>

  <h2>3. 수치형 변수 분포</h2>
  <h3>amount (결제 금액)</h3>
  <div class="warn">원화(₩)와 달러($) 혼재 — iOS 달러 케이스 약 <strong>3,062건 (16.8%)</strong>. 통화 통일 필수.</div>
  {img('amount', 'amount 분포')}
  <h3>age / concurrent_streams / reg_hour</h3>
  <div class="warn">age max=<strong>950</strong> (미인증 입력 오류). concurrent_streams=3은 7건뿐 → 입력 오류.</div>
  {img('age', 'age 히스토그램 (100세 초과 제외)')}
  {img('streams_hour', '좌: 동시 시청 수 | 우: 가입 시간대')}
  <h3>duration_days</h3>
  {img('duration', 'duration_days 히스토그램')}
  <hr>

  <h2>4. 범주형 변수 분포</h2>
  {img('categorical', '상품코드 / 결제기기 / 결제수단 / 성별')}
  <hr>

  <h2>5. 시계열 패턴</h2>
  {img('timeseries', '좌: 일별 가입 추이 | 우: 요일별 가입 건수')}
  {img('hour_weekday_heatmap', '가입 시간대 × 요일 히트맵')}
  <hr>

  <h2>6. 세그먼트 분석 — 프로모션</h2>
  {img('promo_seg', '프로모션 × 결제기기 / 상품별')}
  <hr>

  <h2>7. 해지방어 × 프로모션 / 상품별 재결제율</h2>
  {img('churn_cross', '좌: 해지방어×프로모션 교차 | 우: 해지방어 여부별 재결제율')}
  <div class="insight"><strong>발견:</strong> 해지방어(is_churn_prevented=O) 고객의 재결제율이 비해당 고객보다 낮음.</div>
  {img('prod_repurchase', '상품별 재결제율 (상위 10개)')}
  <hr>

  <h2>8. 상관관계 분석</h2>
  {img('corr', '좌: 전체 고객 | 우: 인증 고객')}
  <hr>

  <h2>9. 성별 × 연령대 분포</h2>
  {img('gender_age_heatmap', '성별 × 연령대 교차표 (인증 고객)')}

  <div class="footer">OTT 고객 이탈 예측 프로젝트 · EDA 보고서</div>
</div></body></html>'''

OUT_HTML.write_text(html, encoding='utf-8')
print(f'\nHTML 저장: {OUT_HTML}')
