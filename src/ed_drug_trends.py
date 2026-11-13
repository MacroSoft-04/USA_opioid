"""
====================================================================
* Author: Minseo Kim
* Data: data/Drug_Use_Data_from_Selected_Hospitals.csv
  (CDC NCHS, National Hospital Care Survey, preliminary)
* Questions:
  1. Did opioid- and cannabis-related ED visit rates change over the period?
  2. Do they move in opposite directions (substitution)?
  3. Do large metro and rural hospitals move in opposite directions?
* Method: correlations on raw monthly rates and on month-over-month
  differences. Raw series that both trend down correlate strongly even
  when unrelated month to month, so the differenced result is the one
  that answers "do they move together". The 3-month moving average is
  used only for display; correlating smoothed series inflates r because
  neighbouring months share data.
* Output: output/trend_summary.csv, output/correlations.csv,
          output/ed_drug_trends.png
====================================================================
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "Drug_Use_Data_from_Selected_Hospitals.csv"
OUTPUT_DIR = BASE_DIR / "output"

INDICATORS = ["All Opioids", "Cannabis", "Stimulants"]
AREAS = [
    "Large Central & Fringe Metro Areas",
    "Medium & Small Metro Areas",
    "Rural Areas",
]
TOTAL = "Total"
LARGE, RURAL = AREAS[0], AREAS[2]

INDICATOR_LABELS = {
    "All Opioids": "Opioids",
    "Cannabis": "Cannabis",
    "Stimulants": "Stimulants",
}
AREA_LABELS = {
    "Large Central & Fringe Metro Areas": "Large metro",
    "Medium & Small Metro Areas": "Medium & small metro",
    "Rural Areas": "Rural",
    TOTAL: "All hospitals",
}
AREA_COLORS = {
    "Large Central & Fringe Metro Areas": "#2a5c8f",
    "Medium & Small Metro Areas": "#d08c2c",
    "Rural Areas": "#5a9e3a",
}
SMOOTH_MONTHS = 3
MONTHS_PER_YEAR = 12


def load_ed_rates() -> pd.DataFrame:
    """Monthly percent of all ED visits, one column per (indicator, subgroup)."""
    df = pd.read_csv(DATA_PATH)
    df["END_TIME"] = pd.to_datetime(df["END_TIME"], format="%m/%d/%Y")
    ed = df[
        df["SETTING"].eq("ED")
        & df["MEASURE"].eq("Percent")
        & df["INDICATOR"].isin(INDICATORS)
        & df["GROUP"].isin(["Urban-Rural", "Total"])
    ]
    return ed.pivot_table(
        index="END_TIME", columns=["INDICATOR", "SUBGROUP"], values="VALUE"
    )


def trend_summary(rates: pd.DataFrame) -> pd.DataFrame:
    """First-year vs second-year average, plus a linear slope.
    The year-over-year mean comparison avoids month-to-month noise; the
    slope p-value is optimistic because consecutive months are correlated."""
    rows = []
    months = (rates.index.year - rates.index.year[0]) * MONTHS_PER_YEAR + (
        rates.index.month - rates.index.month[0]
    )
    for indicator, subgroup in rates.columns:
        series = rates[(indicator, subgroup)]
        first, second = (
            series.iloc[:MONTHS_PER_YEAR].mean(),
            series.iloc[-MONTHS_PER_YEAR:].mean(),
        )
        fit = stats.linregress(months / MONTHS_PER_YEAR, series)
        rows.append(
            {
                "indicator": indicator,
                "subgroup": subgroup,
                "first_12m_mean_pct": round(first, 3),
                "last_12m_mean_pct": round(second, 3),
                "change_pct": round((second / first - 1) * 100, 1),
                "slope_pp_per_year": round(fit.slope, 3),
                "slope_p": round(fit.pvalue, 3),
            }
        )
    return pd.DataFrame(rows)


def correlate(a: pd.Series, b: pd.Series) -> dict:
    raw = stats.pearsonr(a, b)
    diff = stats.pearsonr(a.diff().dropna(), b.diff().dropna())
    return {
        "n_months": len(a),
        "r_raw": round(raw.statistic, 2),
        "p_raw": round(raw.pvalue, 3),
        "r_diff": round(diff.statistic, 2),
        "p_diff": round(diff.pvalue, 3),
    }


def correlation_table(rates: pd.DataFrame) -> pd.DataFrame:
    pairs = {
        "Opioids vs Cannabis (Total)": (("All Opioids", TOTAL), ("Cannabis", TOTAL)),
        "Opioids: Large metro vs Rural": (
            ("All Opioids", LARGE),
            ("All Opioids", RURAL),
        ),
        "Cannabis: Large metro vs Rural": (("Cannabis", LARGE), ("Cannabis", RURAL)),
    }
    return pd.DataFrame(
        {name: correlate(rates[a], rates[b]) for name, (a, b) in pairs.items()}
    ).T.rename_axis("comparison")


def plot(rates: pd.DataFrame) -> None:
    fig, axes = plt.subplots(
        1, len(INDICATORS), figsize=(15, 4.8), sharex=True, layout="constrained"
    )
    for ax, indicator in zip(axes, INDICATORS):
        for area in AREAS:
            series = rates[(indicator, area)]
            color = AREA_COLORS[area]
            ax.plot(series.index, series, color=color, lw=0.8, alpha=0.45)
            ax.plot(
                series.index,
                series.rolling(SMOOTH_MONTHS, center=True).mean(),
                color=color,
                lw=2.2,
                label=AREA_LABELS[area],
            )
        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_formatter(lambda v, _: f"{v:.1f}%")
        ax.set_title(
            INDICATOR_LABELS[indicator], loc="left", fontsize=12, fontweight="bold"
        )
        ax.grid(axis="y", linestyle="--", alpha=0.35)
        ax.tick_params(axis="x", rotation=45)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[0].set_ylabel("Share of all ED visits (%)")

    # Every panel starts at 0%, so the lower-left corner of the first panel is empty.
    axes[0].legend(loc="lower left", frameon=False)
    start, end = rates.index.min(), rates.index.max()
    fig.suptitle(
        f"Drug-related ED visits by hospital location, U.S. selected hospitals, {start:%b %Y}–{end:%b %Y}",
        fontsize=14,
        fontweight="bold",
    )
    fig.text(
        0.99,
        -0.01,
        f"Thin lines: monthly values | Thick lines: {SMOOTH_MONTHS}-month centered moving average (display only) | Source: CDC NCHS",
        ha="right",
        fontsize=8,
        color="#7a848d",
    )
    fig.savefig(OUTPUT_DIR / "ed_drug_trends.png", dpi=200, bbox_inches="tight")


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    rates = load_ed_rates()

    trends = trend_summary(rates)
    corr = correlation_table(rates)
    trends.to_csv(OUTPUT_DIR / "trend_summary.csv", index=False)
    corr.to_csv(OUTPUT_DIR / "correlations.csv")

    print(
        f"Period: {rates.index.min():%Y-%m} to {rates.index.max():%Y-%m} ({len(rates)} months)\n"
    )
    print(trends.to_string(index=False))
    print("\n" + corr.to_string())
    plot(rates)
