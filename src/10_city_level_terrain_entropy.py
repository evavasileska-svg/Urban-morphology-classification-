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
sns.set_theme(style='whitegrid')
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

print("Loading data...")

df = pd.read_csv(PROCESSED_DIR / "terrain_entropy_analysis.csv")
print(f"Loaded {len(df)} patches from "
      f"{df['city'].nunique()} cities")

# ── aggregate to city level ────────────────────────────────────────
print("\nAggregating to city level...")

city_df = df.groupby('city').agg(
    mean_entropy        = ('entropy_normalised', 'mean'),
    median_entropy      = ('entropy_normalised', 'median'),
    std_entropy         = ('entropy_normalised', 'std'),
    mean_phi            = ('orientation_order_phi', 'mean'),
    mean_slope          = ('mean_slope_deg', 'mean'),
    median_slope        = ('mean_slope_deg', 'median'),
    mean_max_slope      = ('max_slope_deg', 'mean'),
    mean_elev_variance  = ('elevation_variance', 'mean'),
    n_patches           = ('entropy_normalised', 'count'),
).reset_index()

# short city name for labels
city_df['city_short'] = city_df['city'].apply(
    lambda x: x.split(',')[0]
)

print(f"\nCity level dataset: {len(city_df)} cities")
print(city_df[['city_short', 'n_patches',
               'mean_entropy', 'mean_slope']].to_string())

# ── correlations at city level ─────────────────────────────────────
print("\nCity level correlations with mean entropy:")
for col in ['mean_slope', 'median_slope',
            'mean_max_slope', 'mean_elev_variance']:
    clean = city_df[['mean_entropy', col]].dropna()
    r_p, p_p = stats.pearsonr(clean['mean_entropy'], clean[col])
    r_s, p_s = stats.spearmanr(clean['mean_entropy'], clean[col])
    print(f"  {col:25} "
          f"Pearson r={r_p:+.3f} p={p_p:.3f}  "
          f"Spearman r={r_s:+.3f} p={p_s:.3f}")

# ── plot 1: city level scatter — slope vs entropy ──────────────────
print("\nPlotting city level scatter...")

fig, axes = plt.subplots(1, 2, figsize=(16, 7))
fig.suptitle('City level — terrain vs street network entropy\n'
             '(each dot = one city, averaged across all patches)',
             fontsize=13)

# ── left: mean slope vs mean entropy ──────────────────────────────
ax = axes[0]
clean = city_df.dropna(subset=['mean_slope', 'mean_entropy'])

# scatter dots sized by number of patches
sizes = (clean['n_patches'] / clean['n_patches'].max()) * 400 + 50
scatter = ax.scatter(
    clean['mean_slope'],
    clean['mean_entropy'],
    s=sizes,
    alpha=0.8,
    color='steelblue',
    edgecolors='white',
    linewidth=0.8,
    zorder=3
)

# trend line
m, b, r, p, _ = stats.linregress(
    clean['mean_slope'], clean['mean_entropy']
)
x_line = np.linspace(clean['mean_slope'].min(),
                     clean['mean_slope'].max(), 100)
ax.plot(x_line, m * x_line + b,
        color='red', linewidth=2, linestyle='--',
        label=f'r = {r:.3f}   p = {p:.3f}', zorder=2)

# city labels
for _, row in clean.iterrows():
    ax.annotate(
        row['city_short'],
        xy=(row['mean_slope'], row['mean_entropy']),
        xytext=(4, 2),
        textcoords='offset points',
        fontsize=7,
        color='#333333'
    )

ax.set_xlabel('Mean slope (degrees) — city average', fontsize=11)
ax.set_ylabel('Mean entropy normalised — city average', fontsize=11)
ax.set_title('Mean slope vs Mean entropy\n'
             'dot size = number of patches', fontsize=11)
ax.legend(fontsize=10)

# add note about patch level r for comparison
ax.text(0.02, 0.02,
        f'Patch level r = 0.184\nCity level r = {r:.3f}',
        transform=ax.transAxes,
        fontsize=9, color='darkred',
        bbox=dict(boxstyle='round', facecolor='lightyellow',
                  alpha=0.8))

# ── right: elevation variance vs entropy ──────────────────────────
ax2 = axes[1]
clean2 = city_df.dropna(
    subset=['mean_elev_variance', 'mean_entropy']
)

sizes2 = (clean2['n_patches'] / clean2['n_patches'].max()) * 400 + 50
ax2.scatter(
    np.log1p(clean2['mean_elev_variance']),
    clean2['mean_entropy'],
    s=sizes2,
    alpha=0.8,
    color='purple',
    edgecolors='white',
    linewidth=0.8,
    zorder=3
)

