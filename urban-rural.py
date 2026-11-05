import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('Drug_Use_Data_from_Selected_Hospitals.csv')

urban_rural_data = df[df['GROUP']=='Urban-Rural']

print("--Urban-Rural 그룹의 세부 분류(SUBGROUP)목록--")
print(urban_rural_data['SUBGROUP'].unique())