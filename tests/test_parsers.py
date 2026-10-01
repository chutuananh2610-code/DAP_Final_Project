from pathlib import Path
import math

from dap_project.data.parsers import (
    parse_area_m2,
    infer_property_type,
    parse_detail_html,
    parse_price_vnd,
)


def test_parse_price():
    assert parse_price_vnd("3 tỷ 800 triệu") == 3_800_000_000
    assert parse_price_vnd("2,25 tỷ") == 2_250_000_000
    assert parse_price_vnd("850 triệu") == 850_000_000
    assert math.isnan(parse_price_vnd("Thương lượng"))


def test_parse_area():
    assert parse_area_m2("128.4m2") == 128.4
    assert parse_area_m2("71,04 m²") == 71.04


def test_parse_detail_fixture():
    html = Path("tests/fixtures/sample_detail.html").read_text(encoding="utf-8")
    rec = parse_detail_html(html, "https://example.test/sample-1234567.html")
    assert rec["listing_id"] == "26073032914"
    assert rec["price_vnd"] == 3_800_000_000
    assert rec["area_m2"] == 60
    assert rec["bedrooms"] == 2
    assert rec["property_type"] == "apartment"


def test_infer_property_type_extended_rules():
    assert infer_property_type("Cần bán CHCC 3PN trung tâm") == "apartment"
    assert infer_property_type("ĐẤT MẶT TIỀN diện tích 300m2") == "land"
    assert infer_property_type("Nhà đẹp 4 tầng hẻm xe hơi") == "house"
