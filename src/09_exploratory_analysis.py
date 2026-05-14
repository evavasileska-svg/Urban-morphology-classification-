import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats
import sys

sys.path.append(str(Path(__file__).parent.parent))
from src.config import PROCESSED_DIR, RESULTS_DIR

# ── setup ──────────────────────────────────────────────────────────
pd.set_option('display.float_format', '{:.4f}'.format)
sns.set_theme(style='whitegrid')
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

print("Loading terrain-entropy dataset...")

df = pd.read_csv(PROCESSED_DIR / "terrain_entropy_analysis.csv")

print(f"Patches loaded: {len(df)}")
print(f"Columns: {list(df.columns)}")
print()
print("Basic statistics:")
print(df[['entropy_normalised',
          'orientation_order_phi',
          'mean_slope_deg',
          'max_slope_deg',
          'elevation_variance']].describe())
print()

# ── 1. histograms ──────────────────────────────────────────────────
print("Plotting histograms...")

fig, axes = plt.subplots(1, 5, figsize=(22, 5))
fig.suptitle('Distribution of terrain and entropy features',
             fontsize=14)

configs = [
    ('entropy_normalised',    'Entropy normalised (Ho)',
     'steelblue',  False),
    ('orientation_order_phi', 'Orientation order phi (φ)',
     'darkorange', False),
    ('mean_slope_deg',        'Mean slope (degrees)',
     'green',      False),
    ('max_slope_deg',         'Max slope (degrees)',
     'darkgreen',  False),
    ('elevation_variance',    'Elevation variance',
     'purple',     True),   # log scale
]

for ax, (col, title, color, log_scale) in zip(axes, configs):
    data = df[col].dropna()
    ax.hist(data, bins=50, color=color,
            edgecolor='white', linewidth=0.5)
    ax.set_title(title, fontsize=11)
    ax.set_xlabel(col, fontsize=9)
    ax.set_ylabel('count')
    ax.axvline(data.mean(), color='red', linestyle='--',
               label=f'mean={data.mean():.3f}')
    ax.legend(fontsize=8)
    if log_scale:
        ax.set_yscale('log')

plt.tight_layout()
plt.savefig(RESULTS_DIR / "terrain_01_histograms.png",
            dpi=150, bbox_inches='tight')
plt.show()
print("Saved: terrain_01_histograms.png")

# ── 2. scatter plots — each terrain feature vs entropy ────────────
print("\nPlotting scatter plots...")

fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle('Terrain features vs Street Network Entropy',
             fontsize=14)

terrain_features = [
    ('mean_slope_deg',     'Mean slope (degrees)',     False),
    ('max_slope_deg',      'Max slope (degrees)',      False),
    ('elevation_variance', 'Elevation variance (log)', True),
]

targets = [
    ('entropy_normalised',    'Entropy normalised'),
    ('orientation_order_phi', 'Orientation order phi (φ)'),
]

# sample for speed
sample = df.dropna().sample(min(5000, len(df)), random_state=42)

for col_idx, (feat, feat_label, use_log) in \
        enumerate(terrain_features):
    for row_idx, (target, target_label) in enumerate(targets):

        ax = axes[row_idx, col_idx]

        x = np.log1p(sample[feat]) if use_log else sample[feat]
        y = sample[target]

        ax.scatter(x, y, alpha=0.3, s=8, color='steelblue')

        # trend line
        clean = pd.DataFrame({'x': x, 'y': y}).dropna()
        if len(clean) > 10:
            m, b, r, p, _ = stats.linregress(clean['x'], clean['y'])
            x_line = np.linspace(clean['x'].min(),
                                  clean['x'].max(), 100)
            ax.plot(x_line, m * x_line + b,
                    color='red', linewidth=2,
                    label=f'r={r:.3f}  p={p:.3f}')
            ax.legend(fontsize=9)

        x_label = f'log({feat}+1)' if use_log else feat_label
        ax.set_xlabel(x_label, fontsize=9)
        ax.set_ylabel(target_label, fontsize=9)
        ax.set_title(f'{feat_label} vs {target_label}', fontsize=10)

plt.tight_layout()
plt.savefig(RESULTS_DIR / "terrain_02_scatter.png",
            dpi=150, bbox_inches='tight')
plt.show()
print("Saved: terrain_02_scatter.png")

# ── 3. box plots — entropy by slope category ──────────────────────
print("\nPlotting box plots...")

df_clean = df.dropna(subset=['mean_slope_deg']).copy()
df_clean['slope_category'] = pd.cut(
    df_clean['mean_slope_deg'],
    bins=[0, 2, 5, 100],
    labels=['flat\n(0–2°)', 'moderate\n(2–5°)', 'steep\n(5°+)']
)

