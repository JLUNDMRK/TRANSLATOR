import pytest
from app_extract import extract_codes

@pytest.mark.parametrize("text,dtc,comp", [
    ("DTC0101", ["DTC0101"], []),
    ("DTC 0101", ["DTC0101"], []),
    ("DTC-0101", ["DTC0101"], []),
    ("GMS2579", ["GMS2579"], []),
    ("EMS23AF", ["EMS23AF"], []),
    ("23AFh", ["23AF"], []),
    ("12345", ["12345"], []),
    ("23AF", ["23AF"], []),
    ("T123", [], ["T123"]),
    ("T-123", [], ["T123"]),
    ("T 123", [], ["T123"]),
    ("T_123", [], ["T123"]),
    ("GMS2579 och T229, T230 & T231", ["GMS2579"], ["T229","T230","T231"]),
    ("DTC0101 EMS23AF T123", ["DTC0101","EMS23AF"], ["T123"]),
    (None, [], []),
    ("", [], []),
    ("Ingen kod här", [], []),
])
def test_extract_codes(text, dtc, comp):
    result_dtc, result_comp = extract_codes(text)
    assert result_dtc == dtc
    assert result_comp == comp

def test_deduplication():
    text = "DTC0101 DTC0101 EMS23AF EMS23AF T123 T123"
    dtc, comp = extract_codes(text)
    assert dtc == ["DTC0101","EMS23AF"]
    assert comp == ["T123"]

def test_max_5_codes():
    text = "DTC0101 DTC0102 DTC0103 DTC0104 DTC0105 DTC0106 T123 T124 T125 T126 T127"
    dtc, comp = extract_codes(text)
    assert dtc[:5] == ["DTC0101","DTC0102","DTC0103","DTC0104","DTC0105"]
    assert comp[:5] == ["T123","T124","T125","T126","T127"]

def test_whitespace_and_commas():
    text = "T229, T230 , T231"
    dtc, comp = extract_codes(text)
    assert comp == ["T229","T230","T231"]
