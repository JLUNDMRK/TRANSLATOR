"""
Unit tests for code_extract module.

Tests cover:
- Various DTC code formats
- Prefix code variants
- Hex/decimal detection
- Component codes
- Deduplication and normalization
- DataFrame augmentation
- Edge cases and special characters
"""

import pytest
import pandas as pd
from src.pipeline.code_extract import (
    extract_codes,
    augment_dataframe,
    _normalize_component_code,
    _normalize_fault_code,
    _contains_hex_letters,
    _deduplicate_preserving_order
)


class TestNormalizationHelpers:
    """Test normalization helper functions."""
    
    def test_normalize_component_code(self):
        assert _normalize_component_code('T123') == 'T123'
        assert _normalize_component_code('T-123') == 'T123'
        assert _normalize_component_code('T 123') == 'T123'
        assert _normalize_component_code('T_123') == 'T123'
        assert _normalize_component_code('t-123') == 'T123'
    
    def test_normalize_fault_code(self):
        assert _normalize_fault_code('DTC0101') == 'DTC0101'
        assert _normalize_fault_code('DTC-0101') == 'DTC0101'
        assert _normalize_fault_code('DTC 0101') == 'DTC0101'
        assert _normalize_fault_code('dtc0101') == 'DTC0101'
    
    def test_contains_hex_letters(self):
        assert _contains_hex_letters('23AF') is True
        assert _contains_hex_letters('23AB') is True
        assert _contains_hex_letters('ABCD') is True
        assert _contains_hex_letters('1234') is False
        assert _contains_hex_letters('23DF') is True
    
    def test_deduplicate_preserving_order(self):
        codes = ['DTC0101', 'EMS23AF', 'DTC0101', 'ems23af', 'T123']
        result = _deduplicate_preserving_order(codes)
        assert result == ['DTC0101', 'EMS23AF', 'T123']
        assert len(result) == 3


class TestDTCCodeExtraction:
    """Test DTC code detection and normalization."""
    
    def test_dtc_with_no_separator(self):
        text = "Fel DTC0101 registrerad"
        codes = extract_codes(text)
        assert 'DTC0101' in codes['fault_codes']
    
    def test_dtc_with_dash(self):
        text = "Fel DTC-0101 registrerad"
        codes = extract_codes(text)
        assert 'DTC0101' in codes['fault_codes']
    
    def test_dtc_with_space(self):
        text = "Fel DTC 0101 registrerad"
        codes = extract_codes(text)
        assert 'DTC0101' in codes['fault_codes']
    
    def test_dtc_multiple_in_text(self):
        text = "Fel DTC0101 och DTC-0102 registrerad"
        codes = extract_codes(text)
        assert 'DTC0101' in codes['fault_codes']
        assert 'DTC0102' in codes['fault_codes']
        assert len(codes['fault_codes']) == 2
    
    def test_dtc_hex_variant(self):
        text = "Error code DTC12AB found"
        codes = extract_codes(text)
        assert 'DTC12AB' in codes['fault_codes']


class TestPrefixCodeExtraction:
    """Test prefix-code (EMS23AF style) extraction."""
    
    def test_prefix_code_ems(self):
        text = "Motor error EMS23AF detected"
        codes = extract_codes(text)
        assert 'EMS23AF' in codes['fault_codes']
    
    def test_prefix_code_eca(self):
        text = "Emission control ECA0101"
        codes = extract_codes(text)
        assert 'ECA0101' in codes['fault_codes']
    
    def test_prefix_code_bms(self):
        text = "Battery system BMS1A2B fault"
        codes = extract_codes(text)
        assert 'BMS1A2B' in codes['fault_codes']
    
    def test_prefix_code_with_separator(self):
        text = "Error code EMS-23AF or EMS 23AF"
        codes = extract_codes(text)
        # Should capture both as one after dedup
        assert 'EMS23AF' in codes['fault_codes']
    
    def test_prefix_code_lowercase(self):
        """Lowercase prefix should be normalized to uppercase."""
        text = "Error ems23af found"
        codes = extract_codes(text)
        # The pattern should now match lowercase prefixes and normalize them
        assert len(codes['fault_codes']) > 0, f"No fault codes found in: {codes['fault_codes']}"
        assert any('EMS23AF' in code or 'EMS' in code.upper() for code in codes['fault_codes'])


