"""Model interpretation helpers for BQ01."""

from __future__ import annotations

import pandas as pd
from sklearn.inspection import permutation_importance


def permutation_importance_report(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    *,
    random_state: int = 42,
    n_repeats: int = 8,
) -> pd.DataFrame:
    """Compute original-feature permutation importance using holdout MAE."""
    result = permutation_importance(
        model,
        X_test,
        y_test,
        scoring="neg_mean_absolute_error",
        n_repeats=n_repeats,
        random_state=random_state,
        n_jobs=-1,
    )
    return (
        pd.DataFrame(
            {
                "feature": X_test.columns,
                "importance_mean_mae": result.importances_mean,
                "importance_std": result.importances_std,
            }
        )
        .sort_values("importance_mean_mae", ascending=False)
        .reset_index(drop=True)
    )


def linear_coefficient_report(model) -> pd.DataFrame:
    """Return encoded coefficients for a fitted linear/ridge pipeline."""
    preprocessor = model.named_steps["preprocess"]
    estimator = model.named_steps["model"]
    if not hasattr(estimator, "coef_"):
        return pd.DataFrame(columns=["feature", "coefficient"])

    names = preprocessor.get_feature_names_out()
    return (
        pd.DataFrame(
            {
                "feature": names,
                "coefficient": estimator.coef_,
            }
        )
        .assign(abs_coefficient=lambda x: x["coefficient"].abs())
        .sort_values("abs_coefficient", ascending=False)
        .reset_index(drop=True)
    )
