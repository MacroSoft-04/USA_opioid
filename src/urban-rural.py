import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SRC_DIR
DATA_DIR = PROJECT_ROOT / "data"

df = pd.read_csv(DATA_DIR / "Drug_Use_Data_from_Selected_Hospitals.csv")

urban_rural_data = df[df["GROUP"] == "Urban-Rural"]

print("--Urban-Rural 그룹의 세부 분류(SUBGROUP)목록--")
print(urban_rural_data["SUBGROUP"].unique())