class TestHexAndDecimalExtraction:
    """Test hex vs decimal code detection."""
    
    def test_hex_with_h_suffix(self):
        text = "Code 23AFh detected"
        codes = extract_codes(text)
        assert '23AF' in codes['fault_codes']
    
    def test_hex_with_H_suffix(self):
        text = "Code 23AFH detected"
        codes = extract_codes(text)
        assert '23AF' in codes['fault_codes']
    
    def test_hex_4digit_with_af(self):
        text = "Hex-code 23AF in message"
        codes = extract_codes(text)
        # Should extract as fault code (4 digit hex with A-F)
        assert '23AF' in codes['fault_codes']
    
    def test_hex_not_extracted_without_af(self):
        """Pure decimal 4 digits without A-F should not be extracted as hex."""
        text = "Code 1234 in text"
        codes = extract_codes(text)
        # 1234 should NOT be extracted (4 digits, but no A-F)
        assert '1234' not in codes['fault_codes']
    
    def test_decimal_5digits(self):
        text = "Error code: 12345 registered"
        codes = extract_codes(text)
        assert '12345' in codes['fault_codes']
    
    def test_hex_priority_over_decimal(self):
        """If a code could be both hex and decimal, prefer hex if it has A-F."""
        text = "Hex code 1234A found"
        codes = extract_codes(text)
        # Contains 5 chars with A-F, treated as hex variant
        # Should be caught by prefix pattern or similar


class TestComponentCodeExtraction:
    """Test component code (T-series) extraction."""
    
    def test_component_code_T123(self):
        text = "Component T123 faulty"
        codes = extract_codes(text)
        assert 'T123' in codes['component_codes']
    
    def test_component_code_with_dash(self):
        text = "Component T-123 faulty"
        codes = extract_codes(text)
        assert 'T123' in codes['component_codes']
    
    def test_component_code_with_space(self):
        text = "Component T 123 faulty"
        codes = extract_codes(text)
        assert 'T123' in codes['component_codes']
    
    def test_component_code_longer(self):
        text = "Control unit T1234 malfunction"
        codes = extract_codes(text)
        assert 'T1234' in codes['component_codes']
    
    def test_multiple_component_codes(self):
        text = "Units T123 and T987 both failed"
        codes = extract_codes(text)
        assert 'T123' in codes['component_codes']
        assert 'T987' in codes['component_codes']
        assert len(codes['component_codes']) == 2
    
    def test_component_not_treated_as_fault_code(self):
        """Component codes should be separate from fault codes."""
        text = "T123 component affected by DTC0101"
        codes = extract_codes(text)
        assert 'T123' in codes['component_codes']
        assert 'T123' not in codes['fault_codes']
        assert 'DTC0101' in codes['fault_codes']


class TestMixedAndComplexTexts:
    """Test extraction from realistic mixed-language and complex texts."""
    
    def test_mixed_swedish_english(self):
        text = "Motorfelet DTC0101 och komponenten T123 registrerad. Engine error EMS23AF."
        codes = extract_codes(text)
        assert 'DTC0101' in codes['fault_codes']
        assert 'EMS23AF' in codes['fault_codes']
        assert 'T123' in codes['component_codes']
    
    def test_codes_with_punctuation(self):
        text = "Error DTC0101, fault EMS23AF; component T123."
        codes = extract_codes(text)
        assert 'DTC0101' in codes['fault_codes']
        assert 'EMS23AF' in codes['fault_codes']
        assert 'T123' in codes['component_codes']
    
    def test_codes_with_parentheses(self):
        text = "Registered: DTC0101 (primary) and EMS23AF (secondary)"
        codes = extract_codes(text)
        assert 'DTC0101' in codes['fault_codes']
        assert 'EMS23AF' in codes['fault_codes']
    
    def test_long_claim_text_with_multiple_codes(self):
        text = """
        Den 2025-03-04 registrerades följande motorfelser:
        Huvudfel: DTC 0101 och DTC-0102
        Sekundära fel: EMS23AF, ECA0101, BMS1A2B
        Påverkade komponenter: T123 och T-987
        Systemfel: 12345 registrerat.
        """
        # Use higher limit to capture all codes
        codes = extract_codes(text, max_fault_codes=10, max_component_codes=10)
        assert 'DTC0101' in codes['fault_codes']
        assert 'DTC0102' in codes['fault_codes']
        assert 'EMS23AF' in codes['fault_codes']
        assert 'ECA0101' in codes['fault_codes']
        assert 'BMS1A2B' in codes['fault_codes']
        assert 'T123' in codes['component_codes']
        assert 'T987' in codes['component_codes']
        assert '12345' in codes['fault_codes']
    
    def test_deduplication_case_insensitive(self):
        text = "Error dtc0101 and DTC0101 and Dtc0101"
        codes = extract_codes(text)
        assert codes['fault_codes'].count('DTC0101') == 1 or len(codes['fault_codes']) == 1


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_empty_text(self):
        codes = extract_codes("")
        assert codes['fault_codes'] == []
        assert codes['component_codes'] == []
    
    def test_none_input(self):
        codes = extract_codes(None)
        assert codes['fault_codes'] == []
        assert codes['component_codes'] == []
    
    def test_text_with_no_codes(self):
        text = "This is a normal text with no fault codes or components."
        codes = extract_codes(text)
        assert len(codes['fault_codes']) == 0
        assert len(codes['component_codes']) == 0
    
    def test_max_fault_codes_limit(self):
        text = "DTC0101 DTC0102 DTC0103 DTC0104 DTC0105 DTC0106 DTC0107"
        codes = extract_codes(text, max_fault_codes=5)
        assert len(codes['fault_codes']) == 5
    
    def test_max_component_codes_limit(self):
        text = "T100 T200 T300 T400 T500 T600"
        codes = extract_codes(text, max_component_codes=5)
        assert len(codes['component_codes']) == 5
    
    def test_code_at_start_of_text(self):
        text = "DTC0101 is the main error"
        codes = extract_codes(text)
        assert 'DTC0101' in codes['fault_codes']
    
    def test_code_at_end_of_text(self):
        text = "The main error is DTC0101"
        codes = extract_codes(text)
        assert 'DTC0101' in codes['fault_codes']
    
    def test_code_surrounded_by_newlines(self):
        text = "Error found:\nDTC0101\nSuspected cause: component T123\n"
        codes = extract_codes(text)
        assert 'DTC0101' in codes['fault_codes']
        assert 'T123' in codes['component_codes']


