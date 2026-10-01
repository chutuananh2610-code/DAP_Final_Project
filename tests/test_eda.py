import numpy as np
import pandas as pd

from dap_project.data.eda_cleaning import prepare_eda_dataset
from dap_project.features.build_features import (
    add_preliminary_model_features,
    select_model_v1_features,
)


def _sample_frame():
    rows = []
    for i in range(60):
        rows.append({
            "listing_id": str(i),
            "url": f"https://nhadat.cafeland.vn/nha-{i}.html",
            "title": "Nhà mặt tiền 3 tầng",
            "property_type": "unknown",
            "price_vnd": 5_000_000_000 + i * 20_000_000,
            "area_m2": 60 + (i % 10),
            "legacy_area": "Quận 1",
            "description": np.nan,
            "listing_date": np.nan,
            "area_definition_risk": False,
        })
    rows.append({
        "listing_id": "broker",
        "url": "https://nhadat.cafeland.vn/moi-gioi/test-1.html",
        "title": "Nguyễn Văn A",
        "property_type": "unknown",
        "price_vnd": 6_000_000_000,
        "area_m2": 70,
        "legacy_area": "Quận 1",
        "description": np.nan,
        "listing_date": np.nan,
        "area_definition_risk": False,
    })
    rows.append({
        "listing_id": "extreme",
        "url": "https://nhadat.cafeland.vn/nha-extreme.html",
        "title": "Nhà mặt tiền 20 tầng",
        "property_type": "house",
        "price_vnd": 900_000_000_000,
        "area_m2": 50_000,
        "legacy_area": "Quận 1",
        "description": np.nan,
        "listing_date": np.nan,
        "area_definition_risk": True,
    })
    return pd.DataFrame(rows)


def test_prepare_eda_dataset_filters_and_refines():
    cleaned, audit, diagnostics, missing = prepare_eda_dataset(_sample_frame())
    assert diagnostics["structural_non_listing_rows"] == 1
    assert diagnostics["property_type_refined_rows"] >= 60
    assert "broker" not in set(cleaned["listing_id"])
    assert "extreme" not in set(cleaned["listing_id"])
    assert diagnostics["robust_outlier_rows_removed"] >= 1
    assert "description" in set(missing["column"])


def test_model_v1_feature_selection_blocks_target_derived_columns():
    cleaned, _, _, _ = prepare_eda_dataset(_sample_frame())
    featured = add_preliminary_model_features(cleaned)
    selected = select_model_v1_features(featured)
    chosen = set(selected["numeric"] + selected["categorical"])
    assert "area_m2" in chosen
    assert "property_type" in chosen
    assert "legacy_area" in chosen
    assert "price_per_m2_vnd" not in chosen
    assert "price_billion" not in chosen
    assert "log_price_vnd" not in chosen
