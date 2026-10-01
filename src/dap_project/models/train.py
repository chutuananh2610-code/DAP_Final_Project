"""Training utilities for BQ01 regression models."""

from __future__ import annotations

import time
from typing import Any

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.model_selection import GridSearchCV, KFold, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor


def build_preprocessor(
    numeric_features: list[str],
    categorical_features: list[str],
) -> ColumnTransformer:
    """Build train-only preprocessing for numeric and categorical predictors."""
    numeric_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", drop="first")),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric_pipe, numeric_features),
            ("categorical", categorical_pipe, categorical_features),
        ],
        remainder="drop",
    )


def build_pipeline(
    estimator: Any,
    numeric_features: list[str],
    categorical_features: list[str],
) -> Pipeline:
    """Combine preprocessing and estimator into a leakage-safe pipeline."""
    return Pipeline(
        [
            ("preprocess", build_preprocessor(numeric_features, categorical_features)),
            ("model", estimator),
        ]
    )


def train_candidate_models(
    X_train,
    y_train,
    numeric_features: list[str],
    categorical_features: list[str],
    *,
    random_state: int = 42,
    cv_folds: int = 5,
    tune: bool = True,
    include_random_forest: bool = True,
) -> tuple[dict[str, Pipeline], dict[str, dict[str, Any]]]:
    """Fit baseline, linear and non-linear regressors using CV-based tuning."""
    cv = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    fitted: dict[str, Pipeline] = {}
    tuning: dict[str, dict[str, Any]] = {}

    base_specs = {
        "Dummy Median": DummyRegressor(strategy="median"),
        "Linear Regression": LinearRegression(),
    }
    for name, estimator in base_specs.items():
        model = build_pipeline(estimator, numeric_features, categorical_features)
        start = time.perf_counter()
        model.fit(X_train, y_train)
        fitted[name] = model
        tuning[name] = {
            "best_params": {},
            "fit_seconds": round(time.perf_counter() - start, 4),
            "tuned_with_cv": False,
        }

    if tune:
        ridge_search = GridSearchCV(
            build_pipeline(Ridge(), numeric_features, categorical_features),
            {"model__alpha": [0.1, 1.0, 10.0, 100.0, 1000.0]},
            scoring="neg_mean_absolute_error",
            cv=cv,
            n_jobs=-1,
        )
        tree_search = GridSearchCV(
            build_pipeline(
                DecisionTreeRegressor(random_state=random_state),
                numeric_features,
                categorical_features,
            ),
            {
                "model__max_depth": [5, 8, 12, None],
                "model__min_samples_split": [2, 10],
                "model__min_samples_leaf": [3, 10, 25],
            },
            scoring="neg_mean_absolute_error",
            cv=cv,
            n_jobs=-1,
        )
        searches: list[tuple[str, Any]] = [
            ("Ridge", ridge_search),
            ("Decision Tree", tree_search),
        ]

        if include_random_forest:
            forest_search = RandomizedSearchCV(
                build_pipeline(
                    RandomForestRegressor(random_state=random_state, n_jobs=-1),
                    numeric_features,
                    categorical_features,
                ),
                {
                    "model__n_estimators": [100, 160, 220],
                    "model__max_depth": [10, 14, None],
                    "model__min_samples_leaf": [2, 4, 8],
                    "model__max_features": ["sqrt", 0.7, 1.0],
                },
                n_iter=8,
                scoring="neg_mean_absolute_error",
                cv=cv,
                random_state=random_state,
                n_jobs=-1,
            )
            searches.append(("Random Forest", forest_search))

        for name, search in searches:
            start = time.perf_counter()
            search.fit(X_train, y_train)
            fitted[name] = search.best_estimator_
            tuning[name] = {
                "best_params": search.best_params_,
                "best_cv_mae": float(-search.best_score_),
                "fit_seconds": round(time.perf_counter() - start, 4),
                "tuned_with_cv": True,
            }
    else:
        fixed_specs = {
            "Ridge": Ridge(alpha=10.0),
            "Decision Tree": DecisionTreeRegressor(
                max_depth=6,
                min_samples_leaf=5,
                random_state=random_state,
            ),
        }
        if include_random_forest:
            fixed_specs["Random Forest"] = RandomForestRegressor(
                n_estimators=30,
                max_depth=8,
                min_samples_leaf=4,
                random_state=random_state,
                n_jobs=1,
            )
        for name, estimator in fixed_specs.items():
            model = build_pipeline(estimator, numeric_features, categorical_features)
            start = time.perf_counter()
            model.fit(X_train, y_train)
            fitted[name] = model
            tuning[name] = {
                "best_params": {},
                "fit_seconds": round(time.perf_counter() - start, 4),
                "tuned_with_cv": False,
            }

    return fitted, tuning