m2, b2, r2, p2, _ = stats.linregress(
    np.log1p(clean2['mean_elev_variance']),
    clean2['mean_entropy']
)
x_line2 = np.linspace(
    np.log1p(clean2['mean_elev_variance']).min(),
    np.log1p(clean2['mean_elev_variance']).max(), 100
)
ax2.plot(x_line2, m2 * x_line2 + b2,
         color='red', linewidth=2, linestyle='--',
         label=f'r = {r2:.3f}   p = {p2:.3f}', zorder=2)

for _, row in clean2.iterrows():
    ax2.annotate(
        row['city_short'],
        xy=(np.log1p(row['mean_elev_variance']),
            row['mean_entropy']),
        xytext=(4, 2),
        textcoords='offset points',
        fontsize=7,
        color='#333333'
    )

ax2.set_xlabel('log(Mean elevation variance + 1) — city average',
               fontsize=11)
ax2.set_ylabel('Mean entropy normalised — city average', fontsize=11)
ax2.set_title('Elevation variance vs Mean entropy\n'
              'dot size = number of patches', fontsize=11)
ax2.legend(fontsize=10)

ax2.text(0.02, 0.02,
         f'Patch level r = 0.257\nCity level r = {r2:.3f}',
         transform=ax2.transAxes,
         fontsize=9, color='darkred',
         bbox=dict(boxstyle='round', facecolor='lightyellow',
                   alpha=0.8))

plt.tight_layout()
plt.savefig(RESULTS_DIR / "city_01_slope_vs_entropy.png",
            dpi=150, bbox_inches='tight')
plt.show()
print("Saved: city_01_slope_vs_entropy.png")

# ── plot 2: bar chart — cities ranked by entropy ───────────────────
print("\nPlotting city ranking...")

city_sorted = city_df.sort_values('mean_entropy')

fig, ax = plt.subplots(figsize=(14, 8))

bars = ax.barh(
    city_sorted['city_short'],
    city_sorted['mean_entropy'],
    color=plt.cm.RdYlBu_r(
        (city_sorted['mean_entropy'] - city_sorted['mean_entropy'].min()) /
        (city_sorted['mean_entropy'].max() - city_sorted['mean_entropy'].min())
    ),
    edgecolor='white',
    linewidth=0.5
)

# add slope value as text on each bar
for i, (_, row) in enumerate(city_sorted.iterrows()):
    slope_text = f"slope={row['mean_slope']:.1f}°" \
                 if not pd.isna(row['mean_slope']) else ''
    ax.text(row['mean_entropy'] + 0.002, i,
            f"{row['mean_entropy']:.3f}  {slope_text}",
            va='center', fontsize=8, color='#333333')

ax.set_xlabel('Mean entropy normalised', fontsize=12)
ax.set_title('Cities ranked by mean street network entropy\n'
             'with mean terrain slope shown',
             fontsize=13)
ax.set_xlim(0, 1.05)
ax.axvline(city_df['mean_entropy'].mean(),
           color='red', linestyle='--', linewidth=1.5,
           label=f"overall mean = "
                 f"{city_df['mean_entropy'].mean():.3f}")
ax.legend(fontsize=10)

plt.tight_layout()
plt.savefig(RESULTS_DIR / "city_02_entropy_ranking.png",
            dpi=150, bbox_inches='tight')
plt.show()
print("Saved: city_02_entropy_ranking.png")

# ── plot 3: box plot per city ordered by slope ─────────────────────
print("\nPlotting per-city box plots ordered by slope...")

city_order = city_df.sort_values('mean_slope')['city_short'].tolist()

df['city_short'] = df['city'].apply(lambda x: x.split(',')[0])

fig, ax = plt.subplots(figsize=(16, 8))

sns.boxplot(
    data=df,
    x='city_short',
    y='entropy_normalised',
    order=city_order,
    palette='Blues',
    ax=ax,
    fliersize=2,
    linewidth=0.8
)

# add mean slope as secondary x-axis labels
ax.set_xticklabels(
    [f"{city}\n{city_df[city_df['city_short']==city]['mean_slope'].values[0]:.1f}°"
     if len(city_df[city_df['city_short']==city]) > 0 else city
     for city in city_order],
    rotation=45, ha='right', fontsize=8
)

ax.set_xlabel('City (ordered by mean slope, flattest to steepest)',
              fontsize=11)
ax.set_ylabel('Entropy normalised', fontsize=11)
ax.set_title('Entropy distribution per city\n'
             'ordered from flattest (left) to steepest (right) terrain',
             fontsize=13)

plt.tight_layout()
plt.savefig(RESULTS_DIR / "city_03_per_city_boxplot.png",
            dpi=150, bbox_inches='tight')
plt.show()
print("Saved: city_03_per_city_boxplot.png")

print("\nCity level analysis complete.")
print(f"Figures saved to {RESULTS_DIR}")