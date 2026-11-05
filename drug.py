import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('Drug_Use_Data_from_Selected_Hospitals.csv')

df['INDICATOR'] = df['INDICATOR'].fillna('').str.strip()
df['GROUP'] = df['GROUP'].fillna('').str.strip()
df['SUBGROUP'] = df['SUBGROUP'].fillna('').str.strip()
df['END_TIME']=pd.to_datetime(df['END_TIME'])

base_filter = (df['GROUP']=='Urban-Rural')&(df['SETTING']=='ED')&(df['MEASURE']=='Percent')

def get_smoothed_data(subgroup, indicator):
    data = df[base_filter & (df['SUBGROUP']==subgroup)&(df['INDICATOR']==indicator)].sort_values('END_TIME')
    data['SMOOTHED_VALUE']=data['VALUE'].rolling(window=3, min_periods=1).mean()
    return data

large_op_s = get_smoothed_data('Large Central & Fringe Metro Areas', 'All Opioids') 
rural_op_s = get_smoothed_data('Rural Areas', 'All Opioids')

large_ca_s = get_smoothed_data('Large Central & Fringe Metro Areas', 'Cannabis') 
rural_ca_s = get_smoothed_data('Rural Areas', 'Cannabis')

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12), sharex=True)

ax1.plot(large_op_s['END_TIME'], large_op_s['VALUE'], label='Large (Smoothed)', color='tab:blue', linewidth = 3)
ax1.plot(rural_op_s['END_TIME'], rural_op_s['VALUE'], label='Rural (Smoothed)', color='tab:green', linewidth = 3, linestyle='--')
ax1.set_ylabel('Opioids (3-mo Avg %)')
ax1.set_title('Smoothed Opioid Trends (Urban vs Rural)', fontsize = 14)
ax1.legend()
ax1.grid(True, alpha = 0.3)

ax2.plot(large_ca_s['END_TIME'], large_ca_s['SMOOTHED_VALUE'], label='Large (Smoothed)', color='tab:blue', linewidth = 3)
ax2.plot(rural_ca_s['END_TIME'], rural_ca_s['SMOOTHED_VALUE'], label='Rural (Smoothed)', color='tab:green', linewidth = 3, linestyle='--')
ax2.set_ylabel('Cannabis (3-mo Avg %)')
ax2.set_title('Smoothed Cannabis Trends (Urban vs Rural)', fontsize = 14)
ax2.legend()
ax2.grid(True, alpha = 0.3)

plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

def calculate_correlation(indicator):
    urban = get_smoothed_data('Large Central & Fringe Metro Areas', indicator)[['END_TIME', 'SMOOTHED_VALUE']]
    rural = get_smoothed_data('Rural Areas', indicator)[['END_TIME', 'SMOOTHED_VALUE']]

    merged = pd.merge(urban, rural, on = 'END_TIME', suffixes=('_Urban','_Rural'))

    correlation = merged['SMOOTHED_VALUE_Urban'].corr(merged['SMOOTHED_VALUE_Rural'])
    return correlation, merged

op_corr, _ = calculate_correlation('All Opioids')
ca_corr, _ = calculate_correlation('Cannabis')

print(f"-- 분석 결과: 도시 vs 시골 상관계수 --")
print(f"1. All Opioids 상관계수: {op_corr: .4f}")
print(f"2. Cannabis 상관계수: {ca_corr: .4f}")