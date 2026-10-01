import pandas as pd

from dap_project.data.eda_cleaning import prepare_eda_dataset
from dap_project.features.build_features import (
    add_preliminary_model_features,
    select_model_v1_features,
)


def _sample_frame():
    return pd.DataFrame({
        "listing_id": ["1", "2", "3", "4", "5", "6"],
        "url": [
            "https://nhadat.cafeland.vn/ban-nha-1.html",
            "https://nhadat.cafeland.vn/chcc-2.html",
            "https://nhadat.cafeland.vn/moi-gioi/test-3.html",
            "https://nhadat.cafeland.vn/dat-4.html",
            "https://nhadat.cafeland.vn/biet-thu-5.html",
            "https://nhadat.cafeland.vn/nha-6.html",
        ],
        "title": [
            "Bán nhà 3 tầng Quận 1",
            "Bán CHCC 2PN Quận 7",
            "Nguyễn Văn A",
            "Bán đất nền Củ Chi",
            "Biệt thự khu Thảo Điền",
            "Nhà phố Bình Thạnh",
        ],
        "property_type": ["unknown", "unknown", "unknown", "land", "villa", "house"],
        "price_vnd": [8e9, 4e9, 1e9, 2e9, 30e9, 10e9],
        "area_m2": [60, 70, 50, 120, 250, 80],
        "legacy_area": ["Quận 1", "Quận 7", "Quận 3", "Huyện Củ Chi", "TP Thủ Đức", "Quận Bình Thạnh"],
    })


def test_prepare_eda_filters_profiles_and_refines_unknown_types():
    cleaned, audit, diagnostics, _ = prepare_eda_dataset(
        _sample_frame(),
        config={"outlier_min_group_size": 30, "outlier_votes_to_remove": 3},
    )

    assert diagnostics["structural_non_listing_rows"] == 1
    assert len(cleaned) == 5
    assert audit["property_type_refined"].sum() >= 2
    assert cleaned.loc[cleaned["listing_id"].eq("1"), "property_type"].iloc[0] == "house"
    assert cleaned.loc[cleaned["listing_id"].eq("2"), "property_type"].iloc[0] == "apartment"


def test_model_v1_feature_selection_blocks_target_derived_fields():
    cleaned, _, _, _ = prepare_eda_dataset(
        _sample_frame(),
        config={"outlier_min_group_size": 30, "outlier_votes_to_remove": 3},
    )
    featured = add_preliminary_model_features(cleaned)
    selected = select_model_v1_features(featured)
    all_features = selected["numeric"] + selected["categorical"]

    assert "area_m2" in selected["numeric"]
    assert "property_type" in selected["categorical"]
    assert "legacy_area" in selected["categorical"]
    assert "price_per_m2_vnd" not in all_features
    assert "price_per_m2_million" not in all_features
    assert "price_vnd" not in all_features
