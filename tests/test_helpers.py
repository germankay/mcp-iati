from mcp_iati import helpers as h


def test_activity_status_label_uses_iati_enum():
    assert h.activity_status_label("2") == "Implementation"


def test_activity_status_label_preserves_unknown_code():
    assert h.activity_status_label("999") == "999"


def test_transaction_type_label_uses_iati_enum():
    assert h.transaction_type_label("2") == "Out Commitment"


def test_format_amount_uses_two_decimal_places():
    assert h.format_amount(1234.5) == "1,234.50"


def test_build_table_applies_headers_and_formatters():
    table = h.build_table(
        [{"identifier": "IATI-1", "status": "2"}],
        [("identifier", "Identificador"), ("status", "Estado")],
        formatters={"status": h.activity_status_label},
    )

    assert table == [
        ["Identificador", "Estado"],
        ["IATI-1", "Implementation"],
    ]
