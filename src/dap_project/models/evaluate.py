"""Evaluation helpers for BQ01 regression models."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score


def regression_metrics(y_true, y_pred) -> dict[str, float]:
    """Return MAE, RMSE and R-squared in the target's original VNĐ scale."""
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "R2": float(r2_score(y_true, y_pred)),
    }


def evaluate_fitted_models(
    models: dict,
    tuning: dict,
    X_train,
    y_train,
    X_test,
    y_test,
    *,
    random_state: int = 42,
    cv_folds: int = 5,
) -> pd.DataFrame:
    """Evaluate fitted models without using the test set for hyperparameter tuning."""
    cv = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    rows: list[dict[str, object]] = []

    for name, model in models.items():
        train_pred = model.predict(X_train)
        test_pred = model.predict(X_test)
        train_metrics = regression_metrics(y_train, train_pred)
        test_metrics = regression_metrics(y_test, test_pred)
        cv_mae = -cross_val_score(
            model,
            X_train,
            y_train,
            scoring="neg_mean_absolute_error",
            cv=cv,
            n_jobs=-1,
        )

        rows.append(
            {
                "Model": name,
                "CV_MAE_mean": float(cv_mae.mean()),
                "CV_MAE_std": float(cv_mae.std()),
                "Train_MAE": train_metrics["MAE"],
                "Test_MAE": test_metrics["MAE"],
                "Train_RMSE": train_metrics["RMSE"],
                "Test_RMSE": test_metrics["RMSE"],
                "Train_R2": train_metrics["R2"],
                "Test_R2": test_metrics["R2"],
                "Generalization_gap_MAE": test_metrics["MAE"] - train_metrics["MAE"],
                "Training_time_seconds": float(tuning[name]["fit_seconds"]),
                "Tuned_with_CV": bool(tuning[name]["tuned_with_cv"]),
            }
        )

    return pd.DataFrame(rows).sort_values("CV_MAE_mean").reset_index(drop=True)


def choose_final_model(comparison: pd.DataFrame) -> str:
    """Choose model family by CV MAE; test metrics remain final holdout evidence."""
    candidates = comparison.loc[comparison["Model"] != "Dummy Median"].copy()
    if candidates.empty:
        raise ValueError("No non-baseline candidate model is available.")
    candidates = candidates.sort_values(["CV_MAE_mean", "CV_MAE_std"])
    return str(candidates.iloc[0]["Model"])


def build_prediction_frame(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    context: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Create row-level holdout predictions for error analysis."""
    pred = model.predict(X_test)
    out = pd.DataFrame(
        {
            "actual_price": np.asarray(y_test, dtype=float),
            "predicted_price": np.asarray(pred, dtype=float),
        },
        index=X_test.index,
    )
    out["absolute_error"] = (out["actual_price"] - out["predicted_price"]).abs()
    out["percentage_error"] = np.where(
        out["actual_price"] > 0,
        out["absolute_error"] / out["actual_price"] * 100.0,
        np.nan,
    )

    if context is not None:
        for column in [
            "property_type",
            "legacy_area",
            "area_m2",
            "area_definition_risk",
        ]:
            if column in context.columns:
                out[column] = context.loc[out.index, column]

    return out.reset_index(drop=True)
