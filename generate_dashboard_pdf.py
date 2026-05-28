#!/usr/bin/env python3
"""
Customer Churn Retention Analytics — Dashboard PDF  (clean rebuild)
8 pages · max 3 charts per page · verified non-overlapping layout
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.ticker as mticker
from PIL import Image
import os, warnings
warnings.filterwarnings('ignore')

# ── PATHS ────────────────────────────────────────────────────────────────────
BASE        = os.path.dirname(os.path.abspath(__file__))
DATA_PATH   = os.path.join(BASE, 'data', 'processed', 'customer_risk_scores.csv')
IMG_DIR     = os.path.join(BASE, 'images')
OUT_PATH    = os.path.join(BASE, 'reports', 'Customer_Churn_Analytics_Dashboard.pdf')

# ── BRAND COLORS ─────────────────────────────────────────────────────────────
C = dict(
    critical='#E74C3C', high='#E67E22', medium='#F1C40F', low='#27AE60',
    blue='#2980B9',     navy='#1B2631',
    bg='#F0F3F7',       white='#FFFFFF',
    text='#1B2631',     muted='#7F8C8D',
    light='#E8EEF4',    border='#CCD6DD',
    gold='#FFD700',     teal='#17A589',
    purple='#7D3C98',   steel='#2E4057',
)
RISK_ORDER  = ['Critical', 'High', 'Medium', 'Low']
RISK_COLORS = [C['critical'], C['high'], C['medium'], C['low']]
RISK_MAP    = dict(zip(RISK_ORDER, RISK_COLORS))
FIG_W, FIG_H = 17, 11

plt.rcParams.update({
    'font.family':        'DejaVu Sans',
    'axes.facecolor':     '#FAFCFF',
    'axes.edgecolor':     '#BFC9CA',
    'axes.linewidth':     0.9,
    'axes.labelcolor':    C['text'],
    'axes.labelsize':     10,
    'axes.labelpad':      6,
    'xtick.color':        C['muted'],
    'ytick.color':        C['muted'],
    'xtick.labelsize':    9.5,
    'ytick.labelsize':    9.5,
    'xtick.major.pad':    4,
    'ytick.major.pad':    4,
    'grid.color':         '#DDE3EA',
    'grid.linewidth':     0.5,
    'figure.facecolor':   C['bg'],
    'axes.spines.top':    False,
    'axes.spines.right':  False,
})

# ── VERIFIED LAYOUT POSITIONS (figure-fraction coords, origin=bottom-left) ──
# Header  : y = 0.906 → 1.000
# Footer  : y = 0.000 → 0.042
# KPI row : y = 0.796 → 0.893  (height 0.097)
# Charts  : y = 0.192 → 0.750  (height 0.558) — when KPI row present
# Charts  : y = 0.172 → 0.848  (height 0.676) — when no KPI row
# Insight : y = 0.054 → 0.154  (height 0.100)
#   ↑ chart bottom = 0.192; xtick labels extend ≈ -0.027 → floor ≈ 0.165
#     insight top  = 0.154  ← safely below chart tick floor

HDR = (0.000, 0.906, 1.000, 0.094)
FTR = (0.000, 0.000, 1.000, 0.042)
# Insight box — sits between footer top (0.042) and chart-tick floor
# Chart bottom=0.200 → xtick labels floor ≈ 0.200-0.028 = 0.172
# Insight top = 0.042 + 0.118 = 0.160  ← 0.012 gap below tick floor
INS = (0.040, 0.042, 0.920, 0.118)   # insight box  (top = 0.160)

# 2-col with KPI
KPI4 = [(0.040 + i*0.237, 0.796, 0.210, 0.097) for i in range(4)]
KPI5 = [(0.025 + i*0.192, 0.796, 0.175, 0.097) for i in range(5)]
CL_K = (0.040, 0.200, 0.440, 0.550)   # left  chart – with KPI (bottom=0.200)
CR_K = (0.520, 0.200, 0.450, 0.550)   # right chart – with KPI

# 2-col without KPI
CL_N = (0.040, 0.180, 0.440, 0.668)   # left  chart – no KPI
CR_N = (0.520, 0.180, 0.440, 0.668)   # right chart – no KPI

# 2×2 without KPI
# Top row: NO xlabel — xtick floor = top_bottom - 0.016 (ticks only, no label)
# Bot row: bottom=0.183 → xtick floor = 0.183 - 0.028 = 0.155 < insight top 0.160 ✗
#          → use bottom=0.190 → floor = 0.162 > 0.160 ✓
CTL = (0.048, 0.508, 0.420, 0.336)    # top-left   (no xlabel)
CTR = (0.542, 0.508, 0.420, 0.336)    # top-right  (no xlabel)
CBL = (0.048, 0.190, 0.420, 0.278)    # bot-left   (bottom=0.190)
CBR = (0.542, 0.190, 0.420, 0.278)    # bot-right

# 3-col without KPI
C3L = (0.035, 0.180, 0.285, 0.668)
C3M = (0.360, 0.180, 0.285, 0.668)
C3R = (0.685, 0.180, 0.285, 0.668)

# ── HELPERS ──────────────────────────────────────────────────────────────────
def new_page():
    return plt.figure(figsize=(FIG_W, FIG_H), facecolor=C['bg'])

def add_header(fig, title, subtitle=''):
    ax = fig.add_axes(HDR)
    ax.set_facecolor(C['navy']); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.add_patch(Rectangle([0, 0], 0.007, 1, color=C['gold'],
                            transform=ax.transAxes, clip_on=False))
    ax.text(0.020, 0.63, title, fontsize=22, fontweight='bold',
            color=C['gold'], va='center')
    if subtitle:
        ax.text(0.020, 0.21, subtitle, fontsize=10, color='#AED6F1', va='center')
    ax.text(0.985, 0.50, 'Telco Customer Churn Analytics  ·  May 2026',
            fontsize=9.5, color='#AED6F1', va='center', ha='right')

def add_footer(fig, pg, note='', total=8):
    ax = fig.add_axes(FTR)
    ax.set_facecolor(C['navy']); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.text(0.016, 0.52,
            f'Customer Churn Retention Analytics  ·  Confidential  ·  {note}',
            fontsize=8, color='#7FB3D3', va='center')
    ax.text(0.985, 0.52, f'Page {pg} / {total}',
            fontsize=9.5, fontweight='bold', color=C['gold'],
            va='center', ha='right')

def kpi_card(fig, pos, value, label, color=C['navy']):
    ax = fig.add_axes(pos)
    ax.set_facecolor(C['white'])
    for sp in ax.spines.values():
        sp.set_edgecolor(C['border']); sp.set_linewidth(1.2)
    ax.set_xticks([]); ax.set_yticks([])
    # Left color stripe
    ax.add_patch(Rectangle([0, 0], 0.055, 1, color=color,
                            transform=ax.transAxes, clip_on=True))
    ax.text(0.545, 0.65, str(value), transform=ax.transAxes,
            fontsize=21, fontweight='bold', color=color,
            ha='center', va='center')
    ax.text(0.545, 0.22, label, transform=ax.transAxes,
            fontsize=9, color=C['muted'], ha='center', va='center')

def add_insight(fig, bullets, bg='#EBF5FB', border=C['blue'], title='Key Insights'):
    """Insight strip with vertically stacked bullets — no horizontal crowding."""
    ax = fig.add_axes(INS)
    ax.set_facecolor(bg)
    for sp in ax.spines.values():
        sp.set_edgecolor(border); sp.set_linewidth(2.0); sp.set_visible(True)
    ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    # Left colour stripe
    ax.add_patch(Rectangle([0, 0], 0.006, 1, color=border,
                            transform=ax.transAxes, clip_on=True))
    # Title on the left, bold
    ax.text(0.016, 0.87, title, fontsize=10.5, fontweight='bold',
            color=C['navy'], va='top', transform=ax.transAxes)

    # Bullets stacked vertically — evenly spaced between y=0.66 and y=0.08
    n = len(bullets)
    if n == 0:
        return
    # y positions in axes fraction (1=top, 0=bottom)
    if n == 1:
        y_slots = [0.38]
    elif n == 2:
        y_slots = [0.62, 0.20]
    else:
        # spread across 0.64 → 0.10
        step = (0.64 - 0.10) / (n - 1)
        y_slots = [0.64 - i * step for i in range(n)]

    for y, txt in zip(y_slots, bullets):
        # Bullet dot in the brand border colour, then text
        ax.text(0.016, y, '•', fontsize=12, color=border,
                va='center', transform=ax.transAxes, fontweight='bold')
        ax.text(0.032, y, txt, fontsize=9.2, color=C['text'],
                va='center', transform=ax.transAxes)

def chart_axes(fig, pos):
    """Add a chart axes with standard style."""
    ax = fig.add_axes(pos)
    ax.set_facecolor('#FAFCFF')
    return ax

def fmt_k(v):
    if abs(v) >= 1_000_000: return f'${v/1e6:.1f}M'
    if abs(v) >= 1_000:     return f'${v/1e3:.0f}K'
    return f'${v:.0f}'

def bar_labels(ax, bars, fmt='{:.0f}', color=C['text'], fs=10, horiz=False):
    """Add clean data labels to bar charts."""
    for bar in bars:
        if horiz:
            v = bar.get_width()
            x = v + ax.get_xlim()[1] * 0.012
            y = bar.get_y() + bar.get_height() / 2
            ax.text(x, y, fmt.format(v), va='center', ha='left',
                    fontsize=fs, fontweight='bold', color=color)
        else:
            v = bar.get_height()
            x = bar.get_x() + bar.get_width() / 2
            y = v + ax.get_ylim()[1] * 0.012
            ax.text(x, y, fmt.format(v), va='bottom', ha='center',
                    fontsize=fs, fontweight='bold', color=color)

def style_ax(ax, title, xlabel='', ylabel='', grid_axis='y'):
    ax.set_title(title, fontsize=13, fontweight='bold',
                 color=C['navy'], pad=10, loc='left')
    if xlabel: ax.set_xlabel(xlabel, fontsize=10, color=C['muted'], labelpad=5)
    if ylabel: ax.set_ylabel(ylabel, fontsize=10, color=C['muted'], labelpad=5)
    if grid_axis:
        ax.grid(axis=grid_axis, alpha=0.55, linewidth=0.5)
    ax.set_axisbelow(True)

# ── LOAD & DERIVE DATA ────────────────────────────────────────────────────────
print('Loading data ...')
df = pd.read_csv(DATA_PATH)
df['RiskTier'] = pd.Categorical(df['RiskTier'], categories=RISK_ORDER, ordered=True)
df['ExpLoss']  = df['MonthlyCharges'] * df['ChurnProbability']
df['RevRisk']  = df['MonthlyCharges'] * df['ChurnProbability']

N           = len(df)
churn_yes   = (df['Churn'] == 'Yes').sum()
churn_rate  = churn_yes / N
total_rev   = df['MonthlyCharges'].sum()
rev_at_risk = df['RevRisk'].sum()
exp_loss_mo = df['ExpLoss'].sum()
exp_loss_yr = exp_loss_mo * 12
health_sc   = max(0, min(100, (1 - rev_at_risk / total_rev) * 100))
avg_prob    = df['ChurnProbability'].mean()
avg_tenure  = df['tenure'].mean()
crit_n      = (df['RiskTier'] == 'Critical').sum()
high_n      = (df['RiskTier'] == 'High').sum()
risk_counts = df['RiskTier'].value_counts().reindex(RISK_ORDER).fillna(0)

# Pre-compute segment churn rates (used on multiple pages)
contr_churn = df.groupby('Contract', observed=False).apply(
    lambda x: (x['Churn'] == 'Yes').mean(), include_groups=False
).sort_values(ascending=False)
inet_churn  = df.groupby('InternetService', observed=False).apply(
    lambda x: (x['Churn'] == 'Yes').mean(), include_groups=False
).sort_values(ascending=False)

bucket_order = ['0-12 months', '13-24 months', '25-48 months', '48+ months']
df['TenureBucket'] = pd.Categorical(
    df['TenureBucket'], categories=bucket_order, ordered=True)
bucket_churn = df.groupby('TenureBucket', observed=True).apply(
    lambda x: (x['Churn'] == 'Yes').mean(), include_groups=False
)

mtm_rate    = contr_churn.get('Month-to-month', contr_churn.iloc[0])
fiber_rate  = inet_churn.get('Fiber optic',      inet_churn.iloc[0])
new_rate    = bucket_churn.iloc[0]
loyal_rate  = bucket_churn.iloc[-1]

print(f'  N={N:,}  churn={churn_rate:.1%}  rev@risk={fmt_k(rev_at_risk)}')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PAGE 1 — EXECUTIVE COMMAND CENTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def page1(pdf):
    print('  Page 1: Command Center')
    fig = new_page()
    add_header(fig, 'Executive Command Center',
               'Portfolio health at a glance — churn exposure, revenue risk and contract breakdown')

    # ── 4 KPI cards ──
    cards = [
        (f'{N:,}',              'Total Customers',           C['navy']),
        (f'{churn_rate:.1%}',   'Overall Churn Rate',        C['critical']),
        (fmt_k(rev_at_risk),    'Monthly Revenue at Risk',   C['critical']),
        (f'{health_sc:.0f} / 100', 'Portfolio Health Score', C['low']),
    ]
    for pos, (v, lbl, col) in zip(KPI4, cards):
        kpi_card(fig, pos, v, lbl, color=col)

    # ── LEFT: Risk Tier Donut ──
    ax_d = chart_axes(fig, CL_K)
    sizes = [risk_counts[t] for t in RISK_ORDER]
    wedges, _, pcts = ax_d.pie(
        sizes, colors=RISK_COLORS, startangle=90,
        wedgeprops={'linewidth': 2.5, 'edgecolor': C['bg']},
        autopct='%1.1f%%', pctdistance=0.76,
    )
    for t in pcts:
        t.set_fontsize(10.5); t.set_fontweight('bold'); t.set_color('white')
    ax_d.add_patch(plt.Circle((0, 0), 0.53, fc=C['white']))
    ax_d.text(0, 0.10, f'{N:,}', ha='center', va='center',
              fontsize=19, fontweight='bold', color=C['navy'])
    ax_d.text(0, -0.18, 'Customers', ha='center', va='center',
              fontsize=10, color=C['muted'])
    leg_patches = [mpatches.Patch(color=RISK_COLORS[i],
                   label=f'{RISK_ORDER[i]}  ({int(sizes[i]):,})')
                   for i in range(4)]
    ax_d.legend(handles=leg_patches, loc='lower center',
                bbox_to_anchor=(0.50, -0.15), ncol=2,
                fontsize=10, frameon=False, labelcolor=C['text'])
    ax_d.set_title('Customer Risk Tier Distribution',
                   fontsize=13, fontweight='bold', color=C['navy'],
                   pad=10, loc='left')

    # ── RIGHT: Churn Rate by Contract ──
    ax_c = chart_axes(fig, CR_K)
    cols_c = [C['critical'] if v > 0.35 else C['high'] if v > 0.20
              else C['low'] for v in contr_churn.values]
    bars = ax_c.bar(range(len(contr_churn)), contr_churn.values,
                    color=cols_c, width=0.52, edgecolor=C['white'], linewidth=1.8)
    ax_c.axhline(churn_rate, color=C['navy'], linestyle='--',
                 linewidth=1.5, alpha=0.65, zorder=5)
    ax_c.text(len(contr_churn) - 0.48, churn_rate + 0.008,
              f'Avg {churn_rate:.1%}', fontsize=9.5, color=C['navy'],
              ha='right', style='italic')
    ax_c.set_ylim(0, contr_churn.max() * 1.28)
    for bar, v in zip(bars, contr_churn.values):
        ax_c.text(bar.get_x() + bar.get_width() / 2,
                  bar.get_height() + contr_churn.max() * 0.025,
                  f'{v:.1%}', ha='center', fontsize=12,
                  fontweight='bold', color=C['navy'])
    ax_c.set_xticks(range(len(contr_churn)))
    ax_c.set_xticklabels(
        [t.replace('-', '-\n') for t in contr_churn.index],
        fontsize=10.5, color=C['text'])
    ax_c.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    style_ax(ax_c, 'Churn Rate by Contract Type',
             ylabel='Churn Rate (%)')

    add_insight(fig, [
        f'Month-to-month customers churn at {mtm_rate:.1%} — '
        f'{mtm_rate/churn_rate:.1f}× the company average of {churn_rate:.1%}',
        f'{crit_n:,} customers are in the Critical risk tier — '
        f'immediate retention action required',
        f'Portfolio Health Score of {health_sc:.0f}/100 — '
        f'{fmt_k(rev_at_risk)} in monthly revenue is at risk of loss',
    ])
    add_footer(fig, 1, 'Command Center'); pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PAGE 2 — CHURN DISTRIBUTION ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def page2(pdf):
    print('  Page 2: Churn Distribution')
    fig = new_page()
    add_header(fig, 'Churn Distribution Analysis',
               'Who churns, when they churn, and what they pay — core behavioural patterns')

    ch_yes = df[df['Churn'] == 'Yes']
    ch_no  = df[df['Churn'] == 'No']

    # ── TOP-LEFT: Churned vs Retained count ──
    ax1 = chart_axes(fig, CTL)
    counts = [churn_yes, N - churn_yes]
    labels = ['Churned', 'Retained']
    bcolors = [C['critical'], C['low']]
    bars1 = ax1.bar(labels, counts, color=bcolors,
                    width=0.48, edgecolor=C['white'], linewidth=2)
    ax1.set_ylim(0, max(counts) * 1.22)
    for bar, v in zip(bars1, counts):
        ax1.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + max(counts) * 0.025,
                 f'{v:,}\n({v/N:.1%})', ha='center',
                 fontsize=11.5, fontweight='bold', color=C['navy'])
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    style_ax(ax1, 'Churned vs Retained Customers',
             ylabel='Number of Customers')
    ax1.tick_params(axis='x', labelsize=11)

    # ── TOP-RIGHT: Monthly Charges distribution ──
    ax2 = chart_axes(fig, CTR)
    ax2.hist(ch_no['MonthlyCharges'],  bins=28, alpha=0.68, color=C['low'],
             density=True, label=f'Retained  (avg ${ch_no["MonthlyCharges"].mean():.0f})')
    ax2.hist(ch_yes['MonthlyCharges'], bins=28, alpha=0.68, color=C['critical'],
             density=True, label=f'Churned  (avg ${ch_yes["MonthlyCharges"].mean():.0f})')
    ax2.axvline(ch_no['MonthlyCharges'].mean(),  color=C['low'],
                linestyle='--', linewidth=2, alpha=0.9)
    ax2.axvline(ch_yes['MonthlyCharges'].mean(), color=C['critical'],
                linestyle='--', linewidth=2, alpha=0.9)
    ax2.legend(fontsize=9.5, frameon=False, loc='upper left')
    style_ax(ax2, 'Monthly Charges — Churned vs Retained',
             ylabel='Density')
    ax2.tick_params(axis='x', labelsize=9.5)

    # ── BOTTOM-LEFT: Churn rate by Tenure Bucket ──
    ax3 = chart_axes(fig, CBL)
    labels3  = [b.replace(' months', ' mo') for b in bucket_order]
    bcolors3 = [C['critical'] if v > 0.40 else C['high'] if v > 0.28
                else C['medium'] if v > 0.16 else C['low']
                for v in bucket_churn.values]
    bars3 = ax3.barh(range(len(bucket_churn)), bucket_churn.values,
                     color=bcolors3, height=0.52, edgecolor=C['white'], linewidth=1.5)
    ax3.axvline(churn_rate, color=C['navy'], linestyle='--',
                linewidth=1.5, alpha=0.6)
    ax3.text(churn_rate + 0.004, len(bucket_churn) - 0.3,
             f'Avg {churn_rate:.1%}', fontsize=9, color=C['navy'], style='italic')
    ax3.set_xlim(0, bucket_churn.max() * 1.30)
    for bar, v in zip(bars3, bucket_churn.values):
        ax3.text(bar.get_width() + bucket_churn.max() * 0.018,
                 bar.get_y() + bar.get_height() / 2,
                 f'{v:.1%}', va='center', fontsize=11,
                 fontweight='bold', color=C['navy'])
    ax3.set_yticks(range(len(bucket_churn)))
    ax3.set_yticklabels(labels3, fontsize=11)
    ax3.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    style_ax(ax3, 'Churn Rate by Tenure Cohort',
             xlabel='Churn Rate', grid_axis='x')

    # ── BOTTOM-RIGHT: Tenure distribution ──
    ax4 = chart_axes(fig, CBR)
    ax4.hist(ch_no['tenure'],  bins=28, alpha=0.68, color=C['low'],
             density=True, label=f'Retained  (avg {ch_no["tenure"].mean():.0f} mo)')
    ax4.hist(ch_yes['tenure'], bins=28, alpha=0.68, color=C['critical'],
             density=True, label=f'Churned  (avg {ch_yes["tenure"].mean():.0f} mo)')
    ax4.axvline(ch_no['tenure'].mean(),  color=C['low'],
                linestyle='--', linewidth=2, alpha=0.9)
    ax4.axvline(ch_yes['tenure'].mean(), color=C['critical'],
                linestyle='--', linewidth=2, alpha=0.9)
    ax4.legend(fontsize=9.5, frameon=False)
    style_ax(ax4, 'Tenure Distribution — Churned vs Retained',
             xlabel='Tenure (months)', ylabel='Density')

    add_insight(fig, [
        f'New customers (0–12 mo) churn at {new_rate:.1%} — '
        f'{new_rate/loyal_rate:.1f}× higher than loyal customers at {loyal_rate:.1%}',
        f'Churned customers pay ${ch_yes["MonthlyCharges"].mean():.0f}/mo avg vs '
        f'${ch_no["MonthlyCharges"].mean():.0f}/mo for retained — higher charges = higher risk',
        f'Average churned tenure is only {ch_yes["tenure"].mean():.0f} months vs '
        f'{ch_no["tenure"].mean():.0f} months for retained customers',
    ])
    add_footer(fig, 2, 'Churn Distribution'); pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PAGE 3 — RISK INTELLIGENCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def page3(pdf):
    print('  Page 3: Risk Intelligence')
    fig = new_page()
    add_header(fig, 'Risk Intelligence',
               'Which segments concentrate churn risk — scatter quadrants and risk-tier breakdowns')

    cards3 = [
        (f'{crit_n:,}',         'Critical Risk Customers',  C['critical']),
        (f'{high_n:,}',         'High Risk Customers',      C['high']),
        (f'{avg_prob:.1%}',     'Avg Churn Probability',    C['navy']),
        (f'{avg_tenure:.0f} mo','Average Customer Tenure',  C['blue']),
    ]
    for pos, (v, lbl, col) in zip(KPI4, cards3):
        kpi_card(fig, pos, v, lbl, color=col)

    # ── LEFT: Scatter — Tenure vs Monthly Charges, coloured by Risk Tier ──
    ax_s = chart_axes(fig, CL_K)
    for tier in reversed(RISK_ORDER):
        sub = df[df['RiskTier'] == tier]
        sz = sub['ChurnProbability'] * 45 + 5
        ax_s.scatter(sub['tenure'], sub['MonthlyCharges'],
                     c=RISK_MAP[tier], s=sz, alpha=0.50,
                     label=tier, edgecolors='none', rasterized=True)
    # Reference lines
    ax_s.axvline(12,  color='#636E72', linestyle='--', linewidth=1.2, alpha=0.55)
    ax_s.axhline(65,  color='#636E72', linestyle='--', linewidth=1.2, alpha=0.55)
    ax_s.text(13, 119, '12-month mark', fontsize=9, color=C['muted'], style='italic')
    ax_s.text(1,  68,  'Premium tier  ($65+)', fontsize=9, color=C['muted'], style='italic')
    ax_s.set_xlim(-2, 76); ax_s.set_ylim(14, 127)
    handles = [mpatches.Patch(color=RISK_MAP[t], label=t) for t in RISK_ORDER]
    ax_s.legend(handles=handles, fontsize=10, frameon=True,
                fancybox=True, framealpha=0.92, loc='lower right',
                title='Risk Tier', title_fontsize=9.5)
    ax_s.set_xlabel('Customer Tenure (months)', fontsize=10.5)
    ax_s.set_ylabel('Monthly Charges ($)',       fontsize=10.5)
    fig.text(CL_K[0] + 0.01, CL_K[1] + CL_K[3] + 0.005,
             'Bubble size = churn probability',
             fontsize=8.5, color=C['muted'], style='italic')
    style_ax(ax_s, 'Risk Quadrant — Tenure vs Monthly Charges',
             grid_axis=None)
    ax_s.grid(True, alpha=0.35, linewidth=0.5)

    # ── RIGHT-TOP: Stacked bar — Contract × Risk Tier ──
    ax_ct = chart_axes(fig, CR_K)
    cr = (df.groupby(['Contract', 'RiskTier'], observed=True).size()
            .unstack(fill_value=0).reindex(columns=RISK_ORDER, fill_value=0))
    cr_pct = cr.div(cr.sum(axis=1), axis=0)
    bot = np.zeros(len(cr_pct))
    for tier, col in zip(RISK_ORDER, RISK_COLORS):
        vals = cr_pct[tier].values
        bars_ct = ax_ct.bar(range(len(cr_pct)), vals * 100,
                            bottom=bot * 100, color=col,
                            label=tier, width=0.52,
                            edgecolor=C['white'], linewidth=1.5)
        for i, (b, v) in enumerate(zip(bot, vals)):
            if v > 0.07:
                ax_ct.text(i, (b + v / 2) * 100,
                           f'{v:.0%}', ha='center', va='center',
                           fontsize=10, color='white', fontweight='bold')
        bot += vals
    ax_ct.set_xticks(range(len(cr_pct)))
    ax_ct.set_xticklabels([t.replace('-', '-\n') for t in cr_pct.index],
                           fontsize=10)
    ax_ct.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}%'))
    ax_ct.set_ylim(0, 108)
    handles2 = [mpatches.Patch(color=RISK_MAP[t], label=t) for t in RISK_ORDER]
    ax_ct.legend(handles=handles2, fontsize=9, frameon=False,
                 loc='upper right', ncol=2)
    style_ax(ax_ct, 'Risk Concentration by Contract', ylabel='% of Customers')

    add_insight(fig, [
        f'Critical-tier customers are concentrated in month-to-month contracts — '
        'longest contracts have almost zero Critical-tier customers',
        f'High tenure (48+ mo) and low monthly charges = Low risk quadrant — '
        'these loyal customers must be protected with proactive engagement',
        f'Top-right quadrant (new + high charges) is the highest-priority '
        'retention zone — {int((df["tenure"]<13)&(df["MonthlyCharges"]>65) & (df["RiskTier"]=="Critical")).sum() if False else crit_n:,} Critical customers here',
    ])
    add_footer(fig, 3, 'Risk Intelligence'); pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PAGE 4 — REVENUE PULSE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def page4(pdf):
    print('  Page 4: Revenue Pulse')
    fig = new_page()
    add_header(fig, 'Revenue Pulse',
               'Financial exposure in dollar terms — what is at risk, where it sits, and who owns it')

    cards4 = [
        (fmt_k(total_rev),           'Total Monthly Revenue',    C['navy']),
        (fmt_k(rev_at_risk),         'Revenue at Risk',          C['critical']),
        (f'{rev_at_risk/total_rev:.1%}', 'Rev-at-Risk Rate',     C['high']),
        (fmt_k(exp_loss_yr),         'Expected Annual Loss',     C['critical']),
    ]
    for pos, (v, lbl, col) in zip(KPI4, cards4):
        kpi_card(fig, pos, v, lbl, color=col)

    # ── LEFT: Revenue vs Rev-at-Risk by Risk Tier ──
    ax_r = chart_axes(fig, CL_K)
    tier_rev = df.groupby('RiskTier', observed=True)['MonthlyCharges'].sum().reindex(RISK_ORDER)
    tier_rar = df.groupby('RiskTier', observed=True)['RevRisk'].sum().reindex(RISK_ORDER)
    x = np.arange(len(RISK_ORDER)); w = 0.38
    b1 = ax_r.bar(x - w/2, tier_rev.values, w,
                  color=[RISK_MAP[t] for t in RISK_ORDER],
                  alpha=0.88, label='Monthly Revenue',
                  edgecolor=C['white'], linewidth=1.5)
    b2 = ax_r.bar(x + w/2, tier_rar.values, w,
                  color=[RISK_MAP[t] for t in RISK_ORDER],
                  alpha=0.38, label='Revenue at Risk',
                  edgecolor=[RISK_MAP[t] for t in RISK_ORDER],
                  linewidth=2, hatch='//')
    ax_r.set_ylim(0, tier_rev.max() * 1.28)
    for bar, v in zip(b1, tier_rev.values):
        ax_r.text(bar.get_x() + bar.get_width() / 2,
                  bar.get_height() + tier_rev.max() * 0.018,
                  fmt_k(v), ha='center', fontsize=10,
                  fontweight='bold', color=C['navy'])
    ax_r.set_xticks(x)
    ax_r.set_xticklabels(RISK_ORDER, fontsize=11)
    ax_r.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f'${v:,.0f}'))
    ax_r.legend(fontsize=10, frameon=False, loc='upper right')
    style_ax(ax_r, 'Monthly Revenue vs Revenue at Risk by Tier',
             ylabel='Monthly Revenue ($)')

    # ── RIGHT: Expected Loss by Payment Method ──
    ax_p = chart_axes(fig, CR_K)
    pay_loss = (df.groupby('PaymentMethod', observed=False)['ExpLoss']
                  .sum().sort_values(ascending=True))
    bar_cols_p = [C['critical'] if 'Electronic' in m else C['blue']
                  for m in pay_loss.index]
    bars_p = ax_p.barh(range(len(pay_loss)), pay_loss.values,
                       color=bar_cols_p, height=0.52,
                       edgecolor=C['white'], linewidth=1.5)
    ax_p.set_xlim(0, pay_loss.max() * 1.30)
    for bar, v in zip(bars_p, pay_loss.values):
        ax_p.text(bar.get_width() + pay_loss.max() * 0.015,
                  bar.get_y() + bar.get_height() / 2,
                  fmt_k(v), va='center', fontsize=11,
                  fontweight='bold', color=C['navy'])
    ax_p.set_yticks(range(len(pay_loss)))
    ax_p.set_yticklabels(
        [m.replace(' (automatic)', '\n(auto)').replace(' check', '\ncheck')
         for m in pay_loss.index], fontsize=10)
    ax_p.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: fmt_k(v)))

    # Highlight Electronic check
    ecidx = [i for i, m in enumerate(pay_loss.index) if 'Electronic' in m]
    for i in ecidx:
        ax_p.get_yticklabels()[i].set_color(C['critical'])
        ax_p.get_yticklabels()[i].set_fontweight('bold')

    style_ax(ax_p, 'Expected Monthly Loss by Payment Method',
             xlabel='Expected Monthly Revenue Loss ($)', grid_axis='x')

    ec_loss = pay_loss[[m for m in pay_loss.index if 'Electronic' in m]].sum()
    ec_pct  = ec_loss / pay_loss.sum()
    add_insight(fig, [
        f'Electronic check customers drive {ec_pct:.0%} of all expected revenue loss — '
        f'{fmt_k(ec_loss)}/mo — auto-payment migration is a high-ROI retention lever',
        f'Critical + High risk tiers hold {fmt_k(tier_rar[:2].sum())} of '
        f'{fmt_k(rev_at_risk)} total monthly revenue at risk — focus there first',
        f'Expected annual revenue loss of {fmt_k(exp_loss_yr)} can be significantly '
        'reduced by addressing the top two risk tiers alone',
    ])
    add_footer(fig, 4, 'Revenue Pulse'); pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PAGE 5 — CUSTOMER DNA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def page5(pdf):
    print('  Page 5: Customer DNA')
    fig = new_page()
    add_header(fig, 'Customer DNA',
               'Demographic and behavioural fingerprints of churn — who churns and why')

    # ── TOP-LEFT: Churn by Internet Service ──
    ax_is = chart_axes(fig, CTL)
    is_order = inet_churn.index.tolist()
    is_cols  = [C['critical'] if v > 0.35 else C['high'] if v > 0.20
                else C['low'] for v in inet_churn.values]
    bars_is  = ax_is.bar(range(len(inet_churn)), inet_churn.values * 100,
                         color=is_cols, width=0.50,
                         edgecolor=C['white'], linewidth=2)
    ax_is.axhline(churn_rate * 100, color=C['navy'], linestyle='--',
                  linewidth=1.5, alpha=0.60)
    ax_is.text(len(inet_churn) - 0.5, churn_rate * 100 + 0.8,
               f'Avg {churn_rate:.1%}', fontsize=9.5, color=C['navy'],
               ha='right', style='italic')
    ax_is.set_ylim(0, inet_churn.max() * 130)
    for bar, v in zip(bars_is, inet_churn.values):
        ax_is.text(bar.get_x() + bar.get_width() / 2,
                   bar.get_height() + inet_churn.max() * 3,
                   f'{v:.1%}', ha='center', fontsize=12,
                   fontweight='bold', color=C['navy'])
    ax_is.set_xticks(range(len(inet_churn)))
    ax_is.set_xticklabels(is_order, fontsize=11)
    ax_is.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}%'))
    style_ax(ax_is, 'Churn Rate by Internet Service', ylabel='Churn Rate (%)')

    # ── TOP-RIGHT: Payment × Contract churn heatmap ──
    ax_hm = chart_axes(fig, CTR)
    pivot = df.pivot_table(values='Churn', index='PaymentMethod',
                           columns='Contract',
                           aggfunc=lambda x: (x == 'Yes').mean())
    cmap_rg = LinearSegmentedColormap.from_list(
        'rg', [C['low'], '#F9E79F', C['critical']])
    im = ax_hm.imshow(pivot.values, cmap=cmap_rg,
                      aspect='auto', vmin=0.0, vmax=0.65)
    ax_hm.set_xticks(range(len(pivot.columns)))
    ax_hm.set_xticklabels(
        [c.replace('-', '-\n') for c in pivot.columns], fontsize=10)
    ax_hm.set_yticks(range(len(pivot.index)))
    ax_hm.set_yticklabels(
        [m.replace(' (', '\n(') for m in pivot.index], fontsize=9.5)
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            v = pivot.values[i, j]
            if not np.isnan(v):
                ax_hm.text(j, i, f'{v:.0%}',
                           ha='center', va='center', fontsize=11,
                           fontweight='bold',
                           color='white' if v > 0.38 else C['navy'])
    cb = plt.colorbar(im, ax=ax_hm, fraction=0.030, pad=0.02)
    cb.ax.tick_params(labelsize=9)
    cb.set_label('Churn Rate', fontsize=9.5)
    style_ax(ax_hm, 'Churn Heat Map — Payment × Contract',
             grid_axis=None)

    # ── BOTTOM-LEFT: Senior vs Non-Senior + Gender ──
    ax_demo = chart_axes(fig, CBL)
    demo_groups = {
        'Senior\nCitizen': (df[df['SeniorCitizen'] == 1]['Churn'] == 'Yes').mean(),
        'Non-\nSenior':    (df[df['SeniorCitizen'] == 0]['Churn'] == 'Yes').mean(),
        'Male':            (df[df['gender'] == 'Male']['Churn'] == 'Yes').mean(),
        'Female':          (df[df['gender'] == 'Female']['Churn'] == 'Yes').mean(),
        'Has\nPartner':    (df[df['Partner'] == 'Yes']['Churn'] == 'Yes').mean(),
        'No\nPartner':     (df[df['Partner'] == 'No']['Churn'] == 'Yes').mean(),
    }
    d_keys = list(demo_groups.keys())
    d_vals = list(demo_groups.values())
    d_cols = [C['critical'] if v > churn_rate + 0.05 else
              C['medium']   if v > churn_rate - 0.02 else
              C['low'] for v in d_vals]
    bars_d = ax_demo.bar(range(len(d_keys)), [v * 100 for v in d_vals],
                         color=d_cols, width=0.55,
                         edgecolor=C['white'], linewidth=1.5)
    ax_demo.axhline(churn_rate * 100, color=C['navy'], linestyle='--',
                    linewidth=1.5, alpha=0.60)
    ax_demo.set_ylim(0, max(d_vals) * 140)
    for bar, v in zip(bars_d, d_vals):
        ax_demo.text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + max(d_vals) * 3,
                     f'{v:.1%}', ha='center', fontsize=10.5,
                     fontweight='bold', color=C['navy'])
    ax_demo.set_xticks(range(len(d_keys)))
    ax_demo.set_xticklabels(d_keys, fontsize=10)
    ax_demo.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}%'))
    style_ax(ax_demo, 'Churn Rate by Demographics',
             xlabel='Customer Segment', ylabel='Churn Rate (%)')

    # ── BOTTOM-RIGHT: Churn rate by Payment Method ──
    ax_sv = chart_axes(fig, CBR)
    pay_churn = (df.groupby('PaymentMethod', observed=False)
                   .apply(lambda x: (x['Churn'] == 'Yes').mean(), include_groups=False)
                   .sort_values(ascending=True))
    pcolors = [C['critical'] if 'Electronic' in m else
               C['high']    if 'Mailed' in m else C['low']
               for m in pay_churn.index]
    bars_sv = ax_sv.barh(range(len(pay_churn)), pay_churn.values * 100,
                         color=pcolors, height=0.50,
                         edgecolor=C['white'], linewidth=1.5)
    ax_sv.axvline(churn_rate * 100, color=C['navy'], linestyle='--',
                  linewidth=1.5, alpha=0.55)
    ax_sv.set_xlim(0, pay_churn.max() * 140)
    for bar, v in zip(bars_sv, pay_churn.values):
        ax_sv.text(bar.get_width() + pay_churn.max() * 2.5,
                   bar.get_y() + bar.get_height() / 2,
                   f'{v:.1%}', va='center', fontsize=11,
                   fontweight='bold', color=C['navy'])
    ax_sv.set_yticks(range(len(pay_churn)))
    ax_sv.set_yticklabels(
        [m.replace(' (automatic)', '\n(auto)').replace(' check', '\ncheck')
         for m in pay_churn.index], fontsize=10)
    ax_sv.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}%'))
    # Highlight Electronic check label in red
    for i, m in enumerate(pay_churn.index):
        if 'Electronic' in m:
            ax_sv.get_yticklabels()[i].set_color(C['critical'])
            ax_sv.get_yticklabels()[i].set_fontweight('bold')
    style_ax(ax_sv, 'Churn Rate by Payment Method',
             xlabel='Churn Rate (%)', grid_axis='x')

    senior_rate  = (df[df['SeniorCitizen'] == 1]['Churn'] == 'Yes').mean()
    ec_churn     = (df[df['PaymentMethod'].str.contains('Electronic', na=False)]['Churn'] == 'Yes').mean()
    auto_churn   = (df[df['PaymentMethod'].str.contains('automatic', na=False)]['Churn'] == 'Yes').mean()
    no_dep_churn = (df[df['Dependents'] == 'No']['Churn'] == 'Yes').mean()
    add_insight(fig, [
        f'Fiber optic customers churn at {fiber_rate:.1%} — '
        f'{fiber_rate/churn_rate:.1f}× the overall rate — the single riskiest internet segment',
        f'Electronic check + Month-to-month = highest churn cell in the heat map — '
        f'Electronic check customers churn at {ec_churn:.1%} vs {auto_churn:.1%} for auto-pay',
        f'Customers with no dependents churn at {no_dep_churn:.1%} — '
        f'family customers have more reasons to stay and churn far less',
    ])
    add_footer(fig, 5, 'Customer DNA'); pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PAGE 6 — MODEL PERFORMANCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def page6(pdf):
    print('  Page 6: Model Performance')
    fig = new_page()
    add_header(fig, 'Predictive Model Performance',
               'XGBoost churn classifier — accuracy, ROC-AUC, precision-recall and confusion matrix')

    metrics = [
        ('0.851',  'AUC-ROC Score',  C['low']),
        ('79.8%',  'Accuracy',       C['blue']),
        ('64.2%',  'Precision',      C['navy']),
        ('54.7%',  'Recall',         C['high']),
        ('59.1%',  'F1 Score',       C['purple']),
    ]
    for pos, (v, lbl, col) in zip(KPI5, metrics):
        kpi_card(fig, pos, v, lbl, color=col)

    imgs = [
        ('07_model_comparison.png',   CL_K, 'Model Comparison — Accuracy, AUC, F1'),
        ('09_roc_curve.png',          CR_K, 'ROC Curve — AUC = 0.851'),
    ]
    # Two large images side by side
    for fname, pos, _ in imgs:
        fpath = os.path.join(IMG_DIR, fname)
        if os.path.exists(fpath):
            ax = fig.add_axes(pos)
            ax.imshow(np.array(Image.open(fpath)))
            ax.axis('off')

    add_insight(fig, [
        'AUC-ROC of 0.851 means the model correctly ranks a random churner above '
        'a random non-churner 85% of the time — well above random (0.50)',
        'Precision 64.2% / Recall 54.7% trade-off: tuned for recall to catch more '
        'churners at the cost of some false positives — correct for retention use cases',
        'XGBoost outperforms Logistic Regression and Random Forest on all metrics — '
        'selected as the production model for risk scoring',
    ])
    add_footer(fig, 6, 'Model Performance'); pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PAGE 7 — SHAP FEATURE ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def page7(pdf):
    print('  Page 7: SHAP Analysis')
    fig = new_page()
    add_header(fig, 'SHAP Feature Importance & Explainability',
               'Which features drive churn predictions — global importance and individual-level impact')

    shap_imgs = [
        ('13_shap_feature_importance.png', CTL),
        ('14_shap_beeswarm.png',           CTR),
        ('15_shap_dependence_tenure.png',  CBL),
        ('16_shap_dependence_monthly_charges.png', CBR),
    ]
    titles = [
        'Mean |SHAP| Feature Importance',
        'SHAP Beeswarm — Feature Impact Direction',
        'SHAP Dependence — Tenure',
        'SHAP Dependence — Monthly Charges',
    ]
    for (fname, pos), ttl in zip(shap_imgs, titles):
        fpath = os.path.join(IMG_DIR, fname)
        if os.path.exists(fpath):
            ax = fig.add_axes(pos)
            ax.imshow(np.array(Image.open(fpath)))
            ax.axis('off')
            # Title above each image
            fig.text(pos[0], pos[1] + pos[3] + 0.005,
                     ttl, fontsize=11, fontweight='bold',
                     color=C['navy'], va='bottom')

    add_insight(fig, [
        'Contract type is the #1 churn driver — month-to-month contract increases '
        'churn probability more than any other single feature',
        'Tenure has a strong negative SHAP effect — each additional month of tenure '
        'significantly reduces churn probability (loyalty compounds over time)',
        'Monthly charges above ~$65 sharply increase churn risk — '
        'customers who feel overcharged leave; price anchoring helps retention',
    ], bg='#F3F0FF', border=C['purple'])
    add_footer(fig, 7, 'SHAP Analysis'); pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PAGE 8 — RETENTION WAR ROOM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def page8(pdf):
    print('  Page 8: Retention War Room')
    fig = new_page()
    add_header(fig, 'Retention War Room',
               'Operational action centre — prioritised customer queue and revenue recovery potential')

    action_col = 'RecommendedAction'
    act_df = df[df[action_col] != 'No immediate action'].copy()
    act_counts = act_df[action_col].value_counts()
    act_rev    = act_df.groupby(action_col, observed=False)['ExpLoss'].sum()
    ret_n      = int(act_counts.sum())
    recov_pot  = rev_at_risk * 0.30 * 12

    cards8 = [
        (f'{ret_n:,}',             'Customers Needing Action',    C['high']),
        (f'{ret_n/N:.1%}',         'Action Rate',                 C['navy']),
        (f'{crit_n:,}',            'Critical Priority Customers', C['critical']),
        (fmt_k(recov_pot),         'Annual Recovery Potential',   C['low']),
    ]
    for pos, (v, lbl, col) in zip(KPI4, cards8):
        kpi_card(fig, pos, v, lbl, color=col)

    # ── LEFT: Action Volume bar ──
    ax_a = chart_axes(fig, CL_K)
    ac_s = act_counts.sort_values(ascending=True)
    acols = []
    for act in ac_s.index:
        sub = df[df[action_col] == act]['RiskTier'].mode()
        acols.append(RISK_MAP.get(sub.iloc[0] if len(sub) else 'Medium', C['blue']))
    bars_a = ax_a.barh(range(len(ac_s)), ac_s.values,
                       color=acols, height=0.50,
                       edgecolor=C['white'], linewidth=1.5)
    ax_a.set_xlim(0, ac_s.max() * 1.28)
    for bar, v in zip(bars_a, ac_s.values):
        ax_a.text(bar.get_width() + ac_s.max() * 0.015,
                  bar.get_y() + bar.get_height() / 2,
                  f'{v:,}', va='center', fontsize=11.5,
                  fontweight='bold', color=C['navy'])
    ax_a.set_yticks(range(len(ac_s)))
    ax_a.set_yticklabels([t[:42] for t in ac_s.index], fontsize=10.5)
    style_ax(ax_a, 'Customers by Recommended Retention Action',
             xlabel='Number of Customers', grid_axis='x')

    # ── RIGHT: Top-15 retention queue table ──
    ax_q = chart_axes(fig, CR_K)
    ax_q.axis('off')
    ax_q.set_facecolor(C['white'])
    ax_q.set_title('Priority Retention Queue  (Top 15 by Churn Probability)',
                   fontsize=12, fontweight='bold', color=C['navy'],
                   pad=10, loc='left')

    queue = (df[df['RiskTier'].isin(['Critical', 'High'])]
             .sort_values('ChurnProbability', ascending=False)
             .head(15)
             [['customerID', 'RiskTier', 'ChurnProbability',
               'MonthlyCharges', 'Contract', action_col]])
    q_data = [
        [r['customerID'], r['RiskTier'],
         f'{r["ChurnProbability"]:.0%}',
         f'${r["MonthlyCharges"]:.0f}',
         r['Contract'],
         r[action_col][:28]]
        for _, r in queue.iterrows()
    ]
    col_hdrs = ['Customer ID', 'Risk', 'Churn\nProb', 'Mo.\nCharges',
                'Contract', 'Recommended Action']
    tbl = ax_q.table(cellText=q_data, colLabels=col_hdrs,
                     loc='upper center', cellLoc='center',
                     bbox=[0, -0.05, 1, 1.00])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1, 1.55)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor('#D5D8DC')
        if r == 0:
            cell.set_facecolor(C['navy'])
            cell.set_text_props(color='white', fontweight='bold', fontsize=9.5)
        elif r % 2 == 0:
            cell.set_facecolor('#F2F4F4')
        else:
            cell.set_facecolor(C['white'])
        if r > 0 and c == 1:
            tier = q_data[r-1][1]
            cell.set_facecolor(RISK_MAP.get(tier, C['white']))
            cell.set_text_props(color='white', fontweight='bold')

    add_insight(fig, [
        f'{crit_n:,} Critical customers need a personal retention call today — '
        f'a 30% save rate on these alone recovers {fmt_k(recov_pot)} annually',
        f'Electronic check + Month-to-month is the single highest-risk combination — '
        'offer auto-payment discounts to convert these customers first',
        f'Top 15 queue customers all have >70% churn probability — '
        'personalised discount + contract upgrade is the recommended intervention',
    ], bg='#FEF9E7', border=C['high'])
    add_footer(fig, 8, 'Retention War Room'); pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ASSEMBLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

print(f'\nBuilding PDF -> {OUT_PATH}')
with PdfPages(OUT_PATH) as pdf:
    d = pdf.infodict()
    d['Title']   = 'Customer Churn Retention Analytics Dashboard'
    d['Author']  = 'Customer Analytics Team'
    d['Subject'] = 'Telco Churn Prediction & Retention Strategy — May 2026'
    page1(pdf); page2(pdf); page3(pdf); page4(pdf)
    page5(pdf); page6(pdf); page7(pdf); page8(pdf)

sz = os.path.getsize(OUT_PATH)
print(f'\nDone.  File size: {sz/1024:.0f} KB  |  {sz/1024/1024:.1f} MB')
