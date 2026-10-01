"""Feature and modeling pipeline for BQ01 real-estate price prediction."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import joblib
import matplotlib
import numpy as np
import pandas as pd
import yaml
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, learning_curve, train_test_split

matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings(
    "ignore",
    message=r"`sklearn\.utils\.parallel\.delayed` should be used.*",
    category=UserWarning,
)

from dap_project.features.build_features import (
    TARGET_COLUMN,
    add_preliminary_model_features,
    build_feature_selection_report,
    select_model_features,
)
from dap_project.models.evaluate import (
    build_prediction_frame,
    choose_final_model,
    evaluate_fitted_models,
)
from dap_project.models.interpret import (
    linear_coefficient_report,
    permutation_importance_report,
)
from dap_project.models.train import train_candidate_models


def _load_config(project_root: Path) -> dict:
    with (project_root / "config.yaml").open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _latest_cleaned_path(project_root: Path) -> Path:
    processed = project_root / "data" / "processed"
    parquet = sorted(processed.glob("hcm_realestate_cleaned_*.parquet"))
    if parquet:
        return parquet[-1]
    csv = sorted(processed.glob("hcm_realestate_cleaned_*.csv"))
    if csv:
        return csv[-1]
    raise FileNotFoundError("Không tìm thấy cleaned dataset từ Bài tập 3.")


def _read_dataset(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def _numeric_vif(df: pd.DataFrame, numeric_features: list[str]) -> pd.DataFrame:
    """Calculate VIF without adding statsmodels as a project dependency."""
    if not numeric_features:
        return pd.DataFrame(columns=["feature", "VIF"])
    if len(numeric_features) == 1:
        return pd.DataFrame({"feature": numeric_features, "VIF": [1.0]})

    clean = df[numeric_features].apply(pd.to_numeric, errors="coerce")
    clean = clean.fillna(clean.median(numeric_only=True))
    rows = []
    for feature in numeric_features:
        others = [c for c in numeric_features if c != feature]
        model = LinearRegression().fit(clean[others], clean[feature])
        r2 = float(model.score(clean[others], clean[feature]))
        vif = float("inf") if r2 >= 0.999999 else 1.0 / (1.0 - r2)
        rows.append({"feature": feature, "VIF": vif})
    return pd.DataFrame(rows)


def run_feature_stage(project_root: Path) -> dict:
    """Audit the BT3 cleaned data and freeze a non-leaking model feature set."""
    project_root = Path(project_root)
    config = _load_config(project_root)
    model_cfg = config.get("modeling", {})
    threshold = float(
        model_cfg.get(
            "feature_min_non_null_rate",
            config.get("eda", {}).get("feature_min_non_null_rate", 0.70),
        )
    )
    source = _latest_cleaned_path(project_root)
    df = add_preliminary_model_features(_read_dataset(source))
    selected = select_model_features(df, min_non_null_rate=threshold)
    features = selected["numeric"] + selected["categorical"]

    report_dir = project_root / "reports" / "modeling"
    report_dir.mkdir(parents=True, exist_ok=True)
    selection_report = build_feature_selection_report(df, selected)
    selection_path = report_dir / "feature_selection_report.csv"
    selection_report.to_csv(selection_path, index=False, encoding="utf-8-sig")

    duplicate_listing = 0
    if "listing_id" in df.columns:
        duplicate_listing = int(df["listing_id"].duplicated().sum())

    audit = {
        "source": str(source),
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "target": TARGET_COLUMN,
        "target_missing": int(df[TARGET_COLUMN].isna().sum()),
        "target_nonpositive": int((pd.to_numeric(df[TARGET_COLUMN], errors="coerce") <= 0).sum()),
        "duplicate_listing_id": duplicate_listing,
        "numeric_features": selected["numeric"],
        "categorical_features": selected["categorical"],
        "model_features": features,
        "feature_count": len(features),
    }
    audit_path = report_dir / "modeling_data_audit.json"
    _write_json(audit_path, audit)
    audit_csv_path = report_dir / "MODELING_DATA_AUDIT.csv"
    pd.DataFrame([audit]).to_csv(audit_csv_path, index=False, encoding="utf-8-sig")

    corr_path = report_dir / "numeric_correlation.csv"
    if selected["numeric"]:
        df[selected["numeric"]].corr(numeric_only=True).to_csv(
            corr_path,
            encoding="utf-8-sig",
        )
    else:
        pd.DataFrame().to_csv(corr_path)

    vif = _numeric_vif(df, selected["numeric"])
    vif_path = report_dir / "vif.csv"
    vif.to_csv(vif_path, index=False, encoding="utf-8-sig")

    return {
        "dataframe": df,
        "source": source,
        "selected": selected,
        "audit": audit,
        "selection_report_path": selection_path,
        "audit_path": audit_path,
        "audit_csv_path": audit_csv_path,
        "correlation_path": corr_path,
        "vif_path": vif_path,
    }


def _group_error_table(pred: pd.DataFrame, group: str) -> pd.DataFrame:
    if group not in pred.columns:
        return pd.DataFrame()
    return (
        pred.groupby(group, dropna=False)
        .agg(
            rows=("absolute_error", "size"),
            MAE=("absolute_error", "mean"),
            Median_APE=("percentage_error", "median"),
        )
        .sort_values("MAE", ascending=False)
        .reset_index()
    )


def _save_figure(fig, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def _plot_actual_vs_predicted(pred: pd.DataFrame, path: Path) -> str:
    fig, ax = plt.subplots(figsize=(7, 6))
    x = pred["actual_price"] / 1e9
    y = pred["predicted_price"] / 1e9
    ax.scatter(x, y, alpha=0.55, s=20)
    low = min(float(x.min()), float(y.min()))
    high = max(float(x.max()), float(y.max()))
    ax.plot([low, high], [low, high], linestyle="--", linewidth=1.5)
    ax.set_title("Actual vs Predicted Price — Holdout Set")
    ax.set_xlabel("Actual price (tỷ VNĐ)")
    ax.set_ylabel("Predicted price (tỷ VNĐ)")
    return _save_figure(fig, path)


def _plot_residual_distribution(pred: pd.DataFrame, path: Path) -> str:
    residual = (pred["actual_price"] - pred["predicted_price"]) / 1e9
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist(residual, bins=35)
    ax.axvline(0, linestyle="--", linewidth=1.5)
    ax.set_title("Residual Distribution — Final Model")
    ax.set_xlabel("Actual - predicted (tỷ VNĐ)")
    ax.set_ylabel("Listings")
    return _save_figure(fig, path)


def _plot_residual_vs_predicted(pred: pd.DataFrame, path: Path) -> str:
    residual = (pred["actual_price"] - pred["predicted_price"]) / 1e9
    predicted = pred["predicted_price"] / 1e9
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(predicted, residual, alpha=0.5, s=18)
    ax.axhline(0, linestyle="--", linewidth=1.5)
    ax.set_title("Residual vs Predicted Price")
    ax.set_xlabel("Predicted price (tỷ VNĐ)")
    ax.set_ylabel("Residual (tỷ VNĐ)")
    return _save_figure(fig, path)


def _plot_model_comparison(comparison: pd.DataFrame, path: Path) -> str:
    fig, ax = plt.subplots(figsize=(9, 5))
    positions = np.arange(len(comparison))
    width = 0.38
    ax.bar(positions - width / 2, comparison["Test_MAE"] / 1e9, width, label="MAE")
    ax.bar(positions + width / 2, comparison["Test_RMSE"] / 1e9, width, label="RMSE")
    ax.set_xticks(positions)
    ax.set_xticklabels(comparison["Model"], rotation=20, ha="right")
    ax.set_ylabel("Error (tỷ VNĐ)")
    ax.set_title("Holdout Error Comparison")
    ax.legend()
    return _save_figure(fig, path)


def _plot_learning_curve(
    model,
    X_train,
    y_train,
    path: Path,
    title: str,
    *,
    random_state: int,
    cv_folds: int,
) -> str:
    cv = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    sizes, train_scores, valid_scores = learning_curve(
        model,
        X_train,
        y_train,
        train_sizes=np.linspace(0.2, 1.0, 5),
        scoring="neg_mean_absolute_error",
        cv=cv,
        n_jobs=1,
    )
    train_mae = -train_scores.mean(axis=1) / 1e9
    valid_mae = -valid_scores.mean(axis=1) / 1e9
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(sizes, train_mae, marker="o", label="Train MAE")
    ax.plot(sizes, valid_mae, marker="o", label="Validation MAE")
    ax.set_title(title)
    ax.set_xlabel("Training samples")
    ax.set_ylabel("MAE (tỷ VNĐ)")
    ax.legend()
    return _save_figure(fig, path)


def _plot_importance(importance: pd.DataFrame, path: Path) -> str:
    top = importance.head(12).sort_values("importance_mean_mae")
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(top["feature"], top["importance_mean_mae"] / 1e9)
    ax.set_title("Permutation Importance — Final Model")
    ax.set_xlabel("Increase in MAE after permutation (tỷ VNĐ)")
    return _save_figure(fig, path)


def _plot_error_by_property(grouped: pd.DataFrame, path: Path) -> str:
    data = grouped.sort_values("MAE", ascending=True)
    fig, ax = plt.subplots(figsize=(7, 5))
    if data.empty:
        ax.text(0.5, 0.5, "No grouped error data", ha="center", va="center")
    else:
        ax.barh(data["property_type"], data["MAE"] / 1e9)
    ax.set_title("Prediction Error by Property Type")
    ax.set_xlabel("MAE (tỷ VNĐ)")
    return _save_figure(fig, path)


def _build_bt4_report(
    project_root: Path,
    audit: dict,
    comparison: pd.DataFrame,
    final_name: str,
    tuning: dict,
    importance: pd.DataFrame,
    error_property: pd.DataFrame,
    error_area: pd.DataFrame,
    figures: dict[str, str],
) -> str:
    best = comparison.loc[comparison["Model"] == final_name].iloc[0]
    baseline = comparison.loc[comparison["Model"] == "Dummy Median"].iloc[0]
    improvement = (baseline["Test_MAE"] - best["Test_MAE"]) / baseline["Test_MAE"] * 100.0
    top_features = ", ".join(importance.head(3)["feature"].astype(str).tolist())
    worst_property = "n/a"
    if not error_property.empty:
        row = error_property.iloc[0]
        worst_property = f"{row['property_type']} (MAE {row['MAE']/1e9:.2f} tỷ VNĐ)"
    worst_area = "n/a"
    if not error_area.empty:
        row = error_area.iloc[0]
        worst_area = f"{row['legacy_area']} (MAE {row['MAE']/1e9:.2f} tỷ VNĐ)"

    lines = [
        "# BÀI TẬP 4 — MÔ HÌNH HÓA & SO SÁNH KẾT QUẢ",
        "",
        "## 1. Business Question và dữ liệu đầu vào",
        "",
        "BQ01: Ước tính giá rao bán BĐS tại TP.HCM từ vị trí, loại hình và đặc điểm tin đăng CafeLand.",
        f"Input cleaned: `{Path(audit['source']).name}` — {audit['rows']:,} dòng.",
        f"Target: `{audit['target']}`. Feature model v1: {', '.join(audit['model_features'])}.",
        "",
        "## 2. Kiểm soát leakage và tiền xử lý",
        "",
        "- Chỉ fit imputer/scaler/encoder trên train thông qua scikit-learn Pipeline + ColumnTransformer.",
        "- Không dùng price_text, price_per_m2, price_billion, log_price_vnd, title, description, listing_id, url làm X.",
        "- OneHotEncoder dùng `handle_unknown='ignore'`; numeric dùng median imputation + StandardScaler.",
        "- Split 80/20 với random_state cố định; hyperparameter chỉ chọn bằng cross-validation trên train.",
        "",
        "## 3. Mô hình và đánh giá",
        "",
        "| Model | CV MAE (tỷ) | Test MAE (tỷ) | Test RMSE (tỷ) | Test R² |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, row in comparison.iterrows():
        lines.append(
            f"| {row['Model']} | {row['CV_MAE_mean']/1e9:.2f} | {row['Test_MAE']/1e9:.2f} | "
            f"{row['Test_RMSE']/1e9:.2f} | {row['Test_R2']:.3f} |"
        )

    lines += [
        "",
        f"Final model: **{final_name}**, được chọn theo CV MAE thấp nhất trong các model không phải baseline.",
        f"Holdout MAE = **{best['Test_MAE']/1e9:.2f} tỷ VNĐ**, RMSE = **{best['Test_RMSE']/1e9:.2f} tỷ VNĐ**, R² = **{best['Test_R2']:.3f}**.",
        f"So với Dummy Median, Test MAE giảm **{improvement:.1f}%**.",
        f"Best params: `{tuning[final_name].get('best_params', {})}`.",
        "",
        "## 4. Bias–variance / overfitting",
        "",
        f"Train MAE của final model = {best['Train_MAE']/1e9:.2f} tỷ; Test MAE = {best['Test_MAE']/1e9:.2f} tỷ. "
        f"Generalization gap = {best['Generalization_gap_MAE']/1e9:.2f} tỷ VNĐ.",
        "Learning curves được lưu riêng cho Ridge và mô hình phi tuyến để xem train/validation error khi tăng dữ liệu.",
        "",
        "## 5. Model interpretation và error analysis",
        "",
        f"Permutation importance trên holdout cho thấy các feature nổi bật: **{top_features}**.",
        f"Nhóm property_type có MAE cao nhất: **{worst_property}**.",
        f"Khu vực có MAE cao nhất trong holdout: **{worst_area}**.",
        "Các kết quả này phản ánh khả năng dự báo/association, không phải quan hệ nhân quả.",
        "",
        "## 6. Giá trị nghiệp vụ",
        "",
        "Mô hình có thể dùng như lớp tham khảo định giá nhanh từ dữ liệu giá rao CafeLand, hỗ trợ sàng lọc và so sánh ban đầu.",
        "Sai số phải được đọc theo đơn vị tỷ VNĐ và không có benchmark thẩm định độc lập trong bộ dữ liệu hiện tại, vì vậy không nên diễn giải là độ chính xác đủ cho quyết định giao dịch.",
        "",
        "## 7. Hạn chế",
        "",
        "- Target là giá rao, không phải giá giao dịch thực tế.",
        "- Feature vị trí hiện ở mức legacy_area; chưa có tọa độ/tiện ích chi tiết.",
        "- Card-only crawl làm thiếu các thuộc tính chi tiết như listing_date, bedrooms, legal_status.",
        "- area_m2 có area-definition risk ở một số nhà phố; cần theo dõi khi mở rộng model.",
        "- CafeLand có selection bias; kết quả không đại diện toàn bộ thị trường TP.HCM.",
        "- Không suy luận causal effect từ coefficient/feature importance.",
        "",
        "## 8. Artifacts",
        "",
    ]
    for name, path in figures.items():
        lines.append(f"- {name}: `{Path(path).as_posix()}`")

    lines += [
        "",
        "Model artifact: `models/best_price_model.joblib`.",
        "Metrics/table: `reports/modeling/`.",
        "Demo: `streamlit run app/app.py`.",
    ]
    text = "\n".join(lines) + "\n"
    report_path = project_root / "docs" / "BT4_submission.md"
    report_path.write_text(text, encoding="utf-8")
    draft_path = project_root / "reports" / "final_report" / "BT4_modeling_draft.md"
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(text, encoding="utf-8")
    return str(report_path)


def _write_slide_outline(project_root: Path, final_name: str, comparison: pd.DataFrame) -> str:
    best = comparison.loc[comparison["Model"] == final_name].iloc[0]
    outline = f"""# OUTLINE SLIDE — BÀI TẬP 4

