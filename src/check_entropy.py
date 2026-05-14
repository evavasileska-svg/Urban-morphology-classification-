import pandas as pd

df = pd.read_csv('data/processed/entropy_features.csv')

print('Columns present:')
for col in df.columns:
    print(f'  {col}')

print()
print('orientation_order_phi stats:')
print(df['orientation_order_phi'].describe())

print()
print('entropy_weighted_norm stats:')
print(df['entropy_weighted_norm'].describe())

print()
# Boeing found Ho and Hw strongly correlated r > 0.99
corr = df['entropy_normalised'].corr(df['entropy_weighted_norm'])
print(f'Correlation Ho vs Hw: {corr:.4f}')
print('Boeing found r > 0.99 — if yours is similar the method is correct')

print()
print('phi range check:')
print(f'  min phi:  {df["orientation_order_phi"].min():.4f}')
print(f'  max phi:  {df["orientation_order_phi"].max():.4f}')
print(f'  mean phi: {df["orientation_order_phi"].mean():.4f}')
print('Boeing found European cities average phi around 0.033')

print()
print('Sample of 5 rows:')
print(df[['city', 'entropy_normalised', 
          'entropy_weighted_norm',
          'orientation_order_phi']].head())