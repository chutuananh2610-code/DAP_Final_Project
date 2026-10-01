from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
import pytest

from dap_project.features.build_features import (
    assert_no_leakage,
    build_feature_selection_report,
    select_model_features,
)
from dap_project.models.evaluate import regression_metrics
from dap_project.models.train import train_candidate_models


def _sample_frame(n: int = 72) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    area = rng.uniform(35, 250, size=n)
    property_type = rng.choice(["house", "apartment", "land"], size=n)
    legacy_area = rng.choice(["Quận 1", "Quận 7", "TP Thủ Đức"], size=n)
    area_effect = area * 45_000_000
    type_effect = pd.Series(property_type).map(
        {"house": 3_000_000_000, "apartment": 1_000_000_000, "land": 2_000_000_000}
    ).to_numpy()
    noise = rng.normal(0, 800_000_000, size=n)
    return pd.DataFrame(
        {
            "area_m2": area,
            "property_type": property_type,
            "legacy_area": legacy_area,
            "price_vnd": area_effect + type_effect + noise,
            "price_text": "leak",
            "listing_id": [f"id-{i}" for i in range(n)],
        }
    )


def test_feature_selection_excludes_leakage():
    df = _sample_frame()
    selected = select_model_features(df)
    features = selected["numeric"] + selected["categorical"]
    assert features == ["area_m2", "property_type", "legacy_area"]
    assert "price_vnd" not in features
    assert "price_text" not in features
    assert "listing_id" not in features


def test_explicit_leakage_guard_raises():
    with pytest.raises(ValueError):
        assert_no_leakage(["area_m2", "price_vnd"])


def test_feature_report_documents_target_and_features():
    df = _sample_frame()
    selected = select_model_features(df)
    report = build_feature_selection_report(df, selected)
    target = report.loc[report["feature"] == "price_vnd"].iloc[0]
    area = report.loc[report["feature"] == "area_m2"].iloc[0]
    assert target["role"] == "target"
    assert bool(area["used_in_model"])


def test_pipeline_handles_unseen_category_and_reload(tmp_path):
    df = _sample_frame()
    X = df[["area_m2", "property_type", "legacy_area"]]
    y = df["price_vnd"]
    models, _ = train_candidate_models(
        X,
        y,
        ["area_m2"],
        ["property_type", "legacy_area"],
        cv_folds=3,
        tune=False,
        include_random_forest=False,
    )
    model = models["Ridge"]
    unseen = pd.DataFrame(
        [{"area_m2": 100.0, "property_type": "villa", "legacy_area": "Quận 3"}]
    )
    prediction = model.predict(unseen)
    assert prediction.shape == (1,)
    assert np.isfinite(prediction[0])

    path = tmp_path / "model.joblib"
    joblib.dump(model, path)
    reloaded = joblib.load(path)
    assert np.allclose(prediction, reloaded.predict(unseen))


def test_regression_metrics_are_complete():
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.5, 2.5])
    metrics = regression_metrics(y_true, y_pred)
    assert set(metrics) == {"MAE", "RMSE", "R2"}
    assert metrics["MAE"] >= 0
    assert metrics["RMSE"] >= metrics["MAE"]
