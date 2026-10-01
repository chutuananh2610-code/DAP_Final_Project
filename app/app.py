from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "best_price_model.joblib"
METADATA_PATH = PROJECT_ROOT / "models" / "model_metadata.json"

st.set_page_config(page_title="DAP BQ01 — Định giá nhanh", layout="centered")
st.title("Định giá nhanh BĐS TP.HCM")
st.caption("Demo Bài tập 4 — DAP Final Project, dữ liệu giá rao CafeLand")

if not MODEL_PATH.exists() or not METADATA_PATH.exists():
    st.error("Chưa có model artifact. Chạy: python scripts/run_all.py --stage modeling")
    st.stop()

model = joblib.load(MODEL_PATH)
metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))

numeric_features = metadata.get("numeric_features", [])
categorical_features = metadata.get("categorical_features", [])
categories = metadata.get("categories", {})
ranges = metadata.get("numeric_ranges", {})

inputs: dict[str, object] = {}
for feature in numeric_features:
    info = ranges.get(feature, {})
    default = float(info.get("median", 0.0))
    minimum = float(info.get("min", 0.0))
    maximum = float(info.get("max", max(default, 1.0)))
    label = "Diện tích (m²)" if feature == "area_m2" else feature
    inputs[feature] = st.number_input(
        label,
        min_value=max(0.0, minimum),
        max_value=maximum,
        value=default,
        step=1.0,
    )

for feature in categorical_features:
    options = categories.get(feature, [])
    label = {
        "property_type": "Loại hình BĐS",
        "legacy_area": "Quận/Huyện (ranh giới nghiên cứu)",
    }.get(feature, feature)
    inputs[feature] = st.selectbox(label, options=options)

if st.button("Ước tính giá", type="primary"):
    row = pd.DataFrame([inputs], columns=numeric_features + categorical_features)
    predicted = float(model.predict(row)[0])
    st.metric("Giá rao ước tính", f"{predicted / 1e9:,.2f} tỷ VNĐ")
    st.caption(
        "Đây là ước tính từ mô hình học trên giá rao CafeLand, "
        "không phải giá giao dịch và không phải chứng thư thẩm định giá."
    )

with st.expander("Thông tin mô hình"):
    st.write(f"Final model: {metadata.get('final_model')}")
    st.write(f"Holdout MAE: {metadata.get('test_mae', 0) / 1e9:.2f} tỷ VNĐ")
    st.write(f"Holdout RMSE: {metadata.get('test_rmse', 0) / 1e9:.2f} tỷ VNĐ")
    st.write(f"Holdout R²: {metadata.get('test_r2', 0):.3f}")
