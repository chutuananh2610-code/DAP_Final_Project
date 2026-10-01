from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dap_project.data.organize import quality_summary
from dap_project.pipelines.acquisition import run_acquisition, run_sample
from dap_project.pipelines.eda import run_eda
from dap_project.pipelines.modeling import run_feature_stage, run_modeling, run_report_stage


def show_progress(stage, current, total, page, added):
    percent = current / total * 100 if total else 0
    if stage == "search":
        print(
            f"\rTrang {page:<4} | +{added:<3} tin | "
            f"Đã crawl {current:,}/{total:,} ({percent:5.1f}%)",
            end="",
            flush=True,
        )
    elif stage == "detail":
        print(
            f"\rChi tiết | {current:,}/{total:,} ({percent:5.1f}%)",
            end="",
            flush=True,
        )


def run_crawler(args):
    start = time.perf_counter()
    print("\nBắt đầu crawl CafeLand...\n")
    result = run_acquisition(
        PROJECT_ROOT,
        max_records=args.max_records,
        enrich_details=args.enrich_details,
        progress=show_progress,
    )
    elapsed = time.perf_counter() - start
    raw_rows = result["raw_quality"]["rows"]
    processed_rows = result["processed_quality"]["rows"]
    print("\n")
    print("=" * 50)
    print(f"Raw records       : {raw_rows:,}")
    print(f"Processed records : {processed_rows:,}")
    print(f"Thời gian         : {elapsed / 60:.2f} phút")
    print(f"Gate Bài 2        : {'PASS' if result['gate_passed'] else 'FAIL'}")
    print("=" * 50)
    return result


def run_quality():
    files = sorted((PROJECT_ROOT / "data/processed").glob("hcm_realestate_*.csv"))
    files = [p for p in files if "cleaned" not in p.stem]
    if not files:
        raise SystemExit("Chưa có processed dataset.")

    import pandas as pd

    df = pd.read_csv(files[-1])
    print(json.dumps(quality_summary(df), ensure_ascii=False, indent=2))
    passed = len(df) >= 5000 and df.shape[1] >= 8
    print(f"\nGATE BÀI 2: {'PASS' if passed else 'FAIL'}")
    return passed


def print_eda_summary(result):
    d = result["diagnostics"]
    print("\n" + "=" * 58)
    print("BÀI TẬP 3 — EDA & TRỰC QUAN HÓA")
    print("=" * 58)
    print(f"Input rows        : {d['input_rows']:,}")
    print(f"Cleaned rows      : {d['cleaned_rows']:,}")
    print(f"Broker/profile URL: {d['structural_non_listing_rows']:,}")
    print(f"Robust outliers   : {d['robust_outlier_rows_removed']:,}")
    print(f"Property refined  : {d['property_type_refined_rows']:,}")
    print(f"Static charts     : {result['static_chart_count']}")
    print(f"Interactive charts: {result['interactive_chart_count']}")
    print(f"Report            : {result['report_path']}")
    print(f"GATE Bài 3        : {'PASS' if result['gate_passed'] else 'FAIL'}")
    print("=" * 58)


def print_feature_summary(result):
    audit = result["audit"]
    print("\n" + "=" * 58)
    print("FEATURE ENGINEERING — MODEL V1")
    print("=" * 58)
    print(f"Input             : {result['source']}")
    print(f"Rows              : {audit['rows']:,}")
    print(f"Target missing    : {audit['target_missing']:,}")
    print(f"Numeric features  : {', '.join(audit['numeric_features'])}")
    print(f"Categorical       : {', '.join(audit['categorical_features'])}")
    print(f"Feature report    : {result['selection_report_path']}")
    print("=" * 58)


def print_modeling_summary(result):
    metrics = result["final_metrics"]
    print("\n" + "=" * 58)
    print("BÀI TẬP 4 — MODELING & MODEL COMPARISON")
    print("=" * 58)
    print(f"Rows              : {result['rows']:,}")
    print(f"Train / Test      : {result['train_rows']:,} / {result['test_rows']:,}")
    print(f"Features          : {', '.join(result['features'])}")
    print(f"Final model       : {result['final_model']}")
    print(f"Test MAE          : {metrics['MAE']/1e9:.3f} tỷ VNĐ")
    print(f"Test RMSE         : {metrics['RMSE']/1e9:.3f} tỷ VNĐ")
    print(f"Test R²           : {metrics['R2']:.4f}")
    print(f"Model artifact    : {result['model_path']}")
    print(f"Report            : {result['report_path']}")
    print(f"GATE Bài 4        : {'PASS' if result['gate_passed'] else 'FAIL'}")
    print("=" * 58)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        choices=["sample", "acquisition", "quality", "eda", "features", "modeling", "report"],
        default="sample",
    )
    parser.add_argument("--max-records", type=int)
    parser.add_argument("--enrich-details", action="store_true")
    args = parser.parse_args()

    if args.stage == "sample":
        result = run_sample(PROJECT_ROOT)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.stage == "acquisition":
        run_crawler(args)
        return

    if args.stage == "quality":
        run_quality()
        return

    if args.stage == "eda":
        result = run_eda(PROJECT_ROOT)
        print_eda_summary(result)
        return

    if args.stage == "features":
        result = run_feature_stage(PROJECT_ROOT)
        print_feature_summary(result)
        return

    if args.stage == "modeling":
        result = run_modeling(PROJECT_ROOT)
        print_modeling_summary(result)
        return

    result = run_report_stage(PROJECT_ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