1. Business Question: dự đoán giá rao bán BĐS TP.HCM.
2. Dataset & cleaned policy: 6.086 listing sau BT3.
3. Leakage policy & feature set model v1.
4. Pipeline preprocessing: train-only impute/scale/one-hot.
5. Baseline + Linear/Ridge.
6. Decision Tree + Random Forest và CV tuning.
7. Model comparison: MAE/RMSE/R².
8. Bias–variance: train/test gap + learning curves.
9. Error analysis theo loại hình/khu vực.
10. Model interpretation + 3 business insights.
11. Final model: {final_name} — Test MAE {best['Test_MAE']/1e9:.2f} tỷ VNĐ; R² {best['Test_R2']:.3f}.
12. Hạn chế, ứng dụng và Streamlit demo.
"""
    path = project_root / "presentation" / "BT4_slide_outline.md"
    path.write_text(outline, encoding="utf-8")
    return str(path)


def run_modeling(project_root: Path) -> dict:
    """Run BT4 end-to-end on the latest cleaned BT3 production dataset."""
    project_root = Path(project_root)
    config = _load_config(project_root)
    model_cfg = config.get("modeling", {})
    random_state = int(model_cfg.get("random_state", 42))
    test_size = float(model_cfg.get("test_size", 0.20))
    cv_folds = int(model_cfg.get("cv_folds", 5))

    feature_result = run_feature_stage(project_root)
    df = feature_result["dataframe"].copy()
    selected = feature_result["selected"]
    features = selected["numeric"] + selected["categorical"]
    if not features:
        raise ValueError("Không có feature hợp lệ cho modeling.")

    target = pd.to_numeric(df[TARGET_COLUMN], errors="coerce")
    valid_target = target.notna() & np.isfinite(target) & (target > 0)
    model_df = df.loc[valid_target].copy()
    y = pd.to_numeric(model_df[TARGET_COLUMN], errors="raise").astype(float)
    X = model_df[features].copy()

    train_idx, test_idx = train_test_split(
        model_df.index,
        test_size=test_size,
        random_state=random_state,
    )
    X_train = X.loc[train_idx]
    X_test = X.loc[test_idx]
    y_train = y.loc[train_idx]
    y_test = y.loc[test_idx]

    models, tuning = train_candidate_models(
        X_train,
        y_train,
        selected["numeric"],
        selected["categorical"],
        random_state=random_state,
        cv_folds=cv_folds,
        tune=True,
        include_random_forest=True,
    )
    comparison = evaluate_fitted_models(
        models,
        tuning,
        X_train,
        y_train,
        X_test,
        y_test,
        random_state=random_state,
        cv_folds=cv_folds,
    )
    final_name = choose_final_model(comparison)
    final_model = models[final_name]

    report_dir = project_root / "reports" / "modeling"
    report_dir.mkdir(parents=True, exist_ok=True)
    comparison_path = report_dir / "model_comparison.csv"
    comparison.to_csv(comparison_path, index=False, encoding="utf-8-sig")

    pred = build_prediction_frame(final_model, X_test, y_test, model_df)
    q1, q2 = y_train.quantile([0.33, 0.67]).tolist()
    pred["price_band"] = pd.cut(
        pred["actual_price"],
        bins=[-np.inf, q1, q2, np.inf],
        labels=["low", "mid", "high"],
    )
    prediction_path = report_dir / "holdout_predictions.csv"
    pred.to_csv(prediction_path, index=False, encoding="utf-8-sig")

    error_property = _group_error_table(pred, "property_type")
    error_area = _group_error_table(pred, "legacy_area")
    error_band = _group_error_table(pred, "price_band")
    error_property.to_csv(report_dir / "error_by_property_type.csv", index=False, encoding="utf-8-sig")
    error_area.to_csv(report_dir / "error_by_legacy_area.csv", index=False, encoding="utf-8-sig")
    error_band.to_csv(report_dir / "error_by_price_band.csv", index=False, encoding="utf-8-sig")
    pred.nlargest(30, "absolute_error").to_csv(
        report_dir / "largest_errors_top30.csv",
        index=False,
        encoding="utf-8-sig",
    )

    importance = permutation_importance_report(
        final_model,
        X_test,
        y_test,
        random_state=random_state,
        n_repeats=int(model_cfg.get("permutation_repeats", 8)),
    )
    importance.to_csv(report_dir / "permutation_importance.csv", index=False, encoding="utf-8-sig")

    ridge_coefficients = linear_coefficient_report(models["Ridge"])
    ridge_coefficients.to_csv(report_dir / "ridge_coefficients.csv", index=False, encoding="utf-8-sig")

    figures_dir = project_root / "reports" / "figures"
    figures = {
        "actual_vs_predicted": _plot_actual_vs_predicted(
            pred, figures_dir / "15_model_actual_vs_predicted.png"
        ),
        "residual_distribution": _plot_residual_distribution(
            pred, figures_dir / "16_model_residual_distribution.png"
        ),
        "residual_vs_predicted": _plot_residual_vs_predicted(
            pred, figures_dir / "17_model_residual_vs_predicted.png"
        ),
        "model_comparison": _plot_model_comparison(
            comparison, figures_dir / "18_model_comparison.png"
        ),
        "ridge_learning_curve": _plot_learning_curve(
            models["Ridge"],
            X_train,
            y_train,
            figures_dir / "19_ridge_learning_curve.png",
            "Learning Curve — Ridge Regression",
            random_state=random_state,
            cv_folds=cv_folds,
        ),
    }
    nonlinear_name = final_name if final_name in {"Decision Tree", "Random Forest"} else "Decision Tree"
    figures["nonlinear_learning_curve"] = _plot_learning_curve(
        models[nonlinear_name],
        X_train,
        y_train,
        figures_dir / "20_nonlinear_learning_curve.png",
        f"Learning Curve — {nonlinear_name}",
        random_state=random_state,
        cv_folds=cv_folds,
    )
    figures["permutation_importance"] = _plot_importance(
        importance,
        figures_dir / "21_permutation_importance.png",
    )
    figures["error_by_property_type"] = _plot_error_by_property(
        error_property,
        figures_dir / "22_error_by_property_type.png",
    )

    model_path = project_root / "models" / "best_price_model.joblib"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_model, model_path)

    best_row = comparison.loc[comparison["Model"] == final_name].iloc[0]
    categories = {
        col: sorted(model_df[col].dropna().astype(str).unique().tolist())
        for col in selected["categorical"]
    }
    numeric_ranges = {
        col: {
            "min": float(pd.to_numeric(model_df[col], errors="coerce").min()),
            "median": float(pd.to_numeric(model_df[col], errors="coerce").median()),
            "max": float(pd.to_numeric(model_df[col], errors="coerce").max()),
        }
        for col in selected["numeric"]
    }
    metadata = {
        "business_question": "Dự đoán giá rao bán BĐS tại TP.HCM",
        "target": TARGET_COLUMN,
        "input_dataset": str(feature_result["source"]),
        "input_rows": int(len(model_df)),
        "train_rows": int(len(train_idx)),
        "test_rows": int(len(test_idx)),
        "random_state": random_state,
        "cv_folds": cv_folds,
        "numeric_features": selected["numeric"],
        "categorical_features": selected["categorical"],
        "categories": categories,
        "numeric_ranges": numeric_ranges,
        "final_model": final_name,
        "selection_rule": "Lowest mean CV MAE among non-baseline candidates; holdout used for final evaluation.",
        "best_params": tuning[final_name].get("best_params", {}),
        "test_mae": float(best_row["Test_MAE"]),
        "test_rmse": float(best_row["Test_RMSE"]),
        "test_r2": float(best_row["Test_R2"]),
        "cv_mae_mean": float(best_row["CV_MAE_mean"]),
        "cv_mae_std": float(best_row["CV_MAE_std"]),
        "artifact": str(model_path),
        "disclaimer": "Ước tính từ giá rao CafeLand; không phải chứng thư thẩm định giá.",
    }
    metadata_path = project_root / "models" / "model_metadata.json"
    _write_json(metadata_path, metadata)

    metrics_payload = {
        "final_model": final_name,
        "comparison": comparison.to_dict(orient="records"),
        "tuning": tuning,
        "figures": figures,
    }
    metrics_path = report_dir / "model_metrics.json"
    _write_json(metrics_path, metrics_payload)

    audit = dict(feature_result["audit"])
    audit["source"] = str(feature_result["source"])
    report_path = _build_bt4_report(
        project_root,
        audit,
        comparison,
        final_name,
        tuning,
        importance,
        error_property,
        error_area,
        figures,
    )
    slide_outline_path = _write_slide_outline(project_root, final_name, comparison)

    return {
        "source": str(feature_result["source"]),
        "rows": int(len(model_df)),
        "features": features,
        "train_rows": int(len(train_idx)),
        "test_rows": int(len(test_idx)),
        "comparison_path": str(comparison_path),
        "metrics_path": str(metrics_path),
        "model_path": str(model_path),
        "metadata_path": str(metadata_path),
        "final_model": final_name,
        "final_metrics": {
            "MAE": float(best_row["Test_MAE"]),
            "RMSE": float(best_row["Test_RMSE"]),
            "R2": float(best_row["Test_R2"]),
        },
        "report_path": report_path,
        "slide_outline_path": slide_outline_path,
        "figures": figures,
        "gate_passed": (
            int((comparison["Model"] != "Dummy Median").sum()) >= 2
            and bool(comparison[["Test_MAE", "Test_RMSE", "Test_R2"]].notna().all().all())
            and model_path.exists()
            and len(figures) >= 8
        ),
    }


def run_report_stage(project_root: Path) -> dict:
    """Verify BT4 report/model artifacts already produced by the modeling stage."""
    project_root = Path(project_root)
    required = [
        project_root / "docs" / "BT4_submission.md",
        project_root / "models" / "best_price_model.joblib",
        project_root / "models" / "model_metadata.json",
        project_root / "reports" / "modeling" / "model_comparison.csv",
        project_root / "reports" / "modeling" / "model_metrics.json",
        project_root / "reports" / "modeling" / "MODELING_DATA_AUDIT.csv",
        project_root / "reports" / "modeling" / "feature_selection_report.csv",
        project_root / "notebooks" / "04_feature_engineering.ipynb",
        project_root / "notebooks" / "05_modeling.ipynb",
        project_root / "presentation" / "BT4_slide_outline.md",
        project_root / "app" / "app.py",
        project_root / "reports" / "figures" / "15_model_actual_vs_predicted.png",
        project_root / "reports" / "figures" / "20_nonlinear_learning_curve.png",
        project_root / "reports" / "figures" / "21_permutation_importance.png",
    ]
    missing = [str(path) for path in required if not path.exists()]
    return {"ready": not missing, "missing": missing, "artifacts": [str(p) for p in required]}
