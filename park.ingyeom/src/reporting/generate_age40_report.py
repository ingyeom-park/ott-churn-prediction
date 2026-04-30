"""
age=40 이상 현상 원인 분석 - HTML 리포트 생성 스크립트
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import seaborn as sns
import base64
import io
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "_data" / "01_raw"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── 폰트 / 스타일 설정 ────────────────────────────────────────────────────────
plt.rcParams['font.family']       = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi']        = 130
plt.rcParams['axes.spines.top']   = False
plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.grid']         = True
plt.rcParams['grid.alpha']        = 0.3
plt.rcParams['grid.linestyle']    = '--'

PALETTE = {
    'primary'  : '#2B4590',
    'secondary': '#5B8DB8',
    'accent'   : '#C0392B',
    'warn'     : '#E67E22',
    'ok'       : '#27AE60',
    'neutral'  : '#7F8C8D',
    'light'    : '#ECF0F1',
}

# ── 데이터 로드 ──────────────────────────────────────────────────────────────
df = pd.read_excel(RAW_DATA_DIR / 'Membership.xlsx')
df['verified_label'] = df['is_user_verified'].fillna('NaN')
df['is_ios']         = df['billing_method'] == 140

verified   = df[df['is_user_verified'] == 'Y']
unverified = df[df['is_user_verified'] == 'N']

ios_unv  = unverified[unverified['billing_method'] == 140]
nios_unv = unverified[unverified['billing_method'] != 140]

caseA = unverified[(unverified['age'] == 40) & (unverified['gender'] == 'N')]
caseB = unverified[(unverified['age'] == 40) & (unverified['gender'] != 'N')]
caseC = unverified[(unverified['age'] != 40) & (unverified['gender'] == 'N')]
caseD = unverified[(unverified['age'] != 40) & (unverified['gender'] != 'N')]

real_age40    = (verified['age'] == 40).sum()
ios_default   = ((unverified['billing_method'] == 140) & (unverified['age'] == 40)).sum()
other_default = ((unverified['billing_method'] != 140) & (unverified['age'] == 40)).sum()
fake_total    = ios_default + other_default


# ── 그림 -> base64 변환 헬퍼 ─────────────────────────────────────────────────
def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', facecolor='white')
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f'data:image/png;base64,{b64}'


# ══════════════════════════════════════════════════════════════════════════════
# 차트 1 : 문제 확인 — 인증/미인증 age 히스토그램
# ══════════════════════════════════════════════════════════════════════════════
def chart_problem():
    age_bins = list(range(0, 101, 5))

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))

    ax = axes[0]
    ax.hist(verified['age'].dropna(),   bins=age_bins, alpha=0.75,
            color=PALETTE['secondary'], label=f'인증 (n={len(verified):,})', edgecolor='white')
    ax.hist(unverified['age'].dropna(), bins=age_bins, alpha=0.75,
            color=PALETTE['warn'],      label=f'미인증 (n={len(unverified):,})', edgecolor='white')
    ax.axvline(40, color=PALETTE['accent'], linestyle='--', linewidth=1.5, label='age = 40')
    ax.set_xlabel('연령')
    ax.set_ylabel('건수')
    ax.set_title('인증 vs 미인증 age 분포 비교')
    ax.legend(fontsize=9)

    ax2 = axes[1]
    groups = ['인증(Y)\nn=13,487', '미인증(N)\nn=4,096']
    pcts   = [
        (verified['age']   == 40).sum() / len(verified)   * 100,
        (unverified['age'] == 40).sum() / len(unverified) * 100,
    ]
    bars = ax2.bar(groups, pcts,
                   color=[PALETTE['secondary'], PALETTE['accent']],
                   edgecolor='white', width=0.45)
    for bar, pct in zip(bars, pcts):
        ax2.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 1.5,
                 f'{pct:.1f}%', ha='center', fontsize=13, fontweight='bold')
    ax2.axhline(10.4, color=PALETTE['secondary'], linestyle=':', linewidth=1.5,
                label='인증 기준선 (10.4%)')
    ax2.set_ylabel('age = 40 비율 (%)')
    ax2.set_title('그룹별 age = 40 비율')
    ax2.set_ylim(0, 100)
    ax2.legend(fontsize=9)

    fig.suptitle('문제 확인: 미인증 유저의 88.4%가 age = 40',
                 fontsize=13, fontweight='bold', y=1.02)
    fig.tight_layout()
    return fig_to_b64(fig)


# ══════════════════════════════════════════════════════════════════════════════
# 차트 2 : gender = N 분포
# ══════════════════════════════════════════════════════════════════════════════
def chart_gender():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    g_palette = {'F': '#D98880', 'M': '#7FB3D3', 'N': '#BDC3C7'}

    for ax, (grp, label) in zip(axes, [(verified, '인증(Y)'), (unverified, '미인증(N)')]):
        counts = grp['gender'].value_counts(dropna=False).reindex(['F', 'M', 'N'], fill_value=0)
        bars = ax.bar(counts.index, counts.values,
                      color=[g_palette[g] for g in counts.index],
                      edgecolor='white', width=0.5)
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + counts.max() * 0.02,
                    f'{int(bar.get_height()):,}', ha='center', fontsize=11)
        ax.set_title(f'gender 분포 — {label}')
        ax.set_ylabel('건수')
        ax.set_ylim(0, counts.max() * 1.18)
        handles = [mpatches.Patch(color=g_palette[g], label=lbl)
                   for g, lbl in [('F', '여성(F)'), ('M', '남성(M)'), ('N', '미입력(N)')]]
        ax.legend(handles=handles, fontsize=9)

    pct_N = (unverified['gender'] == 'N').sum() / len(unverified) * 100
    fig.suptitle(f'미인증 유저의 {pct_N:.1f}%가 gender = N (미입력)',
                 fontsize=13, fontweight='bold', y=1.02)
    fig.tight_layout()
    return fig_to_b64(fig)


# ══════════════════════════════════════════════════════════════════════════════
# 차트 3 : 원인1 — iOS 앱스토어 결제
# ══════════════════════════════════════════════════════════════════════════════
def chart_ios():
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))

    # 그래프 A: billing_method별 payment_device
    ax = axes[0]
    bm_device = pd.crosstab(df['billing_method'], df['payment_device'])
    for col in ['ios', 'android', 'pc', 'mobile']:
        if col not in bm_device.columns:
            bm_device[col] = 0
    top4 = bm_device[['ios', 'android', 'pc', 'mobile']]
    top4.plot(kind='bar', ax=ax,
              color=[PALETTE['accent'], PALETTE['ok'], PALETTE['secondary'], PALETTE['warn']],
              edgecolor='white', width=0.7)
    ax.set_title('billing_method별 결제기기 분포')
    ax.set_xlabel('billing_method')
    ax.set_ylabel('건수')
    ax.tick_params(axis='x', rotation=0)
    ax.legend(title='결제기기', fontsize=8, title_fontsize=8)

    # 그래프 B: billing_method별 미인증 비율
    ax2 = axes[1]
    bm_unv_pct = (
        df.groupby('billing_method')['is_user_verified']
          .apply(lambda x: (x == 'N').sum() / x.notna().sum() * 100)
          .reset_index()
    )
    bm_unv_pct.columns = ['bm', 'pct']
    colors = [PALETTE['accent'] if bm == 140 else PALETTE['secondary']
              for bm in bm_unv_pct['bm']]
    bars2 = ax2.bar(bm_unv_pct['bm'].astype(str), bm_unv_pct['pct'],
                    color=colors, edgecolor='white', width=0.6)
    for bar in bars2:
        ax2.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.8,
                 f'{bar.get_height():.1f}%', ha='center', fontsize=8.5)
    ax2.set_title('billing_method별 미인증 비율')
    ax2.set_xlabel('billing_method')
    ax2.set_ylabel('미인증 비율 (%)')
    ax2.set_ylim(0, 80)
    ax2.legend(handles=[
        mpatches.Patch(color=PALETTE['accent'],    label='BM=140 (iOS App Store)'),
        mpatches.Patch(color=PALETTE['secondary'], label='그 외'),
    ], fontsize=8)

    # 그래프 C: iOS vs 비iOS 미인증에서 age=40 비율
    ax3 = axes[2]
    labels = ['iOS 미인증\n(BM=140)\nn=2,175', '비-iOS 미인증\nn=1,921']
    pcts   = [
        (ios_unv['age']  == 40).sum() / len(ios_unv)  * 100,
        (nios_unv['age'] == 40).sum() / len(nios_unv) * 100,
    ]
    bars3 = ax3.bar(labels, pcts,
                    color=[PALETTE['accent'], PALETTE['warn']],
                    edgecolor='white', width=0.45)
    for bar, pct in zip(bars3, pcts):
        ax3.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 1.2,
                 f'{pct:.1f}%', ha='center', fontsize=13, fontweight='bold')
    ax3.set_title('미인증 그룹별 age = 40 비율')
    ax3.set_ylabel('age = 40 비율 (%)')
    ax3.set_ylim(0, 105)

    fig.suptitle('원인 1: iOS 앱스토어(BM=140)는 구독자 개인정보를 앱에 전달하지 않음',
                 fontsize=12, fontweight='bold', y=1.02)
    fig.tight_layout()
    return fig_to_b64(fig)


# ══════════════════════════════════════════════════════════════════════════════
# 차트 4 : 케이스 분류
# ══════════════════════════════════════════════════════════════════════════════
def chart_cases():
    sizes  = [len(caseA), len(caseB), len(caseC), len(caseD)]
    labels = [
        f'A. 완전 기본값\n(age=40, gender=N)\n{len(caseA):,}건',
        f'B. age만 기본값\n(age=40, gender=F/M)\n{len(caseB):,}건',
        f'C. gender만 기본값\n(age≠40, gender=N)\n{len(caseC):,}건',
        f'D. 실제 정보 있음\n(age≠40, gender=F/M)\n{len(caseD):,}건',
    ]
    colors = ['#C0392B', '#E67E22', '#F1C40F', '#27AE60']

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # 파이차트
    ax = axes[0]
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%',
        colors=colors, startangle=130,
        pctdistance=0.72, explode=(0.04, 0.04, 0.04, 0.08),
        textprops={'fontsize': 8.5},
        wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}
    )
    for at in autotexts:
        at.set_fontweight('bold')
        at.set_fontsize(9)
    ax.set_title('미인증 4,096명 케이스 분류', fontsize=11, fontweight='bold')

    # 막대차트
    ax2 = axes[1]
    case_labels = ['A\n완전 기본값', 'B\nage만 기본값', 'C\ngender만 기본값', 'D\n실제 정보']
    bars = ax2.bar(case_labels, sizes, color=colors, edgecolor='white', width=0.55)
    for bar, val in zip(bars, sizes):
        ax2.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 30,
                 f'{val:,}', ha='center', fontsize=11, fontweight='bold')
    ax2.set_ylabel('건수')
    ax2.set_title('케이스별 건수', fontsize=11, fontweight='bold')
    ax2.set_ylim(0, max(sizes) * 1.18)
    ax2.text(3, len(caseD) * 1.35, '모델링\n활용 가능',
             ha='center', color=PALETTE['ok'], fontsize=9, fontweight='bold')

    unreliable_pct = (len(caseA) + len(caseB) + len(caseC)) / len(unverified) * 100
    fig.suptitle(f'미인증 유저의 {unreliable_pct:.1f}%는 age/gender를 신뢰할 수 없음',
                 fontsize=13, fontweight='bold', y=1.02)
    fig.tight_layout()
    return fig_to_b64(fig)


# ══════════════════════════════════════════════════════════════════════════════
# 차트 5 : 기본값 제거 전/후 비교
# ══════════════════════════════════════════════════════════════════════════════
def chart_before_after():
    df_clean = df.copy()
    df_clean.loc[df_clean['is_user_verified'] == 'N', 'age'] = np.nan
    clean_counts = df_clean['age'].dropna().value_counts().sort_index()
    raw_counts   = df['age'].dropna().value_counts().sort_index()

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))

    for ax, counts, title, highlight in [
        (axes[0], raw_counts,   '처리 전 — 전체 age 분포', True),
        (axes[1], clean_counts, '처리 후 — 인증 유저 age 분포 (신뢰 가능)', False),
    ]:
        valid_idx = [a for a in counts.index if a <= 100]
        c = counts[valid_idx]
        bar_colors = [PALETTE['accent'] if (a == 40 and highlight) else PALETTE['secondary']
                      for a in c.index]
        ax.bar([str(int(a)) for a in c.index], c.values,
               color=bar_colors, edgecolor='white', width=0.75)
        ax.set_xlabel('age')
        ax.set_ylabel('건수')
        ax.set_title(title, fontsize=10, fontweight='bold')
        ax.tick_params(axis='x', rotation=45, labelsize=8)
        if highlight:
            cnt_40 = (df['age'] == 40).sum()
            ax.legend(handles=[
                mpatches.Patch(color=PALETTE['accent'],    label=f'age=40: {cnt_40:,}건 (28.1%)'),
                mpatches.Patch(color=PALETTE['secondary'], label='그 외'),
            ], fontsize=9)

    fig.suptitle('기본값 제거 전/후 age 분포 비교', fontsize=13, fontweight='bold', y=1.02)
    fig.tight_layout()
    return fig_to_b64(fig)


# ══════════════════════════════════════════════════════════════════════════════
# 차트 6 : 최종 요약 — age=40 구성 분해
# ══════════════════════════════════════════════════════════════════════════════
def chart_summary():
    fig, ax = plt.subplots(figsize=(7, 5.5))

    total_40 = real_age40 + ios_default + other_default

    b1 = ax.bar(['age = 40\n총 5,104건'], real_age40,
                color=PALETTE['ok'],
                label=f'실제 36-40세 (인증): {real_age40:,}건',
                edgecolor='white')
    b2 = ax.bar(['age = 40\n총 5,104건'], ios_default,
                bottom=real_age40,
                color=PALETTE['accent'],
                label=f'iOS 앱스토어 기본값: {ios_default:,}건',
                edgecolor='white')
    b3 = ax.bar(['age = 40\n총 5,104건'], other_default,
                bottom=real_age40 + ios_default,
                color=PALETTE['warn'],
                label=f'비-iOS 미인증 기본값: {other_default:,}건',
                edgecolor='white')

    def center_label(bar_obj, bottom, value, total):
        x = bar_obj[0].get_x() + bar_obj[0].get_width() / 2
        y = bottom + value / 2
        ax.text(x, y, f'{value:,}건\n({value/total*100:.1f}%)',
                ha='center', va='center', fontsize=11,
                fontweight='bold', color='white')

    center_label(b1, 0,                        real_age40,    total_40)
    center_label(b2, real_age40,               ios_default,   total_40)
    center_label(b3, real_age40 + ios_default, other_default, total_40)

    ax.set_ylabel('건수')
    ax.set_title('age = 40 총 5,104건의 실제 구성', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9, loc='upper right')
    ax.set_ylim(0, 5800)

    ax.annotate(
        f'기본값 합계: {fake_total:,}건\n전체의 {fake_total/total_40*100:.1f}%',
        xy=(0.22, real_age40 + fake_total / 2),
        xytext=(0.45, 3000),
        fontsize=10, color=PALETTE['accent'], fontweight='bold',
        arrowprops=dict(arrowstyle='->', color=PALETTE['accent']),
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#FDEDEC', edgecolor=PALETTE['accent'])
    )

    fig.tight_layout()
    return fig_to_b64(fig)


# ══════════════════════════════════════════════════════════════════════════════
# HTML 생성
# ══════════════════════════════════════════════════════════════════════════════
print("차트 생성 중...")
img1 = chart_problem()
img2 = chart_gender()
img3 = chart_ios()
img4 = chart_cases()
img5 = chart_before_after()
img6 = chart_summary()
print("모든 차트 생성 완료. HTML 작성 중...")

HTML = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>age = 40 이상 현상 원인 분석</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
    background: #F8F9FA;
    color: #212529;
    font-size: 15px;
    line-height: 1.7;
  }}

  .page-wrap {{
    max-width: 960px;
    margin: 0 auto;
    padding: 48px 32px 80px;
  }}

  /* ── 헤더 ── */
  .report-header {{
    border-bottom: 3px solid #2B4590;
    padding-bottom: 20px;
    margin-bottom: 40px;
  }}
  .report-header h1 {{
    font-size: 24px;
    font-weight: 700;
    color: #2B4590;
    letter-spacing: -0.3px;
  }}
  .report-header p {{
    margin-top: 6px;
    color: #555;
    font-size: 14px;
  }}

  /* ── 섹션 ── */
  .section {{
    margin-bottom: 52px;
  }}
  .section-title {{
    font-size: 17px;
    font-weight: 700;
    color: #2B4590;
    border-left: 4px solid #2B4590;
    padding-left: 10px;
    margin-bottom: 14px;
  }}
  .section-num {{
    font-size: 12px;
    font-weight: 400;
    color: #888;
    margin-right: 6px;
    letter-spacing: 0.5px;
  }}

  /* ── 차트 ── */
  .chart-wrap {{
    background: #fff;
    border: 1px solid #DEE2E6;
    border-radius: 6px;
    padding: 20px;
    margin-bottom: 14px;
  }}
  .chart-wrap img {{
    width: 100%;
    height: auto;
    display: block;
  }}

  /* ── 설명 박스 ── */
  .desc-box {{
    background: #fff;
    border: 1px solid #DEE2E6;
    border-left: 4px solid #5B8DB8;
    border-radius: 4px;
    padding: 14px 18px;
    font-size: 14px;
    color: #333;
    margin-bottom: 8px;
  }}
  .desc-box strong {{
    color: #2B4590;
  }}
  .desc-box .highlight {{
    color: #C0392B;
    font-weight: 700;
  }}

  /* ── 인용 (명세서) ── */
  .quote-box {{
    background: #FAFAFA;
    border: 1px solid #CED4DA;
    border-left: 4px solid #E67E22;
    border-radius: 4px;
    padding: 14px 18px;
    font-size: 14px;
    color: #444;
    margin-bottom: 14px;
    font-style: italic;
  }}

  /* ── 수치 카드 ── */
  .stat-row {{
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
    flex-wrap: wrap;
  }}
  .stat-card {{
    flex: 1;
    min-width: 160px;
    background: #fff;
    border: 1px solid #DEE2E6;
    border-radius: 6px;
    padding: 16px 18px;
    text-align: center;
  }}
  .stat-card .val {{
    font-size: 28px;
    font-weight: 700;
    color: #2B4590;
    line-height: 1.2;
  }}
  .stat-card .val.red  {{ color: #C0392B; }}
  .stat-card .val.green {{ color: #27AE60; }}
  .stat-card .lbl {{
    font-size: 12px;
    color: #666;
    margin-top: 4px;
  }}

  /* ── 결론 테이블 ── */
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    background: #fff;
  }}
  th {{
    background: #2B4590;
    color: #fff;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
  }}
  td {{
    padding: 10px 14px;
    border-bottom: 1px solid #DEE2E6;
    vertical-align: top;
  }}
  tr:last-child td {{ border-bottom: none; }}
  tr:nth-child(even) td {{ background: #F8F9FA; }}

  /* ── 결론 박스 ── */
  .conclusion-box {{
    background: #EBF5FB;
    border: 1px solid #AED6F1;
    border-radius: 6px;
    padding: 20px 24px;
    font-size: 14px;
    line-height: 1.9;
  }}
  .conclusion-box h3 {{
    font-size: 15px;
    color: #2B4590;
    margin-bottom: 10px;
    font-weight: 700;
  }}
  .conclusion-box ol {{
    padding-left: 20px;
  }}
  .conclusion-box li {{
    margin-bottom: 6px;
  }}

  /* ── 구분선 ── */
  hr {{
    border: none;
    border-top: 1px solid #DEE2E6;
    margin: 40px 0;
  }}
</style>
</head>
<body>
<div class="page-wrap">

  <!-- 헤더 -->
  <div class="report-header">
    <h1>age = 40 이상 현상 원인 분석</h1>
    <p>Membership 데이터셋 &nbsp;|&nbsp; is_user_verified / age / gender / billing_method 교차 분석</p>
  </div>

  <!-- 요약 수치 -->
  <div class="stat-row">
    <div class="stat-card">
      <div class="val">18,183</div>
      <div class="lbl">전체 레코드</div>
    </div>
    <div class="stat-card">
      <div class="val">5,104</div>
      <div class="lbl">전체 age = 40 건수</div>
    </div>
    <div class="stat-card">
      <div class="val red">88.4%</div>
      <div class="lbl">미인증 중 age = 40 비율</div>
    </div>
    <div class="stat-card">
      <div class="val">10.4%</div>
      <div class="lbl">인증 유저 중 age = 40 비율<br><span style="font-size:11px;color:#999">(정상 기준)</span></div>
    </div>
    <div class="stat-card">
      <div class="val red">{fake_total/5104*100:.0f}%</div>
      <div class="lbl">age = 40 중 기본값(가짜) 비율</div>
    </div>
  </div>

  <hr>

  <!-- 섹션 1 -->
  <div class="section">
    <div class="section-title"><span class="section-num">01</span>문제 확인</div>
    <div class="chart-wrap">
      <img src="{img1}" alt="인증/미인증 age 분포 비교">
    </div>
    <div class="desc-box">
      인증 유저 기준 age = 40(36-40세)의 자연스러운 비율은 <strong>10.4%</strong>입니다.
      반면 미인증 유저에서는 <span class="highlight">88.4%</span>가 age = 40으로 기록되어 있습니다.
      단순 연령 분포의 차이로 설명할 수 없는 수준으로, 시스템 기본값이 적용된 것으로 판단됩니다.
    </div>
  </div>

  <!-- 섹션 2 -->
  <div class="section">
    <div class="section-title"><span class="section-num">02</span>데이터 명세서 확인</div>
    <div class="quote-box">
      Membership_Description.xlsx &nbsp;&mdash;&nbsp;
      <strong>is_user_verified</strong> : 본인인증여부
      &nbsp;<strong style="color:#C0392B">(미인증시 성별/연령 부정확)</strong>
    </div>
    <div class="desc-box">
      데이터 설계 단계에서 이미 <strong>미인증 유저의 age와 gender는 신뢰할 수 없다</strong>고 명시되어 있습니다.
      즉, 이 현상은 데이터 품질 문제가 아닌, <strong>시스템 설계상 의도된 동작</strong>입니다.
      본인인증 절차를 거치지 않은 경우 서비스가 성별과 연령을 알 수 없어 기본값을 부여합니다.
    </div>
  </div>

  <!-- 섹션 3 -->
  <div class="section">
    <div class="section-title"><span class="section-num">03</span>gender = N 기본값도 동반 발생</div>
    <div class="chart-wrap">
      <img src="{img2}" alt="gender 분포">
    </div>
    <div class="desc-box">
      인증 유저의 gender = N 비율은 <strong>0.3%</strong>에 불과하지만,
      미인증 유저에서는 <span class="highlight">67.3%</span>가 gender = N으로 기록됩니다.
      age = 40과 마찬가지로 <strong>미인증 시 성별 기본값으로 N이 부여</strong>되는 구조입니다.
    </div>
  </div>

  <!-- 섹션 4 -->
  <div class="section">
    <div class="section-title"><span class="section-num">04</span>원인 1 &mdash; iOS 앱스토어 결제 (billing_method = 140)</div>
    <div class="chart-wrap">
      <img src="{img3}" alt="iOS 결제 분석">
    </div>
    <div class="desc-box">
      <strong>billing_method = 140은 Apple App Store 인앱결제 전용</strong>입니다 (payment_device가 100% ios).
      애플 정책에 따라 앱스토어 구독 시 서비스 제공자에게 사용자의 성별·생년월일이 전달되지 않습니다.
      따라서 해당 경로로 가입한 유저는 자동으로 <span class="highlight">is_user_verified = N, age = 40, gender = N</span>으로 기록됩니다.
      iOS 미인증 유저 2,175명 중 <strong>98.1%</strong>가 age = 40입니다.
    </div>
  </div>

  <!-- 섹션 5 -->
  <div class="section">
    <div class="section-title"><span class="section-num">05</span>원인 2 &mdash; 비-iOS 결제 후 본인인증 미실시</div>
    <div class="desc-box">
      Android, PC 등 비-iOS 결제 수단으로 가입했으나 본인인증 절차를 완료하지 않은 경우에도
      동일하게 <strong>age = 40 기본값</strong>이 적용됩니다.
      비-iOS 미인증 유저 1,921명 중 <strong>77.4%</strong>가 age = 40입니다.
      iOS보다 비율이 낮은 이유는 일부 유저가 가입 시 직접 연령 정보를 입력했기 때문입니다.
    </div>
  </div>

  <!-- 섹션 6 -->
  <div class="section">
    <div class="section-title"><span class="section-num">06</span>미인증 4,096명 케이스 분류</div>
    <div class="chart-wrap">
      <img src="{img4}" alt="케이스 분류">
    </div>
    <div class="desc-box">
      미인증 유저를 age·gender 신뢰 여부에 따라 네 케이스로 분류하면,
      <span class="highlight">91.2%(A+B+C = 3,735건)</span>가 age 또는 gender 중 하나 이상을 신뢰할 수 없습니다.
      실제 정보가 있는 케이스 D는 <strong>361건(8.8%)</strong>에 불과합니다.
    </div>
    <table>
      <tr>
        <th>케이스</th><th>조건</th><th>건수</th><th>비율</th><th>신뢰 가능 여부</th>
      </tr>
      <tr>
        <td><strong>A</strong></td>
        <td>age = 40 &amp; gender = N (완전 기본값)</td>
        <td>{len(caseA):,}</td><td>{len(caseA)/len(unverified)*100:.1f}%</td>
        <td style="color:#C0392B">age·gender 모두 불가</td>
      </tr>
      <tr>
        <td><strong>B</strong></td>
        <td>age = 40, gender = F/M</td>
        <td>{len(caseB):,}</td><td>{len(caseB)/len(unverified)*100:.1f}%</td>
        <td style="color:#E67E22">age 불가, gender 가능</td>
      </tr>
      <tr>
        <td><strong>C</strong></td>
        <td>age ≠ 40, gender = N</td>
        <td>{len(caseC):,}</td><td>{len(caseC)/len(unverified)*100:.1f}%</td>
        <td style="color:#E67E22">age 가능, gender 불가</td>
      </tr>
      <tr>
        <td><strong>D</strong></td>
        <td>age ≠ 40 &amp; gender = F/M (실제 정보)</td>
        <td>{len(caseD):,}</td><td>{len(caseD)/len(unverified)*100:.1f}%</td>
        <td style="color:#27AE60">age·gender 모두 가능</td>
      </tr>
    </table>
  </div>

  <!-- 섹션 7 -->
  <div class="section">
    <div class="section-title"><span class="section-num">07</span>기본값 제거 전/후 age 분포 비교</div>
    <div class="chart-wrap">
      <img src="{img5}" alt="기본값 제거 전후 비교">
    </div>
    <div class="desc-box">
      미인증 유저의 age를 결측치로 처리하면 age = 40의 과대 표현이 해소되고,
      실제 이용자 연령대는 <strong>20-30대에 집중</strong>된 분포로 나타납니다.
    </div>
  </div>

  <!-- 섹션 8 -->
  <div class="section">
    <div class="section-title"><span class="section-num">08</span>전체 구조 요약 &mdash; age = 40 구성 분해</div>
    <div class="chart-wrap">
      <img src="{img6}" alt="age=40 구성 분해">
    </div>
    <div class="desc-box">
      전체 age = 40 레코드 5,104건 중 <strong>실제 36-40세</strong>는 {real_age40:,}건({real_age40/5104*100:.1f}%)에 불과합니다.
      나머지 <span class="highlight">{fake_total:,}건({fake_total/5104*100:.1f}%)</span>은 iOS 기본값 또는 비-iOS 미인증 기본값입니다.
    </div>
  </div>

  <hr>

  <!-- 결론 -->
  <div class="section">
    <div class="section-title"><span class="section-num">09</span>결론 및 모델링 처리 방향</div>
    <div class="conclusion-box">
      <h3>원인 요약</h3>
      <p>
        미인증 유저(is_user_verified = N)에게 시스템이 자동으로 <strong>age = 40, gender = N을 기본값으로 부여</strong>합니다.
        주요 경로는 두 가지입니다.
      </p>
      <ol style="margin-top:10px;">
        <li><strong>iOS 앱스토어 결제 (billing_method = 140)</strong> &mdash; 애플 정책상 개인정보 미전달, 2,134건(52.1%)</li>
        <li><strong>비-iOS 결제 후 본인인증 미실시</strong> &mdash; 인증 절차 생략, 1,487건(36.3%)</li>
      </ol>
    </div>
    <br>
    <div class="conclusion-box">
      <h3>모델링 처리 권장사항</h3>
      <ol>
        <li><strong>is_user_verified = N인 경우 age, gender를 결측치(NaN)로 처리</strong> &mdash; 기본값이 모델에 노이즈로 작용하는 것을 방지</li>
        <li><strong>billing_method = 140 (iOS) 여부를 별도 피처로 추가</strong> &mdash; iOS 유저의 행동 패턴을 독립적으로 학습</li>
        <li><strong>gender = N도 결측치로 처리</strong> &mdash; 미인증과 동일 논리 적용</li>
        <li><strong>인증 유저 13,487건의 age/gender만 신뢰하여 분석 및 학습</strong></li>
      </ol>
    </div>
  </div>

</div>
</body>
</html>"""

output_path = REPORTS_DIR / 'age40_analysis_report.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(HTML)

print(f"HTML 저장 완료: {output_path}")
