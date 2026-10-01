"""Bài tập 3 EDA pipeline orchestration."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from dap_project.data.eda_cleaning import prepare_eda_dataset
from dap_project.data.organize import save_multiformat
from dap_project.features.build_features import (
    add_preliminary_model_features,
    feature_availability,
    select_model_v1_features,
)
from dap_project.visualization.plots import generate_eda_figures


def load_config(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def find_latest_processed(project_root: str | Path) -> Path:
    root = Path(project_root)
    files = sorted((root / "data/processed").glob("hcm_realestate_*.csv"))
    files = [p for p in files if "cleaned" not in p.stem]
    if not files:
        raise FileNotFoundError("Chưa có production processed dataset.")
    return files[-1]


def _area_stats(df: pd.DataFrame, min_count: int) -> pd.DataFrame:
    grouped = (
        df.groupby("legacy_area", dropna=False)
        .agg(
            count=("listing_id", "count"),
            median_price_m2=("price_per_m2_million", "median"),
        )
        .dropna(subset=["median_price_m2"])
    )
    eligible = grouped[grouped["count"] >= min_count]
    return eligible.sort_values("median_price_m2")


def _safe_extremes(frame: pd.DataFrame) -> tuple[str, float, str, float]:
    if frame.empty:
        return "N/A", float("nan"), "N/A", float("nan")
    low_name = str(frame.index[0])
    high_name = str(frame.index[-1])
    low_value = float(frame.iloc[0]["median_price_m2"])
    high_value = float(frame.iloc[-1]["median_price_m2"])
    return low_name, low_value, high_name, high_value


def build_insights(
    cleaned: pd.DataFrame,
    diagnostics: dict[str, Any],
    min_area_count: int,
) -> list[str]:
    p50 = float(cleaned["price_billion"].median())
    p95 = float(cleaned["price_billion"].quantile(0.95))
    a50 = float(cleaned["area_m2"].median())
    a95 = float(cleaned["area_m2"].quantile(0.95))

    type_counts = cleaned["property_type"].value_counts()
    dominant_type = str(type_counts.index[0])
    dominant_share = float(type_counts.iloc[0] / len(cleaned) * 100)
    unknown_rate = float(cleaned["property_type"].eq("unknown").mean() * 100)

    area_stats = _area_stats(cleaned, min_area_count)
    low_area, low_ppm2, high_area, high_ppm2 = _safe_extremes(area_stats)

    rho = float(
        cleaned[["area_m2", "price_vnd"]]
        .corr(method="spearman")
        .iloc[0, 1]
    )
    risk = cleaned.get(
        "area_definition_risk",
        pd.Series(False, index=cleaned.index),
    )
    risk_rate = float(risk.fillna(False).astype(bool).mean() * 100)

    return [
        (
            f"Sau kiểm soát chất lượng còn {len(cleaned):,} listing; "
            f"loại {diagnostics['structural_non_listing_rows']:,} URL hồ sơ môi giới "
            f"và {diagnostics['robust_outlier_rows_removed']:,} ngoại lai mạnh."
        ),
        (
            f"Giá rao bán lệch phải: trung vị {p50:.2f} tỷ VNĐ, "
            f"phân vị 95% {p95:.2f} tỷ. Phân tích log giúp hạn chế vài "
            "listing giá rất cao lấn át phần lớn thị trường."
        ),
        (
            f"Diện tích cũng có đuôi dài: trung vị {a50:.1f} m², "
            f"phân vị 95% {a95:.1f} m². Vì vậy ngoại lai được đánh dấu "
            "trên log-scale thay vì cắt bằng một ngưỡng tuyệt đối."
        ),
        (
            f"{dominant_type} là loại hình lớn nhất ({dominant_share:.1f}%). "
            f"Sau tái phân loại bằng title/URL, unknown còn {unknown_rate:.1f}%."
        ),
        (
            f"Trong khu vực có ít nhất {min_area_count} tin, {high_area} có "
            f"trung vị giá/m² cao nhất ({high_ppm2:.1f} triệu), còn {low_area} "
            f"thấp nhất ({low_ppm2:.1f} triệu). Đây là mô tả giá rao bán, "
            "không phải kết luận nhân quả."
        ),
        (
            f"Tương quan Spearman giữa diện tích và tổng giá là {rho:.2f}; "
            "diện tích có thông tin dự báo nhưng không đủ để giải thích toàn bộ giá."
        ),
        (
            f"{risk_rate:.1f}% bản ghi cleaned mang cờ area_definition_risk. "
            "Bước modeling cần theo dõi riêng vì area_m2 ở nhà phố đôi khi "
            "có thể phản ánh diện tích sàn thay vì diện tích đất."
        ),
    ]


def build_chart_notes(
    cleaned: pd.DataFrame,
    diagnostics: dict[str, Any],
    min_area_count: int,
) -> dict[str, str]:
    p50 = float(cleaned["price_billion"].median())
    p95 = float(cleaned["price_billion"].quantile(0.95))
    a50 = float(cleaned["area_m2"].median())
    a95 = float(cleaned["area_m2"].quantile(0.95))
    rho = float(
        cleaned[["area_m2", "price_vnd"]]
        .corr(method="spearman")
        .iloc[0, 1]
    )

    type_stats = (
        cleaned.groupby("property_type")["price_per_m2_million"]
        .agg(["count", "median"])
        .query("count >= 30")
        .sort_values("median")
    )
    low_type = str(type_stats.index[0])
    high_type = str(type_stats.index[-1])
    low_type_value = float(type_stats.iloc[0]["median"])
    high_type_value = float(type_stats.iloc[-1]["median"])

    areas = _area_stats(cleaned, min_area_count)
    low_area, low_area_value, high_area, high_area_value = _safe_extremes(areas)

    area_counts = cleaned["legacy_area"].value_counts()
    top_area = str(area_counts.index[0])
    top_area_count = int(area_counts.iloc[0])
    top_area_share = top_area_count / len(cleaned) * 100

    type_counts = cleaned["property_type"].value_counts()
    top_type = str(type_counts.index[0])
    top_type_share = float(type_counts.iloc[0] / len(cleaned) * 100)
    unknown_share = float(cleaned["property_type"].eq("unknown").mean() * 100)
    missing_rates = (cleaned.isna().mean() * 100).sort_values(ascending=False)
    missing_rates = missing_rates[missing_rates > 0]
    top_missing = str(missing_rates.index[0]) if not missing_rates.empty else "none"
    top_missing_rate = float(missing_rates.iloc[0]) if not missing_rates.empty else 0.0

    return {
        "executive_dashboard": (
            f"Dashboard tóm tắt {len(cleaned):,} listing sau làm sạch, với median giá {p50:.2f} tỷ VNĐ "
            f"và median diện tích {a50:.1f} m². Cơ cấu loại hình và phân bố nguồn cung theo khu vực "
            "được đặt cùng KPI để người xem nắm bức tranh thị trường trước khi đi vào từng phân tích chi tiết."
        ),
        "price_distribution": (
            f"Giá rao bán lệch phải: trung vị {p50:.2f} tỷ VNĐ nhưng "
            f"phân vị 95% {p95:.2f} tỷ. Thang log giúp nhìn rõ phần lớn "
            "thị trường thay vì bị chi phối bởi vài listing rất đắt."
        ),
        "area_distribution": (
            f"Diện tích có trung vị {a50:.1f} m² và phân vị 95% {a95:.1f} m². "
            "Phân phối đuôi dài ủng hộ xử lý ngoại lai trên log-scale."
        ),
        "property_type_distribution": (
            f"{top_type} chiếm {top_type_share:.1f}% dữ liệu cleaned; "
            f"unknown còn {unknown_share:.1f}%. Nhãn chưa chắc chắn được giữ "
            "unknown thay vì gán đoán."
        ),
        "price_m2_by_property_type": (
            f"Trong nhóm có ít nhất 30 tin, trung vị giá/m² từ "
            f"{low_type_value:.1f} triệu ({low_type}) đến "
            f"{high_type_value:.1f} triệu ({high_type}). "
            "property_type vì vậy là feature có cơ sở EDA."
        ),
        "price_m2_by_area": (
            f"Giá/m² phân hóa theo vị trí: {high_area} đạt trung vị "
            f"{high_area_value:.1f} triệu/m² so với {low_area_value:.1f} "
            f"triệu/m² ở {low_area} trong nhóm đủ mẫu. "
            "Chênh lệch này cho thấy legacy_area là đặc trưng quan trọng cần giữ cho BT4."
        ),
        "price_vs_area": (
            f"Spearman(area, price) = {rho:.2f}. Quan hệ dương nhưng phân tán, "
            "nên model cần kết hợp vị trí và loại hình thay vì chỉ diện tích."
        ),
        "listing_count_by_area": (
            f"{top_area} có {top_area_count:,} tin ({top_area_share:.1f}% cleaned). "
            "Mật độ mẫu không đều, vì vậy BT4 nên kiểm tra sai số theo khu vực."
        ),
        "median_price_m2_by_area": (
            f"Trong khu vực có ít nhất {min_area_count} tin, {high_area} đứng cao "
            f"nhất và {low_area} thấp nhất về trung vị giá/m². "
            "price_per_m2 chỉ dùng EDA vì được suy ra từ target."
        ),
        "correlation_heatmap": (
            f"Heatmap dùng Spearman do các biến lệch; area_m2 và price_vnd "
            f"có hệ số {rho:.2f}. Các biến target-derived không đi vào model v1."
        ),
        "cleaning_summary": (
            f"Pipeline loại {diagnostics['structural_non_listing_rows']:,} URL "
            f"không phải listing và {diagnostics['robust_outlier_rows_removed']:,} "
            "dòng có ít nhất hai phiếu ngoại lai robust. "
            "Quy tắc nhiều cờ giúp bảo thủ hơn so với xóa theo một ngưỡng duy nhất."
        ),
        "missingness_profile": (
            f"Trường thiếu nhiều nhất là {top_missing} ({top_missing_rate:.1f}%). "
            "Các trường thiếu cao chủ yếu phản ánh giới hạn của card-only crawl, vì vậy không được impute máy móc; "
            "việc giữ missing giúp tránh tạo tín hiệu giả trước bước modeling."
        ),
        "market_positioning": (
            f"Biểu đồ đặt quy mô nguồn cung cạnh mặt bằng giá/m² để nhận diện các khu vực có vai trò thị trường khác nhau. "
            f"{top_area} nổi bật về số lượng tin, trong khi {high_area} nổi bật về median giá/m²; "
            "điều này củng cố nhu cầu đưa yếu tố vị trí vào mô hình."
        ),
        "interactive_treemap": (
            "Treemap tương tác kết hợp quy mô tin đăng với trung vị giá/m² theo "
            "khu vực → loại hình, phục vụ storytelling và drill-down. "
            "Người xem có thể nhận diện nhanh nơi vừa có nhiều tin vừa có mặt bằng giá cao."
        ),
        "interactive_price_area": (
            f"Scatter Plotly cho phép hover từng listing và lọc trực quan theo loại hình; "
            f"quan hệ diện tích–giá có Spearman khoảng {rho:.2f} nhưng vẫn phân tán mạnh. "
            "Tính tương tác giúp kiểm tra các cụm và điểm bất thường tốt hơn biểu đồ tĩnh."
        ),
    }


def _to_markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_Không có dữ liệu._"
    display = frame.copy()
    headers = [str(c) for c in display.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in display.astype(str).itertuples(index=False, name=None):
        values = [str(v).replace("|", "\\|") for v in row]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_eda_report(
    path: str | Path,
    source: Path,
    diagnostics: dict[str, Any],
    missing_policy: pd.DataFrame,
    availability: pd.DataFrame,
    selected: dict[str, list[str]],
    figures: dict[str, str],
    insights: list[str],
    chart_notes: dict[str, str],
    gate_passed: bool,
) -> str:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# BÀI TẬP 3 — EDA & TRỰC QUAN HÓA DỮ LIỆU",
        "",
        f"Input production: {source.as_posix()}",
        f"GATE BT3: {'PASS' if gate_passed else 'FAIL'}",
        "",
        "## 1. Phạm vi và nguyên tắc",
        "",
        "- BQ01: dự đoán price_vnd cho BĐS bán tại TP.HCM cũ.",
        "- Raw không bị sửa; BT3 bắt đầu từ processed production của BT2.",
        "- price_per_m2 chỉ dùng cho EDA và không dùng làm feature model v1.",
        "- Không impute các trường thiếu cấu trúc chỉ để làm dataset đầy hơn.",
        "",
        "## 2. Xử lý thiếu và ngoại lai",
        "",
        f"- Input: {diagnostics['input_rows']:,} dòng.",
        f"- URL hồ sơ môi giới bị loại: {diagnostics['structural_non_listing_rows']:,}.",
        f"- Property type được tái phân loại: {diagnostics['property_type_refined_rows']:,}.",
        f"- Ngoại lai robust bị loại: {diagnostics['robust_outlier_rows_removed']:,}.",
        f"- Cleaned: {diagnostics['cleaned_rows']:,} dòng ({diagnostics['retained_pct']:.2f}% input).",
        "",
        "### Phương pháp ngoại lai",
        "",
        "Giá, diện tích và giá/m² được xét trên log-scale theo từng property_type. "
        "Một dòng chỉ bị loại khi nhận ít nhất 2/3 cờ IQR robust; nhóm quá nhỏ "
        "dùng ngưỡng toàn cục. Cách này tránh xóa listing chỉ vì một biến đơn lẻ.",
        "",
        "### Chính sách missing",
        "",
        _to_markdown_table(missing_policy),
        "",
        "## 3. Feature availability",
        "",
        _to_markdown_table(availability),
        "",
        "### Model v1 candidate không leakage",
        "",
        f"- Numeric: {', '.join(selected['numeric']) or '(none)'}",
        f"- Categorical: {', '.join(selected['categorical']) or '(none)'}",
        "- Hai nhóm mô hình dự kiến BT4: Linear/Ridge và Tree-based regression.",
        "",
        "## 4. Bộ trực quan hóa",
        "",
    ]
    for key, figure_path in figures.items():
        figure_abs = Path(figure_path).resolve()
        relative = Path(
            os.path.relpath(figure_abs, report_path.parent.resolve())
        ).as_posix()
        lines.extend([
            f"### {key}",
            "",
            f"- Output: `{relative}`",
            f"- Insight: {chart_notes.get(key, '')}",
            "",
        ])
        if figure_abs.suffix.lower() == ".png":
            lines.extend([f"![{key}]({relative})", ""])
        elif figure_abs.suffix.lower() == ".html":
            lines.extend([f"[Mở biểu đồ Plotly tương tác]({relative})", ""])

    lines.extend(["## 5. Bảy insight chính", ""])
    for index, insight in enumerate(insights, start=1):
        lines.append(f"{index}. {insight}")

    lines.extend([
        "",
        "## 6. Kết nối sang Feature Engineering và BT4",
        "",
        "- Giữ area_m2, log_area_m2, property_type, legacy_area.",
        "- Theo dõi area_definition_risk khi đánh giá sai số.",
        "- Không dùng title, description, listing_id, url hoặc biến suy ra từ target.",
        "- Trường detail sparse chỉ đưa vào nếu availability đủ sau enrichment.",
        "- BT4 phải fit mọi ngưỡng preprocessing học từ dữ liệu chỉ trên train; cleaned BT3 là analytical snapshot, không thay thế sklearn Pipeline.",
        "",
        "## 7. Peer review",
        "",
        "Biên bản peer review lưu tại docs/peer_review.md và phải ghi rõ điều chỉnh trước khi nộp.",
    ])
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(report_path)


def run_eda(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root)
    cfg = load_config(root / "config.yaml")
    eda_cfg = cfg.get("eda", {})

    source = find_latest_processed(root)
    source_df = pd.read_csv(source)

    cleaned, audit, diagnostics, missing_policy = prepare_eda_dataset(
        source_df,
        config=eda_cfg,
    )
    cleaned = add_preliminary_model_features(cleaned)

    availability = feature_availability(cleaned)
    selected = select_model_v1_features(
        cleaned,
        min_non_null_rate=float(eda_cfg.get("feature_min_non_null_rate", 0.70)),
    )

    tag = source.stem.removeprefix("hcm_realestate_")
    cleaned_paths = save_multiformat(
        cleaned,
        root / "data/processed" / f"hcm_realestate_cleaned_{tag}",
    )
    audit_path = root / "data/interim" / f"eda_audit_{tag}.csv"
    audit.to_csv(audit_path, index=False, encoding="utf-8-sig")

    report_data_dir = root / "reports" / "eda"
    report_data_dir.mkdir(parents=True, exist_ok=True)
    missing_path = report_data_dir / f"missing_policy_{tag}.csv"
    availability_path = report_data_dir / f"feature_availability_{tag}.csv"
    missing_policy.to_csv(missing_path, index=False, encoding="utf-8-sig")
    availability.to_csv(availability_path, index=False, encoding="utf-8-sig")

    figures = generate_eda_figures(
        cleaned,
        audit,
        root / "reports" / "figures",
        top_n_areas=int(eda_cfg.get("top_n_areas", 15)),
        min_area_group_count=int(eda_cfg.get("min_area_group_count", 30)),
        dpi=int(eda_cfg.get("figure_dpi", 200)),
    )

    min_area_count = int(eda_cfg.get("min_area_group_count", 30))
    insights = build_insights(cleaned, diagnostics, min_area_count)
    chart_notes = build_chart_notes(cleaned, diagnostics, min_area_count)

    static_count = sum(p.lower().endswith(".png") for p in figures.values())
    interactive_count = sum(p.lower().endswith(".html") for p in figures.values())
    minimum_rows = int(
        eda_cfg.get(
            "minimum_cleaned_records",
            cfg.get("acquisition", {}).get("minimum_valid_records", 5000),
        )
    )
    gate_passed = (
        len(cleaned) >= minimum_rows
        and static_count >= 8
        and len(insights) >= 5
        and interactive_count >= 1
    )

    report_path = write_eda_report(
        root / "docs" / "BT3_submission.md",
        source,
        diagnostics,
        missing_policy,
        availability,
        selected,
        figures,
        insights,
        chart_notes,
        gate_passed,
    )

    summary = {
        "source": str(source),
        "cleaned_paths": cleaned_paths,
        "audit_path": str(audit_path),
        "missing_policy_path": str(missing_path),
        "feature_availability_path": str(availability_path),
        "report_path": report_path,
        "figures": figures,
        "diagnostics": diagnostics,
        "model_v1_features": selected,
        "insights": insights,
        "static_chart_count": static_count,
        "interactive_chart_count": interactive_count,
        "gate_passed": gate_passed,
    }
    summary_path = report_data_dir / f"eda_summary_{tag}.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary["summary_path"] = str(summary_path)
    return summary