fig, axes = plt.subplots(1, 2, figsize=(12, 6))
fig.suptitle('Entropy and phi by terrain slope category',
             fontsize=14)

sns.boxplot(data=df_clean, x='slope_category',
            y='entropy_normalised',
            palette='Blues', ax=axes[0])
axes[0].set_title('Entropy normalised by slope category')
axes[0].set_xlabel('Slope category')
axes[0].set_ylabel('Entropy normalised')

# add mean values on top of each box
for i, cat in enumerate(['flat\n(0–2°)',
                          'moderate\n(2–5°)',
                          'steep\n(5°+)']):
    subset = df_clean[df_clean['slope_category'] == cat]
    mean_val = subset['entropy_normalised'].mean()
    axes[0].text(i, mean_val + 0.01, f'{mean_val:.3f}',
                 ha='center', fontsize=9, color='darkred')

sns.boxplot(data=df_clean, x='slope_category',
            y='orientation_order_phi',
            palette='Oranges', ax=axes[1])
axes[1].set_title('Phi (φ) by slope category')
axes[1].set_xlabel('Slope category')
axes[1].set_ylabel('Orientation order phi')

for i, cat in enumerate(['flat\n(0–2°)',
                          'moderate\n(2–5°)',
                          'steep\n(5°+)']):
    subset = df_clean[df_clean['slope_category'] == cat]
    mean_val = subset['orientation_order_phi'].mean()
    axes[1].text(i, mean_val + 0.01, f'{mean_val:.3f}',
                 ha='center', fontsize=9, color='darkred')

plt.tight_layout()
plt.savefig(RESULTS_DIR / "terrain_03_boxplots.png",
            dpi=150, bbox_inches='tight')
plt.show()
print("Saved: terrain_03_boxplots.png")

# ── 4. correlation matrix ─────────────────────────────────────────
print("\nComputing correlation matrix...")

corr_cols = ['entropy_normalised', 'orientation_order_phi',
             'mean_slope_deg', 'max_slope_deg',
             'elevation_variance']

corr_df = df[corr_cols].dropna()
corr_matrix = corr_df.corr()

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle('Correlation matrices — terrain vs entropy',
             fontsize=14)

# Pearson
sns.heatmap(corr_matrix,
            annot=True, fmt='.3f',
            cmap='RdBu_r', center=0,
            vmin=-1, vmax=1,
            square=True, ax=axes[0])
axes[0].set_title('Pearson correlation')

# Spearman
spearman_matrix = corr_df.corr(method='spearman')
sns.heatmap(spearman_matrix,
            annot=True, fmt='.3f',
            cmap='RdBu_r', center=0,
            vmin=-1, vmax=1,
            square=True, ax=axes[1])
axes[1].set_title('Spearman correlation')

plt.tight_layout()
plt.savefig(RESULTS_DIR / "terrain_04_correlation.png",
            dpi=150, bbox_inches='tight')
plt.show()
print("Saved: terrain_04_correlation.png")

# ── 5. pairplot ───────────────────────────────────────────────────
print("\nPlotting pairplot...")

pairplot_df = df[corr_cols].dropna().sample(
    min(3000, len(df)), random_state=42
)

g = sns.pairplot(pairplot_df,
                 diag_kind='hist',
                 plot_kws={'alpha': 0.3, 's': 8},
                 diag_kws={'bins': 40})
g.figure.suptitle(
    'Pairplot — terrain features vs entropy',
    y=1.02, fontsize=14
)
g.savefig(RESULTS_DIR / "terrain_05_pairplot.png",
          dpi=150, bbox_inches='tight')
plt.show()
print("Saved: terrain_05_pairplot.png")

# ── 6. print correlation summary ──────────────────────────────────
print("\n" + "="*55)
print("CORRELATION SUMMARY")
print("="*55)

print("\nPearson correlations with entropy_normalised:")
pearson = corr_df.corr()['entropy_normalised'].drop(
    'entropy_normalised'
).sort_values(key=abs, ascending=False)
for col, val in pearson.items():
    strength = "strong" if abs(val) > 0.5 else \
               "moderate" if abs(val) > 0.3 else "weak"
    print(f"  {col:30} r={val:+.4f}  ({strength})")

print("\nSpearman correlations with entropy_normalised:")
spearman = corr_df.corr(method='spearman')[
    'entropy_normalised'
].drop('entropy_normalised').sort_values(
    key=abs, ascending=False
)
for col, val in spearman.items():
    strength = "strong" if abs(val) > 0.5 else \
               "moderate" if abs(val) > 0.3 else "weak"
    print(f"  {col:30} r={val:+.4f}  ({strength})")

print("\nAnalysis complete.")
print(f"All figures saved to {RESULTS_DIR}")