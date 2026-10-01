"""Feature engineering and leakage policy for BQ01 price prediction."""

from __future__ import annotations

import numpy as np
import pandas as pd

TARGET_COLUMN = "price_vnd"

LEAKAGE_COLUMNS = {
    TARGET_COLUMN,
    "price_text",
    "displayed_price_per_m2",
    "price_per_m2_vnd",
    "price_per_m2_million",
    "price_billion",
    "log_price_vnd",
    "log_price_per_m2",
    "title",
    "description",
    "listing_id",
    "url",
}

BASE_NUMERIC = ("area_m2",)
BASE_CATEGORICAL = ("property_type", "legacy_area")
OPTIONAL_NUMERIC = ("bedrooms", "bathrooms", "floors", "road_width_m")
OPTIONAL_CATEGORICAL = ("legal_status", "direction")
QA_ONLY_COLUMNS = (
    "area_definition_risk",
    "estimated_land_area_from_title",
    "scope_status",
    "price_valid",
    "area_valid",
)


def add_preliminary_model_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add non-leaking exploratory transforms without changing raw columns."""
    out = df.copy()
    if "area_m2" in out.columns:
        area = pd.to_numeric(out["area_m2"], errors="coerce")
        out["log_area_m2"] = np.log1p(area.clip(lower=0))
        try:
            out["area_size_band"] = pd.qcut(
                area,
                q=4,
                labels=["small", "medium", "large", "very_large"],
                duplicates="drop",
            )
        except ValueError:
            out["area_size_band"] = "unknown"
    return out


def select_model_features(
    df: pd.DataFrame,
    min_non_null_rate: float = 0.70,
) -> dict[str, list[str]]:
    """Select available non-leaking features supported by production data."""
    numeric = [c for c in BASE_NUMERIC if c in df.columns]
    categorical = [c for c in BASE_CATEGORICAL if c in df.columns]

    for column in OPTIONAL_NUMERIC:
        if column in df.columns and df[column].notna().mean() >= min_non_null_rate:
            numeric.append(column)
    for column in OPTIONAL_CATEGORICAL:
        if column in df.columns and df[column].notna().mean() >= min_non_null_rate:
            categorical.append(column)

    numeric = [c for c in numeric if c not in LEAKAGE_COLUMNS]
    categorical = [c for c in categorical if c not in LEAKAGE_COLUMNS]
    assert_no_leakage(numeric + categorical)
    return {"numeric": numeric, "categorical": categorical}


def assert_no_leakage(features: list[str] | tuple[str, ...]) -> None:
    """Raise when a target-derived or identifier/text field enters model X."""
    offenders = sorted(set(features).intersection(LEAKAGE_COLUMNS))
    if offenders:
        raise ValueError(f"Leakage columns detected in model features: {offenders}")


def select_model_v1_features(
    df: pd.DataFrame,
    min_non_null_rate: float = 0.70,
) -> dict[str, list[str]]:
    """Backward-compatible BT3 feature view, retaining log_area_m2 for EDA."""
    numeric = [c for c in ("area_m2", "log_area_m2") if c in df.columns]
    categorical = [c for c in BASE_CATEGORICAL if c in df.columns]
    for column in OPTIONAL_NUMERIC:
        if column in df.columns and df[column].notna().mean() >= min_non_null_rate:
            numeric.append(column)
    for column in OPTIONAL_CATEGORICAL:
        if column in df.columns and df[column].notna().mean() >= min_non_null_rate:
            categorical.append(column)
    assert_no_leakage(numeric + categorical)
    return {"numeric": numeric, "categorical": categorical}


def feature_availability(df: pd.DataFrame) -> pd.DataFrame:
    """Return availability statistics for intended and optional predictors."""
    candidates = list(BASE_NUMERIC + BASE_CATEGORICAL)
    candidates += list(OPTIONAL_NUMERIC + OPTIONAL_CATEGORICAL)
    candidates += ["log_area_m2"]

    rows: list[dict[str, object]] = []
    for column in candidates:
        present = column in df.columns
        non_null = float(df[column].notna().mean()) if present else 0.0
        rows.append(
            {
                "feature": column,
                "present": present,
                "non_null_rate": round(non_null, 4),
                "missing_rate": round(1.0 - non_null, 4),
                "dtype": str(df[column].dtype) if present else None,
                "cardinality": int(df[column].nunique(dropna=True)) if present else 0,
            }
        )
    return pd.DataFrame(rows)


def _leakage_reason(column: str) -> str:
    if column == "price_text":
        return "Raw text biểu diễn chính target giá; dùng làm X sẽ lộ trực tiếp nhãn."
    if column in {"price_billion", "log_price_vnd"}:
        return "Biến đổi trực tiếp từ price_vnd; là target leakage."
    if column in {"displayed_price_per_m2", "price_per_m2_vnd", "price_per_m2_million", "log_price_per_m2"}:
        return "Giá/m² chứa price_vnd trong công thức; dùng làm X sẽ lộ target."
    if column in {"title", "description"}:
        return "Text có thể chứa trực tiếp giá/giá m² và làm model học lại nhãn; loại ở model v1."
    if column in {"listing_id", "url"}:
        return "Identifier không có ý nghĩa dự báo ổn định và có nguy cơ memorization."
    if column == TARGET_COLUMN:
        return "Biến mục tiêu, không được đưa vào X."
    return "Không phù hợp model v1 theo leakage policy."


def build_feature_selection_report(
    df: pd.DataFrame,
    selected: dict[str, list[str]],
) -> pd.DataFrame:
    """Document why every available field is used or excluded from model v1."""
    selected_set = set(selected["numeric"] + selected["categorical"])
    rows: list[dict[str, object]] = []

    for column in df.columns:
        if column == TARGET_COLUMN:
            role = "target"
            reason = "Biến mục tiêu, không được đưa vào X."
        elif column in LEAKAGE_COLUMNS:
            role = "excluded"
            reason = _leakage_reason(column)
        elif column in selected_set:
            role = "model_feature"
            reason = "Đủ availability, có ý nghĩa dự báo và không gây target leakage."
        elif column == "log_area_m2":
            role = "exploratory"
            reason = "Biến đổi phục vụ EDA; không dùng mặc định cùng area_m2 để tránh dư thừa/đa cộng tuyến."
        elif column in QA_ONLY_COLUMNS:
            role = "qa_only"
            reason = "Cờ kiểm soát chất lượng, dùng audit/error analysis thay vì predictor v1."
        elif column in OPTIONAL_NUMERIC + OPTIONAL_CATEGORICAL:
            role = "excluded"
            reason = "Feature tùy chọn chưa đạt ngưỡng availability trên production hiện tại."
        else:
            role = "excluded"
            reason = "Không thuộc feature set đã khóa cho model v1."

        rows.append(
            {
                "feature": column,
                "dtype": str(df[column].dtype),
                "missing_rate": round(float(df[column].isna().mean()), 4),
                "cardinality": int(df[column].nunique(dropna=True)),
                "used_in_model": column in selected_set,
                "role": role,
                "reason": reason,
            }
        )

    return pd.DataFrame(rows).sort_values(
        ["used_in_model", "role", "feature"],
        ascending=[False, True, True],
    ).reset_index(drop=True)
