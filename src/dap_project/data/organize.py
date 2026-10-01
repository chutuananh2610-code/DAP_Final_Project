"""Pandas/NumPy organization and initial quality checks."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .parsers import infer_property_type, parse_area_m2, parse_price_vnd
from .scope import infer_scope, load_scope_map


def normalize_dataframe(
    df: pd.DataFrame,
    scope_map_path: str | Path,
) -> pd.DataFrame:
    """Vector-friendly normalization without row-by-row mutation."""
    out = df.copy()

    for col in [
        "source", "url", "listing_id", "title", "description",
        "price_text", "area_text", "location_text", "property_type",
        "listing_date",
    ]:
        if col not in out.columns:
            out[col] = pd.NA

    out["price_vnd"] = out["price_text"].map(parse_price_vnd)
    out["area_m2"] = out["area_text"].map(parse_area_m2)

    unknown_type = out["property_type"].isna() | out["property_type"].eq("unknown")
    out.loc[unknown_type, "property_type"] = (
        out.loc[unknown_type, "title"].fillna("").astype(str)
        .add(" ")
        .add(out.loc[unknown_type, "url"].fillna("").astype(str))
        .map(infer_property_type)
    )

    scope_map = load_scope_map(scope_map_path)
    scope_values = [
        infer_scope(
            str(loc or ""),
            str(title or ""),
            str(desc or ""),
            scope_map,
        )
        for loc, title, desc in zip(
            out["location_text"].fillna(""),
            out["title"].fillna(""),
            out["description"].fillna(""),
        )
    ]
    out[["scope_status", "current_ward", "legacy_area"]] = pd.DataFrame(
        scope_values, index=out.index
    )

    # ID fallback from URL.
    fallback_id = out["url"].astype(str).str.extract(r"-(\d+)\.html$", expand=False)
    out["listing_id"] = out["listing_id"].fillna(fallback_id)
    out.loc[out["listing_id"].eq(""), "listing_id"] = fallback_id

    out["listing_date"] = pd.to_datetime(
        out["listing_date"], format="%d-%m-%Y", errors="coerce"
    )

    # QA flags: not final cleaning decisions.
    out["price_valid"] = np.isfinite(out["price_vnd"]) & (out["price_vnd"] > 0)
    out["area_valid"] = np.isfinite(out["area_m2"]) & (out["area_m2"] > 0)
    out["area_definition_risk"] = False

    # Common clue: house title says width x length while displayed area can be floor area.
    house_mask = out["property_type"].eq("house")
    dims = out["title"].fillna("").astype(str).str.extract(
        r"(\d+(?:[.,]\d+)?)\s*[mx×x]\s*(\d+(?:[.,]\d+)?)",
        expand=True,
    )
    dims = dims.replace(",", ".", regex=True).astype(float)
    estimated_land = dims[0] * dims[1]
    out["estimated_land_area_from_title"] = estimated_land
    mismatch = house_mask & estimated_land.notna() & out["area_m2"].notna()
    mismatch &= (np.abs(out["area_m2"] - estimated_land) / estimated_land) > 0.25
    out.loc[mismatch, "area_definition_risk"] = True

    return out


def build_processed(df: pd.DataFrame) -> pd.DataFrame:
    """Initial processed gate before EDA; no outlier trimming here."""
    keep_scope = df["scope_status"].isin([
        "confirmed_by_current_ward",
        "confirmed_by_legacy_text",
    ])
    valid = keep_scope & df["price_valid"] & df["area_valid"]
    out = df.loc[valid].copy()
    out = out.drop_duplicates(subset=["listing_id"], keep="first")
    return out.reset_index(drop=True)


def quality_summary(df: pd.DataFrame) -> dict[str, Any]:
    missing = df.isna().mean().sort_values(ascending=False)
    return {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "duplicate_listing_id": int(
            df["listing_id"].duplicated().sum()
            if "listing_id" in df.columns else 0
        ),
        "missing_rate": {k: float(v) for k, v in missing.items()},
        "dtypes": {k: str(v) for k, v in df.dtypes.items()},
    }


def save_multiformat(df: pd.DataFrame, base_path: str | Path) -> dict[str, str]:
    """Save CSV, JSON and Parquet when engine is available."""
    base = Path(base_path)
    base.parent.mkdir(parents=True, exist_ok=True)

    paths = {}
    csv_path = base.with_suffix(".csv")
    json_path = base.with_suffix(".json")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df.to_json(json_path, orient="records", force_ascii=False, indent=2, date_format="iso")
    paths["csv"] = str(csv_path)
    paths["json"] = str(json_path)

    try:
        parquet_path = base.with_suffix(".parquet")
        df.to_parquet(parquet_path, index=False)
        paths["parquet"] = str(parquet_path)
    except Exception:
        pass

    return paths


def benchmark_io(paths: dict[str, str], repeat: int = 3) -> pd.DataFrame:
    """Compare size and read time across storage formats."""
    rows = []
    for fmt, path in paths.items():
        p = Path(path)
        timings = []
        for _ in range(repeat):
            start = time.perf_counter()
            if fmt == "csv":
                pd.read_csv(p)
            elif fmt == "json":
                pd.read_json(p)
            elif fmt == "parquet":
                pd.read_parquet(p)
            timings.append(time.perf_counter() - start)

        rows.append({
            "format": fmt,
            "size_bytes": p.stat().st_size,
            "read_seconds_mean": float(np.mean(timings)),
        })
    return pd.DataFrame(rows).sort_values("read_seconds_mean")
