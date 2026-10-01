"""Professional, reusable visualizations for Bài tập 3."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

NAVY = "#17365D"
BLUE = "#2F6B9A"
TEAL = "#2A9D8F"
GOLD = "#E9C46A"
ORANGE = "#F4A261"
RED = "#E76F51"
LIGHT = "#F4F7FA"
GRAY = "#667085"
PALETTE = [NAVY, BLUE, TEAL, GOLD, ORANGE, RED]
PROPERTY_LABELS = {
    "house": "Nhà ở",
    "apartment": "Căn hộ",
    "land": "Đất",
    "villa": "Biệt thự",
    "commercial": "Thương mại",
    "unknown": "Chưa phân loại",
}
SOURCE_NOTE = "Nguồn: CafeLand | TP.HCM trước sáp nhập cấp tỉnh 2025 | Giá rao bán, không phải giá giao dịch"


def _setup() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.titlesize": 15,
        "axes.titleweight": "bold",
        "axes.titlepad": 30,
        "axes.labelsize": 10.5,
        "axes.edgecolor": "#D0D5DD",
        "axes.linewidth": 0.8,
        "grid.color": "#E9EEF3",
        "grid.linewidth": 0.8,
        "xtick.color": "#475467",
        "ytick.color": "#475467",
        "text.color": "#101828",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })


def _finish(fig, path: str | Path, dpi: int = 180, tight: bool = True) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.text(0.01, 0.008, SOURCE_NOTE, fontsize=7.5, color=GRAY)
    if tight:
        fig.tight_layout(rect=(0, 0.035, 1, 0.94))
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def _subtitle(ax, text: str) -> None:
    ax.text(0, 1.01, text, transform=ax.transAxes, fontsize=9.2, color=GRAY, va="bottom", clip_on=False)


def _label_bars(ax, fmt="{:,.0f}") -> None:
    for patch in ax.patches:
        value = patch.get_width() if patch.get_width() >= patch.get_height() else patch.get_height()
        if value <= 0:
            continue
        if patch.get_width() >= patch.get_height():
            ax.text(patch.get_width(), patch.get_y() + patch.get_height()/2, "  " + fmt.format(value), va="center", fontsize=8.5, color=GRAY)
        else:
            ax.text(patch.get_x() + patch.get_width()/2, patch.get_height(), fmt.format(value), ha="center", va="bottom", fontsize=8.5, color=GRAY)


def plot_price_distribution(df: pd.DataFrame, path: str | Path, dpi: int = 180) -> str:
    _setup()
    x = df["price_billion"].dropna()
    med, p95 = x.median(), x.quantile(0.95)
    fig, ax = plt.subplots(figsize=(10, 5.8))
    sns.histplot(x=x, bins=60, kde=True, color=BLUE, alpha=0.82, ax=ax)
    ax.set_xscale("log")
    ax.axvline(med, color=TEAL, linewidth=2.0, label=f"Median {med:.1f} tỷ")
    ax.axvline(p95, color=ORANGE, linewidth=2.0, linestyle="--", label=f"P95 {p95:.1f} tỷ")
    ax.set_title("Phân bố giá rao bán: đuôi phải rất dài", loc="left")
    _subtitle(ax, "Thang log giúp quan sát rõ phần lớn thị trường; đường dọc đánh dấu median và P95")
    ax.set_xlabel("Giá rao bán (tỷ VNĐ, thang log)")
    ax.set_ylabel("Số tin đăng")
    ax.legend(frameon=False, loc="upper right")
    sns.despine(ax=ax)
    return _finish(fig, path, dpi)


def plot_area_distribution(df: pd.DataFrame, path: str | Path, dpi: int = 180) -> str:
    _setup()
    x = df["area_m2"].dropna()
    med, p95 = x.median(), x.quantile(0.95)
    fig, ax = plt.subplots(figsize=(10, 5.8))
    sns.histplot(x=x, bins=60, kde=True, color=TEAL, alpha=0.82, ax=ax)
    ax.set_xscale("log")
    ax.axvline(med, color=NAVY, linewidth=2.0, label=f"Median {med:.0f} m²")
    ax.axvline(p95, color=ORANGE, linewidth=2.0, linestyle="--", label=f"P95 {p95:.0f} m²")
    ax.set_title("Phân bố diện tích: phần lớn tập trung ở quy mô vừa và nhỏ", loc="left")
    _subtitle(ax, "Phân phối lệch phải là cơ sở dùng log-scale trong kiểm tra ngoại lai")
    ax.set_xlabel("Diện tích (m², thang log)")
    ax.set_ylabel("Số tin đăng")
    ax.legend(frameon=False, loc="upper right")
    sns.despine(ax=ax)
    return _finish(fig, path, dpi)


def plot_property_type_distribution(df: pd.DataFrame, path: str | Path, dpi: int = 180) -> str:
    _setup()
    labels = df["property_type"].map(PROPERTY_LABELS).fillna(df["property_type"])
    counts = labels.value_counts().sort_values()
    shares = counts / counts.sum() * 100
    fig, ax = plt.subplots(figsize=(10, 5.8))
    bars = ax.barh(counts.index, counts.values, color=PALETTE[:len(counts)])
    ax.set_title("Cơ cấu nguồn cung tin đăng theo loại hình BĐS", loc="left")
    _subtitle(ax, "Nhà ở riêng lẻ chiếm ưu thế; tỷ trọng được ghi trực tiếp trên từng nhóm")
    ax.set_xlabel("Số tin đăng")
    ax.set_ylabel("")
    for bar, label in zip(bars, counts.index):
        v = bar.get_width()
        ax.text(v, bar.get_y() + bar.get_height()/2, f"  {int(v):,}  ({shares[label]:.1f}%)", va="center", fontsize=9, color=GRAY)
    ax.grid(axis="y", visible=False)
    sns.despine(ax=ax, left=True)
    return _finish(fig, path, dpi)


def plot_price_per_m2_by_property_type(df: pd.DataFrame, path: str | Path, dpi: int = 180) -> str:
    _setup()
    stats = (
        df.groupby("property_type")["price_per_m2_million"]
        .agg(["count", "median"])
        .query("count >= 30")
        .sort_values("median")
    )
    subset = df[df["property_type"].isin(stats.index)].copy()
    subset["property_type_label"] = subset["property_type"].map(PROPERTY_LABELS).fillna(subset["property_type"])
    display_order = [PROPERTY_LABELS.get(x, x) for x in stats.index]
    fig, ax = plt.subplots(figsize=(10.5, 6.0))
    sns.boxplot(
        data=subset,
        x="property_type_label",
        y="price_per_m2_million",
        hue="property_type_label",
        order=display_order,
        hue_order=display_order,
        showfliers=False,
        palette=PALETTE[:len(stats)],
        legend=False,
        ax=ax,
    )
    ax.set_yscale("log")
    ax.set_title("Giá/m² khác biệt rõ giữa các loại hình", loc="left")
    _subtitle(ax, "Boxplot không hiển thị fliers để tập trung vào vùng phân bố chính; trục Y dùng log-scale")
    ax.set_xlabel("Loại hình BĐS")
    ax.set_ylabel("Giá/m² (triệu VNĐ, thang log)")
    ax.tick_params(axis="x", rotation=12)
    sns.despine(ax=ax)
    return _finish(fig, path, dpi)


def _top_areas(df: pd.DataFrame, top_n: int) -> list[str]:
    return df["legacy_area"].value_counts().head(top_n).index.tolist()


def plot_price_per_m2_by_area(df: pd.DataFrame, path: str | Path, top_n: int = 10, dpi: int = 180) -> str:
    _setup()
    areas = _top_areas(df, top_n)
    subset = df[df["legacy_area"].isin(areas)].copy()
    order = subset.groupby("legacy_area")["price_per_m2_million"].median().sort_values().index
    fig, ax = plt.subplots(figsize=(11, 6.8))
    sns.boxplot(data=subset, y="legacy_area", x="price_per_m2_million", order=order, showfliers=False, color=BLUE, width=0.55, ax=ax)
    ax.set_xscale("log")
    ax.set_title("Giá/m² phân hóa mạnh giữa các khu vực có nhiều tin đăng", loc="left")
    _subtitle(ax, f"Top {len(areas)} khu vực theo số lượng listing; boxplot loại fliers để so sánh mặt bằng giá")
    ax.set_xlabel("Giá/m² (triệu VNĐ, thang log)")
    ax.set_ylabel("")
    sns.despine(ax=ax, left=True)
    return _finish(fig, path, dpi)


def plot_price_vs_area(df: pd.DataFrame, path: str | Path, dpi: int = 180) -> str:
    _setup()
    sample = df.sample(min(len(df), 4000), random_state=42)
    rho = sample[["area_m2", "price_vnd"]].corr(method="spearman").iloc[0, 1]
    fig, ax = plt.subplots(figsize=(10, 6.3))
    hb = ax.hexbin(sample["area_m2"], sample["price_billion"], gridsize=42, mincnt=1, xscale="log", yscale="log", cmap="Blues")
    cb = fig.colorbar(hb, ax=ax, pad=0.02)
    cb.set_label("Mật độ quan sát")
    ax.set_title("Diện tích tăng thường đi cùng tổng giá cao hơn, nhưng độ phân tán lớn", loc="left")
    _subtitle(ax, f"Hexbin giảm chồng điểm; tương quan Spearman trên mẫu hiển thị: ρ = {rho:.2f}")
    ax.set_xlabel("Diện tích (m², thang log)")
    ax.set_ylabel("Giá rao bán (tỷ VNĐ, thang log)")
    sns.despine(ax=ax)
    return _finish(fig, path, dpi)


def plot_listing_count_by_area(df: pd.DataFrame, path: str | Path, top_n: int = 15, dpi: int = 180) -> str:
    _setup()
    counts = df["legacy_area"].value_counts().head(top_n).sort_values()
    fig, ax = plt.subplots(figsize=(10.5, 7.0))
    bars = ax.barh(counts.index, counts.values, color=BLUE)
    ax.set_title("Mật độ tin đăng không đồng đều giữa các khu vực", loc="left")
    _subtitle(ax, f"Top {top_n} khu vực theo số listing trong cleaned dataset")
    ax.set_xlabel("Số tin đăng")
    ax.set_ylabel("")
    for bar in bars:
        ax.text(bar.get_width(), bar.get_y()+bar.get_height()/2, f"  {int(bar.get_width()):,}", va="center", fontsize=8.8, color=GRAY)
    ax.grid(axis="y", visible=False)
    sns.despine(ax=ax, left=True)
    return _finish(fig, path, dpi)


def plot_median_price_per_m2_by_area(df: pd.DataFrame, path: str | Path, min_count: int = 30, top_n: int = 15, dpi: int = 180) -> str:
    _setup()
    grouped = df.groupby("legacy_area").agg(median_price_m2=("price_per_m2_million", "median"), count=("listing_id", "count"))
    grouped = grouped[grouped["count"] >= min_count].nlargest(top_n, "median_price_m2").sort_values("median_price_m2")
    fig, ax = plt.subplots(figsize=(10.5, 7.0))
    bars = ax.barh(grouped.index, grouped["median_price_m2"], color=TEAL)
    ax.set_title("Khu vực trung tâm có mặt bằng giá/m² nổi bật", loc="left")
    _subtitle(ax, f"Chỉ hiển thị khu vực có ít nhất {min_count} tin để giảm nhiễu do nhóm quá nhỏ")
    ax.set_xlabel("Trung vị giá/m² (triệu VNĐ)")
    ax.set_ylabel("")
    for bar in bars:
        ax.text(bar.get_width(), bar.get_y()+bar.get_height()/2, f"  {bar.get_width():.1f}", va="center", fontsize=8.8, color=GRAY)
    ax.grid(axis="y", visible=False)
    sns.despine(ax=ax, left=True)
    return _finish(fig, path, dpi)


def plot_correlation_heatmap(df: pd.DataFrame, path: str | Path, dpi: int = 180) -> str:
    _setup()
    columns = ["price_billion", "area_m2", "price_per_m2_million", "log_price_vnd", "log_area_m2", "log_price_per_m2"]
    corr = df[columns].corr(method="spearman")
    labels = ["Giá (tỷ)", "Diện tích", "Giá/m²", "log(Giá)", "log(DT)", "log(Giá/m²)"]
    fig, ax = plt.subplots(figsize=(8.5, 7.2))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", center=0, vmin=-1, vmax=1, square=True, linewidths=0.8, linecolor="white", cbar_kws={"shrink": 0.8, "label": "Spearman ρ"}, ax=ax)
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_yticklabels(labels, rotation=0)
    ax.set_title("Ma trận tương quan Spearman", loc="left")
    _subtitle(ax, "Dùng Spearman để giảm ảnh hưởng của phân phối lệch và ngoại lệ")
    return _finish(fig, path, dpi)


def plot_cleaning_summary(audit: pd.DataFrame, path: str | Path, dpi: int = 180) -> str:
    _setup()
    values = pd.Series({
        "URL hồ sơ môi giới": int(audit["is_non_listing_url"].sum()),
        "Cờ outlier giá": int(audit["outlier_price_log"].sum()),
        "Cờ outlier diện tích": int(audit["outlier_area_log"].sum()),
        "Cờ outlier giá/m²": int(audit["outlier_price_per_m2_log"].sum()),
        "Robust outlier bị loại": int(((~audit["is_non_listing_url"]) & audit["is_robust_outlier"]).sum()),
    }).sort_values()
    fig, ax = plt.subplots(figsize=(10, 5.8))
    colors = [BLUE if x != "Robust outlier bị loại" else RED for x in values.index]
    bars = ax.barh(values.index, values.values, color=colors)
    ax.set_title("Tóm tắt quyết định làm sạch dữ liệu", loc="left")
    _subtitle(ax, "Robust outlier chỉ bị loại khi nhận ít nhất 2/3 cờ trên log-scale")
    ax.set_xlabel("Số dòng")
    ax.set_ylabel("")
    for bar in bars:
        ax.text(bar.get_width(), bar.get_y()+bar.get_height()/2, f"  {int(bar.get_width()):,}", va="center", fontsize=9, color=GRAY)
    ax.grid(axis="y", visible=False)
    sns.despine(ax=ax, left=True)
    return _finish(fig, path, dpi)


def plot_interactive_treemap(df: pd.DataFrame, path: str | Path) -> str:
    import plotly.express as px

    grouped = df.groupby(["legacy_area", "property_type"], as_index=False).agg(
        listings=("listing_id", "count"),
        median_price_m2=("price_per_m2_million", "median"),
    )
    grouped["property_type_label"] = grouped["property_type"].map(PROPERTY_LABELS).fillna(grouped["property_type"])
    fig = px.treemap(
        grouped,
        path=[px.Constant("TP.HCM cũ"), "legacy_area", "property_type_label"],
        values="listings",
        color="median_price_m2",
        color_continuous_scale="Blues",
        title="Cấu trúc thị trường: quy mô tin đăng và mặt bằng giá/m²",
        labels={"median_price_m2": "Median giá/m² (triệu VNĐ)", "listings": "Số tin"},
    )
    fig.update_layout(
        template="plotly_white",
        margin=dict(t=65, l=15, r=15, b=15),
        font=dict(family="Arial", size=13),
        coloraxis_colorbar=dict(title="Triệu VNĐ/m²"),
    )
    fig.update_traces(hovertemplate="<b>%{label}</b><br>Số tin: %{value}<br>Median giá/m²: %{color:.1f} triệu<extra></extra>")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(path, include_plotlyjs="cdn")
    return str(path)


def plot_executive_dashboard(
    df: pd.DataFrame,
    audit: pd.DataFrame,
    path: str | Path,
    dpi: int = 180,
) -> str:
    _setup()
    from matplotlib.patches import FancyBboxPatch

    rows = len(df)
    median_price = float(df["price_billion"].median())
    median_area = float(df["area_m2"].median())
    unknown_share = float(df["property_type"].eq("unknown").mean() * 100)
    top_areas = df["legacy_area"].value_counts().head(7).sort_values()
    type_counts = df["property_type"].map(PROPERTY_LABELS).fillna(df["property_type"]).value_counts()

    fig = plt.figure(figsize=(13.5, 8.2), facecolor="white")
    gs = fig.add_gridspec(2, 4, height_ratios=[0.9, 2.3], hspace=0.42, wspace=0.35)
    cards = [
        ("Listing sau làm sạch", f"{rows:,}", "bản ghi hợp lệ"),
        ("Giá trung vị", f"{median_price:.1f} tỷ", "VNĐ / listing"),
        ("Diện tích trung vị", f"{median_area:.0f} m²", "quy mô điển hình"),
        ("Chưa phân loại", f"{unknown_share:.1f}%", "sau tái phân loại"),
    ]
    for i, (label, value, note) in enumerate(cards):
        ax = fig.add_subplot(gs[0, i])
        ax.axis("off")
        card = FancyBboxPatch(
            (0.02, 0.05), 0.96, 0.88,
            boxstyle="round,pad=0.018,rounding_size=0.04",
            transform=ax.transAxes,
            facecolor=LIGHT,
            edgecolor="#D0D5DD",
            linewidth=1.0,
        )
        ax.add_patch(card)
        ax.text(0.08, 0.72, label, transform=ax.transAxes, fontsize=10, color=GRAY, weight="bold")
        ax.text(0.08, 0.38, value, transform=ax.transAxes, fontsize=22, color=NAVY, weight="bold")
        ax.text(0.08, 0.16, note, transform=ax.transAxes, fontsize=8.5, color=GRAY)

    ax1 = fig.add_subplot(gs[1, :2])
    bars = ax1.barh(top_areas.index, top_areas.values, color=BLUE)
    ax1.set_title("Khu vực có nhiều tin đăng nhất", loc="left", fontsize=12, weight="bold")
    ax1.set_xlabel("Số listing")
    ax1.set_ylabel("")
    for bar in bars:
        ax1.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f"  {int(bar.get_width()):,}", va="center", fontsize=8.5, color=GRAY)
    ax1.grid(axis="y", visible=False)
    sns.despine(ax=ax1, left=True)

    ax2 = fig.add_subplot(gs[1, 2:])
    colors = PALETTE[:len(type_counts)]
    wedges, _ = ax2.pie(
        type_counts.values,
        startangle=90,
        colors=colors,
        wedgeprops=dict(width=0.42, edgecolor="white"),
    )
    ax2.text(0, 0.08, "Cơ cấu", ha="center", va="center", fontsize=11, color=GRAY)
    ax2.text(0, -0.10, "loại hình", ha="center", va="center", fontsize=11, color=NAVY, weight="bold")
    labels = [f"{k}: {v/type_counts.sum()*100:.1f}%" for k, v in type_counts.items()]
    ax2.legend(wedges, labels, frameon=False, fontsize=8.5, loc="center left", bbox_to_anchor=(1.0, 0.5))
    ax2.set_title("Cơ cấu loại hình BĐS", loc="left", fontsize=12, weight="bold")

    fig.suptitle("EDA Snapshot — Thị trường BĐS TP.HCM", x=0.04, y=0.98, ha="left", fontsize=19, weight="bold", color=NAVY)
    fig.text(0.04, 0.935, "Tổng quan nhanh về quy mô dữ liệu, mức giá, diện tích và cấu trúc listing sau làm sạch", fontsize=10, color=GRAY)
    fig.subplots_adjust(left=0.06, right=0.91, top=0.88, bottom=0.08)
    return _finish(fig, path, dpi, tight=False)


def plot_missingness_profile(df: pd.DataFrame, path: str | Path, dpi: int = 180) -> str:
    _setup()
    rates = (df.isna().mean() * 100).sort_values()
    rates = rates[rates > 0]
    fig, ax = plt.subplots(figsize=(10, 5.8))
    if rates.empty:
        ax.text(0.5, 0.5, "Không có missing value trong cleaned dataset", ha="center", va="center", transform=ax.transAxes, fontsize=13)
        ax.axis("off")
    else:
        colors = [RED if v >= 50 else ORANGE if v >= 10 else BLUE for v in rates.values]
        bars = ax.barh(rates.index, rates.values, color=colors)
        ax.set_xlim(0, 105)
        ax.set_xlabel("Tỷ lệ thiếu (%)")
        ax.set_ylabel("")
        for bar in bars:
            ax.text(bar.get_width(), bar.get_y()+bar.get_height()/2, f"  {bar.get_width():.1f}%", va="center", fontsize=9, color=GRAY)
        ax.grid(axis="y", visible=False)
        sns.despine(ax=ax, left=True)
    ax.set_title("Hồ sơ missing: thiếu dữ liệu chủ yếu mang tính cấu trúc", loc="left")
    _subtitle(ax, "Các trường thiếu cao không được impute máy móc; chính sách xử lý được ghi trong missing_policy")
    return _finish(fig, path, dpi)


def plot_market_positioning(
    df: pd.DataFrame,
    path: str | Path,
    min_count: int = 30,
    dpi: int = 180,
) -> str:
    _setup()
    grouped = df.groupby("legacy_area").agg(
        listings=("listing_id", "count"),
        median_price_m2=("price_per_m2_million", "median"),
    )
    grouped = grouped[grouped["listings"] >= min_count].dropna()
    x_mid = float(grouped["listings"].median())
    y_mid = float(grouped["median_price_m2"].median())

    fig, ax = plt.subplots(figsize=(10.5, 6.8))
    ax.scatter(grouped["listings"], grouped["median_price_m2"], s=110, color=TEAL, alpha=0.82, edgecolor="white", linewidth=0.8)
    ax.axvline(x_mid, color="#98A2B3", linestyle="--", linewidth=1.2)
    ax.axhline(y_mid, color="#98A2B3", linestyle="--", linewidth=1.2)
    ax.set_xscale("log")
    ax.set_yscale("log")

    label_idx = set(grouped.nlargest(6, "listings").index) | set(grouped.nlargest(4, "median_price_m2").index)
    for name in label_idx:
        row = grouped.loc[name]
        ax.annotate(name, (row["listings"], row["median_price_m2"]), xytext=(5, 5), textcoords="offset points", fontsize=8.2, color="#344054")

    ax.text(0.02, 0.96, "Giá cao • Ít tin", transform=ax.transAxes, fontsize=8, color=GRAY, va="top")
    ax.text(0.98, 0.96, "Giá cao • Nhiều tin", transform=ax.transAxes, fontsize=8, color=NAVY, va="top", ha="right", weight="bold")
    ax.text(0.02, 0.04, "Giá thấp • Ít tin", transform=ax.transAxes, fontsize=8, color=GRAY, va="bottom")
    ax.text(0.98, 0.04, "Giá thấp • Nhiều tin", transform=ax.transAxes, fontsize=8, color=GRAY, va="bottom", ha="right")
    ax.set_title("Bản đồ định vị thị trường theo khu vực", loc="left")
    _subtitle(ax, f"So sánh quy mô nguồn cung và median giá/m²; chỉ giữ khu vực có ≥ {min_count} tin")
    ax.set_xlabel("Số listing (thang log)")
    ax.set_ylabel("Median giá/m² (triệu VNĐ, thang log)")
    sns.despine(ax=ax)
    return _finish(fig, path, dpi)


def plot_interactive_price_area(df: pd.DataFrame, path: str | Path) -> str:
    import plotly.express as px

    plot_df = df.copy()
    plot_df["property_type_label"] = plot_df["property_type"].map(PROPERTY_LABELS).fillna(plot_df["property_type"])
    hover = ["legacy_area", "price_per_m2_million"]
    fig = px.scatter(
        plot_df,
        x="area_m2",
        y="price_billion",
        color="property_type_label",
        hover_name="title" if "title" in df.columns else None,
        hover_data=hover,
        log_x=True,
        log_y=True,
        opacity=0.58,
        color_discrete_sequence=PALETTE,
        title="Tương tác: diện tích và giá theo loại hình BĐS",
        labels={
            "area_m2": "Diện tích (m², log)",
            "price_billion": "Giá rao bán (tỷ VNĐ, log)",
            "property_type_label": "Loại hình",
            "legacy_area": "Khu vực",
            "price_per_m2_million": "Giá/m² (triệu VNĐ)",
        },
    )
    fig.update_traces(marker=dict(size=7, line=dict(width=0.3, color="white")))
    fig.update_layout(template="plotly_white", margin=dict(t=70, l=40, r=30, b=45), font=dict(family="Arial", size=12), legend_title_text="Loại hình")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(path, include_plotlyjs="cdn")
    return str(path)


def generate_eda_figures(cleaned: pd.DataFrame, audit: pd.DataFrame, output_dir: str | Path, top_n_areas: int = 15, min_area_group_count: int = 30, dpi: int = 180) -> dict[str, str]:
    """Generate a consistent, report-ready BT3 figure set."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {}
    paths["executive_dashboard"] = plot_executive_dashboard(cleaned, audit, out / "00_executive_dashboard.png", dpi)
    paths["price_distribution"] = plot_price_distribution(cleaned, out / "01_price_distribution.png", dpi)
    paths["area_distribution"] = plot_area_distribution(cleaned, out / "02_area_distribution.png", dpi)
    paths["property_type_distribution"] = plot_property_type_distribution(cleaned, out / "03_property_type_distribution.png", dpi)
    paths["price_m2_by_property_type"] = plot_price_per_m2_by_property_type(cleaned, out / "04_price_m2_by_property_type.png", dpi)
    paths["price_m2_by_area"] = plot_price_per_m2_by_area(cleaned, out / "05_price_m2_by_area.png", min(10, top_n_areas), dpi)
    paths["price_vs_area"] = plot_price_vs_area(cleaned, out / "06_price_vs_area.png", dpi)
    paths["listing_count_by_area"] = plot_listing_count_by_area(cleaned, out / "07_listing_count_by_area.png", top_n_areas, dpi)
    paths["median_price_m2_by_area"] = plot_median_price_per_m2_by_area(
        cleaned, out / "08_median_price_m2_by_area.png", min_area_group_count, top_n_areas, dpi
    )
    paths["correlation_heatmap"] = plot_correlation_heatmap(cleaned, out / "09_correlation_heatmap.png", dpi)
    paths["cleaning_summary"] = plot_cleaning_summary(audit, out / "10_cleaning_summary.png", dpi)
    paths["missingness_profile"] = plot_missingness_profile(cleaned, out / "11_missingness_profile.png", dpi)
    paths["market_positioning"] = plot_market_positioning(cleaned, out / "12_market_positioning.png", min_area_group_count, dpi)
    paths["interactive_treemap"] = plot_interactive_treemap(cleaned, out / "13_market_treemap.html")
    paths["interactive_price_area"] = plot_interactive_price_area(cleaned, out / "14_price_area_interactive.html")
    return paths