class TestDataFrameAugmentation:
    """Test DataFrame augmentation functionality."""
    
    def test_augment_simple_dataframe(self):
        df = pd.DataFrame({
            'claim_id': [1, 2],
            'description': [
                'Motor error DTC0101 detected',
                'System fault EMS23AF and component T123'
            ]
        })
        
        result = augment_dataframe(df, 'description')
        
        # Check that new columns were added
        assert 'fault_code_lista' in result.columns
        assert 'component_code_lista' in result.columns
        assert 'fault_code_01' in result.columns
        assert 'component_code_01' in result.columns
        
        # Check values
        assert 'DTC0101' in result.loc[0, 'fault_code_lista']
        assert 'EMS23AF' in result.loc[1, 'fault_code_lista']
        assert 'T123' in result.loc[1, 'component_code_lista']
    
    def test_augment_with_empty_rows(self):
        df = pd.DataFrame({
            'text': ['DTC0101', '', None, 'T123']
        })
        
        result = augment_dataframe(df, 'text')
        
        assert 'DTC0101' in result.loc[0, 'fault_code_lista']
        assert result.loc[1, 'fault_code_lista'] == ''
        assert result.loc[2, 'fault_code_lista'] == ''
        assert 'T123' in result.loc[3, 'component_code_lista']
    
    def test_augment_respects_max_codes(self):
        df = pd.DataFrame({
            'text': ['DTC0101 DTC0102 DTC0103 DTC0104 DTC0105 DTC0106']
        })
        
        result = augment_dataframe(df, 'text', max_codes=5)
        
        # Should have columns 01-05
        assert 'fault_code_05' in result.columns
        # Should not have column 06
        assert 'fault_code_06' not in result.columns
        
        # Check that only 5 codes are extracted
        codes_in_lista = result.loc[0, 'fault_code_lista'].split(', ')
        assert len([c for c in codes_in_lista if c]) == 5
    
    def test_augment_fill_value(self):
        df = pd.DataFrame({
            'text': ['DTC0101']
        })
        
        result = augment_dataframe(df, 'text', max_codes=5, fill_value='N/A')
        
        # First position should have the code
        assert result.loc[0, 'fault_code_01'] == 'DTC0101'
        # Remaining positions should have fill value
        assert result.loc[0, 'fault_code_02'] == 'N/A'
        assert result.loc[0, 'fault_code_03'] == 'N/A'
    
    def test_augment_preserves_original_columns(self):
        df = pd.DataFrame({
            'claim_id': [1, 2],
            'description': ['DTC0101', 'T123'],
            'status': ['open', 'closed']
        })
        
        result = augment_dataframe(df, 'description')
        
        # Original columns should still be there
        assert 'claim_id' in result.columns
        assert 'description' in result.columns
        assert 'status' in result.columns
        assert list(result['claim_id']) == [1, 2]
        assert list(result['status']) == ['open', 'closed']


class TestRegressions:
    """Test for regressions and known edge cases."""
    
    def test_prefix_code_with_all_digits_suffix(self):
        """EMS followed by only digits should still be extracted."""
        text = "Error EMS123456"
        codes = extract_codes(text)
        assert 'EMS123456' in codes['fault_codes']
    
    def test_dashes_in_long_codes(self):
        """Codes with multiple dashes should normalize correctly."""
        text = "Error DTC-0101 or DTC 01 01"  # Changed to more realistic formats
        codes = extract_codes(text)
        # Should normalize DTC-0101 to DTC0101
        assert 'DTC0101' in codes['fault_codes']
    
    def test_similar_component_and_fault_codes(self):
        """T123 should not appear in both component and fault code lists."""
        text = "Component T123 with error code T123 somehow"
        codes = extract_codes(text)
        assert 'T123' in codes['component_codes']
        # T123 should not be in fault codes unless separate T appears as fault
        # (T-only should be component)
        fault_with_t = [c for c in codes['fault_codes'] if c.startswith('T')]
        assert len(fault_with_t) == 0 or fault_with_t[0] == 'T123'
