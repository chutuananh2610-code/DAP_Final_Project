"""Cleaning and audit utilities for Bài tập 3 (EDA)."""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd

from .parsers import infer_property_type


DEFAULT_EDA_CONFIG = {
    "iqr_multiplier": 3.0,
    "outlier_min_group_size": 30,
    "outlier_votes_to_remove": 2,
    "non_listing_path_tokens": ["/moi-gioi/"],
}


MISSING_POLICIES = {
    "description": (
        "Structural/MNAR-like",
        "Card-only crawl does not expose description; do not impute. "
        "Exclude from model v1 unless detail enrichment is run.",
    ),
    "listing_date": (
        "Structural/MNAR-like",
        "Card-only crawl does not expose a reliable listing date; do not impute. "
        "Temporal modeling is deferred.",
    ),
    "update_text": (
        "MAR/collection-layout",
        "Keep missing as missing. Not used in model v1.",
    ),
    "location_text": (
        "MAR/collection-layout",
        "Use validated legacy_area for district-level EDA.",
    ),
    "current_ward": (
        "MAR relative to scope mapping",
        "Keep missing; legacy_area is used for district grouping.",
    ),
    "estimated_land_area_from_title": (
        "MNAR-like",
        "Available only when a title contains explicit dimensions; use as QA only.",
    ),
}


def refine_property_types(df: pd.DataFrame) -> pd.DataFrame:
    """Improve unknown property types without overwriting known labels."""
    out = df.copy()
    if "property_type" not in out.columns:
        out["property_type"] = "unknown"

    current = out["property_type"].fillna("unknown").astype(str).str.lower()
    unknown = current.eq("unknown")
    title = out.get("title", pd.Series("", index=out.index)).fillna("").astype(str)
    url = out.get("url", pd.Series("", index=out.index)).fillna("").astype(str)
    inferred = (title + " " + url).map(infer_property_type)

    refined = unknown & inferred.ne("unknown")
    out["property_type_refined"] = refined
    out.loc[refined, "property_type"] = inferred.loc[refined]
    out["property_type"] = out["property_type"].fillna("unknown")
    return out


def add_eda_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add descriptive features. Target-derived fields are EDA-only."""
    out = df.copy()
    price = pd.to_numeric(out["price_vnd"], errors="coerce")
    area = pd.to_numeric(out["area_m2"], errors="coerce")

    out["price_billion"] = price / 1_000_000_000
    ratio = np.divide(
        price.to_numpy(dtype=float),
        area.to_numpy(dtype=float),
        out=np.full(len(out), np.nan, dtype=float),
        where=area.to_numpy(dtype=float) > 0,
    )
    out["price_per_m2_vnd"] = ratio
    out["price_per_m2_million"] = ratio / 1_000_000
    out["log_price_vnd"] = np.log1p(price)
    out["log_area_m2"] = np.log1p(area)
    out["log_price_per_m2"] = np.log1p(out["price_per_m2_vnd"])
    return out


def _group_robust_iqr_flag(
    values: pd.Series,
    groups: pd.Series,
    multiplier: float,
    min_group_size: int,
) -> pd.Series:
    """Flag extreme observations using groupwise IQR with global fallback."""
    frame = pd.DataFrame({"value": values, "group": groups.fillna("unknown")})
    q1 = frame.groupby("group")["value"].transform(lambda s: s.quantile(0.25))
    q3 = frame.groupby("group")["value"].transform(lambda s: s.quantile(0.75))
    size = frame.groupby("group")["value"].transform("count")

    global_q1 = values.quantile(0.25)
    global_q3 = values.quantile(0.75)
    q1 = q1.where(size >= min_group_size, global_q1)
    q3 = q3.where(size >= min_group_size, global_q3)

    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr
    valid = values.notna() & np.isfinite(values)
    return valid & ((values < lower) | (values > upper))


def build_missing_policy(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize missingness and the documented treatment decision."""
    rows: list[dict[str, Any]] = []
    for column in df.columns:
        missing_count = int(df[column].isna().sum())
        if missing_count == 0:
            continue
        mechanism, action = MISSING_POLICIES.get(
            column,
            ("Unclassified", "Keep missing and review before modeling."),
        )
        rows.append({
            "column": column,
            "missing_count": missing_count,
            "missing_rate_pct": round(missing_count / len(df) * 100, 2),
            "mechanism": mechanism,
            "action": action,
        })
    columns = ["column", "missing_count", "missing_rate_pct", "mechanism", "action"]
    result = pd.DataFrame(rows, columns=columns)
    if result.empty:
        return result
    return result.sort_values(
        ["missing_rate_pct", "column"], ascending=[False, True]
    )


