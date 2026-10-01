from dap_project.data.scope import infer_scope


SCOPE = {
    "Cầu Ông Lãnh": "Quận 1",
    "An Khánh": "TP Thủ Đức",
    "Lái Thiêu": "OUTER",
}


def test_scope_from_current_ward():
    status, ward, legacy = infer_scope(
        "Cầu Ông Lãnh, TP. Hồ Chí Minh", "", "", SCOPE
    )
    assert status == "confirmed_by_current_ward"
    assert legacy == "Quận 1"


def test_scope_from_legacy_text():
    status, ward, legacy = infer_scope(
        "TP. Hồ Chí Minh", "Bán nhà Hóc Môn", "", {}
    )
    assert status == "confirmed_by_legacy_text"
    assert legacy == "Huyện Hóc Môn"