def prepare_eda_dataset(
    df: pd.DataFrame,
    config: dict[str, Any] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], pd.DataFrame]:
    """Create a row-level audit table and a cleaned BT3 dataset."""
    cfg = {**DEFAULT_EDA_CONFIG, **(config or {})}
    audit = add_eda_features(refine_property_types(df))

    tokens = [re.escape(str(x)) for x in cfg["non_listing_path_tokens"]]
    pattern = "|".join(tokens) if tokens else r"$^"
    audit["is_non_listing_url"] = audit["url"].fillna("").astype(str).str.contains(
        pattern, case=False, regex=True
    )

    for column in [
        "outlier_price_log",
        "outlier_area_log",
        "outlier_price_per_m2_log",
    ]:
        audit[column] = False

    listing_mask = ~audit["is_non_listing_url"]
    listing = audit.loc[listing_mask]
    groups = listing["property_type"].fillna("unknown")
    multiplier = float(cfg["iqr_multiplier"])
    min_group = int(cfg["outlier_min_group_size"])

    audit.loc[listing.index, "outlier_price_log"] = _group_robust_iqr_flag(
        listing["log_price_vnd"], groups, multiplier, min_group
    )
    audit.loc[listing.index, "outlier_area_log"] = _group_robust_iqr_flag(
        listing["log_area_m2"], groups, multiplier, min_group
    )
    audit.loc[listing.index, "outlier_price_per_m2_log"] = _group_robust_iqr_flag(
        listing["log_price_per_m2"], groups, multiplier, min_group
    )

    flag_columns = [
        "outlier_price_log",
        "outlier_area_log",
        "outlier_price_per_m2_log",
    ]
    audit["outlier_vote_count"] = audit[flag_columns].sum(axis=1).astype(int)
    audit["is_robust_outlier"] = (
        audit["outlier_vote_count"] >= int(cfg["outlier_votes_to_remove"])
    )

    keep = (~audit["is_non_listing_url"]) & (~audit["is_robust_outlier"])
    cleaned = audit.loc[keep].copy().reset_index(drop=True)

    unknown_before = int(
        df["property_type"].fillna("unknown").astype(str).str.lower().eq("unknown").sum()
    )
    unknown_after = int(
        cleaned["property_type"].astype(str).str.lower().eq("unknown").sum()
    )
    diagnostics = {
        "input_rows": int(len(df)),
        "structural_non_listing_rows": int(audit["is_non_listing_url"].sum()),
        "rows_after_structural_filter": int((~audit["is_non_listing_url"]).sum()),
        "property_type_unknown_before": unknown_before,
        "property_type_refined_rows": int(audit["property_type_refined"].sum()),
        "property_type_unknown_cleaned": unknown_after,
        "outlier_price_log_rows": int(audit["outlier_price_log"].sum()),
        "outlier_area_log_rows": int(audit["outlier_area_log"].sum()),
        "outlier_price_per_m2_log_rows": int(
            audit["outlier_price_per_m2_log"].sum()
        ),
        "robust_outlier_rows_removed": int(
            ((~audit["is_non_listing_url"]) & audit["is_robust_outlier"]).sum()
        ),
        "cleaned_rows": int(len(cleaned)),
        "retained_pct": round(len(cleaned) / len(df) * 100, 2) if len(df) else 0.0,
    }

    risk = cleaned.get("area_definition_risk")
    if risk is not None:
        diagnostics["area_definition_risk_rows_cleaned"] = int(
            risk.fillna(False).astype(bool).sum()
        )
    else:
        diagnostics["area_definition_risk_rows_cleaned"] = 0

    missing_policy = build_missing_policy(cleaned)
    return cleaned, audit, diagnostics, missing_policy
