"""
Code extraction module for fault codes and component codes from free text.

Handles extraction, normalization and deduplication of:
- Component codes (T123, T-123, T 123 → T123)
- Fault codes (DTC variants, prefix codes, hex, decimal)

Supports output to Excel with separate columns for each code.
"""

import re
from typing import Dict, List, Tuple, Optional
from collections import OrderedDict
import pandas as pd


# ============================================================================
# REGEX PATTERNS
# ============================================================================

# Component code: T followed by 3+ digits, with optional separators
COMPONENT_PATTERN = re.compile(r'\bT[\s\-_]?(\d{3,})\b', re.IGNORECASE)

# DTC pattern: DTC prefix with optional separators followed by 4-6 hex/decimal digits
# Also allows dashes within the code part: DTC-01-01 type patterns
DTC_PATTERN = re.compile(r'\bDTC[\s\-_]?([0-9A-Fa-f][\s\-_0-9A-Fa-f]{3,5})\b')

# Prefix-code pattern: 2-5 letter prefix followed by 3-6 alphanumeric characters
# Using word boundary and checking that the match is not a common English word
# Pattern matches: EMS23AF, ECA0101, BMS1A2B, ICL0505 (uppercase or lowercase)
# But may also match some common words like "code" - these are filtered in extraction logic
PREFIX_CODE_PATTERN = re.compile(r'\b([A-Z]{2,5})[\s\-_]?([0-9A-Fa-f]{3,6})\b', re.IGNORECASE)

# Hex with h/H suffix: 3-6 hex digits followed by h/H
HEX_SUFFIX_PATTERN = re.compile(r'\b([0-9A-Fa-f]{3,6})[hH]\b')

# Raw decimal: exactly 5 digits
DECIMAL_PATTERN = re.compile(r'\b(\d{5})\b')

# Raw hex: exactly 4 hex digits containing at least one A-F
RAW_HEX_4_PATTERN = re.compile(r'\b([0-9A-Fa-f]{4})\b')


# List of common English/Swedish words that should not be treated as fault code prefixes
EXCLUDED_PREFIXES = {'CODE', 'TEXT', 'MAIL', 'DATA', 'FILE', 'ITEM', 'LINE', 'FORM', 'NAME', 'TYPE', 'DATE', 'TIME', 'USER', 'PASS', 'WORD', 'INFO', 'TEST', 'DEMO', 'TEMP', 'FILE', 'PATH', 'ADDR'}


def _is_valid_prefix(prefix: str) -> bool:
    """Check if a prefix is a valid fault code prefix (not a common word)."""
    return prefix.upper() not in EXCLUDED_PREFIXES

def _normalize_component_code(code: str) -> str:
    """Normalize component code: remove spaces/dashes/underscores."""
    return re.sub(r'[\s\-_]+', '', code).upper()


def _normalize_fault_code(code: str, has_prefix: bool = False) -> str:
    """Normalize fault code: remove spaces/dashes/underscores."""
    normalized = re.sub(r'[\s\-_]+', '', code).upper()
    return normalized


def _is_hex(value: str) -> bool:
    """Check if a string value is valid hex."""
    try:
        int(value, 16)
        return True
    except ValueError:
        return False


def _contains_hex_letters(value: str) -> bool:
    """Check if string contains hex letters A-F."""
    return bool(re.search(r'[A-Fa-f]', value))


def _deduplicate_preserving_order(codes: List[str]) -> List[str]:
    """
    Remove duplicates while preserving order (case-insensitive).
    Returns the first occurrence of each unique code.
    """
    seen = {}
    result = []
    for code in codes:
        code_upper = code.upper()
        if code_upper not in seen:
            seen[code_upper] = True
            result.append(code)
    return result


# ============================================================================
# MAIN EXTRACTION LOGIC
# ============================================================================

def extract_codes(text: str, max_fault_codes: int = 5, max_component_codes: int = 5) -> Dict[str, List[str]]:
    """
    Extract fault codes and component codes from text.
    
    Processes text in priority order to avoid double-counting tokens:
    1. DTC tokens (DTC12345)
    2. Prefix codes (EMS23AF, ECA0101, etc.)
    3. Hex with h suffix (23AFh)
    4. Decimal 5 digits (12345)
    5. Hex 4 digits with A-F (23AF)
    6. Component codes (T123, T-123)
    
    Args:
        text: Input text to extract codes from
        max_fault_codes: Maximum number of fault codes to return (default 5)
        max_component_codes: Maximum number of component codes to return (default 5)
    
    Returns:
        Dictionary with keys:
            - 'fault_codes': List of unique fault codes (normalized)
            - 'component_codes': List of unique component codes (normalized)
    """
    if not text:
        return {'fault_codes': [], 'component_codes': []}
    
    # Keep track of matched positions to avoid double-counting
    matched_positions: Dict[Tuple[int, int], str] = {}
    fault_codes: List[str] = []
    component_codes: List[str] = []
    
    # Priority 1: DTC tokens
    for match in DTC_PATTERN.finditer(text):
        start, end = match.span()
        matched_positions[(start, end)] = 'dtc'
        code_part = re.sub(r'[\s\-_]+', '', match.group(1))  # Remove separators
        code = 'DTC' + code_part.upper()
        fault_codes.append(code)
    
    # Priority 2: Prefix codes (but skip if already matched as DTC)
    for match in PREFIX_CODE_PATTERN.finditer(text):
        start, end = match.span()
        # Check if this overlaps with already matched token
        if any(s <= start < e or s < end <= e for s, e in matched_positions.keys()):
            continue
        
        prefix = match.group(1).upper()
        code_part = match.group(2).upper()
        
        # Avoid matching component codes or invalid prefixes
        if prefix == 'T' or not _is_valid_prefix(prefix):
            continue
        
        # Limit to max codes before adding
        if len(fault_codes) >= max_fault_codes:
            break
        
        matched_positions[(start, end)] = 'prefix'
        code = prefix + code_part
        fault_codes.append(code)
    
    # Priority 3: Hex with h suffix
    for match in HEX_SUFFIX_PATTERN.finditer(text):
        start, end = match.span()
        if any(s <= start < e or s < end <= e for s, e in matched_positions.keys()):
            continue
        
        if len(fault_codes) >= max_fault_codes:
            break
        
        matched_positions[(start, end)] = 'hex_suffix'
        code = match.group(1).upper()
        fault_codes.append(code)
    
    # Priority 4: Decimal 5 digits
    for match in DECIMAL_PATTERN.finditer(text):
        start, end = match.span()
        if any(s <= start < e or s < end <= e for s, e in matched_positions.keys()):
            continue
        
        if len(fault_codes) >= max_fault_codes:
            break
        
        matched_positions[(start, end)] = 'decimal'
        code = match.group(1)
        fault_codes.append(code)
    
    # Priority 5: Hex 4 digits (only if contains A-F)
    for match in RAW_HEX_4_PATTERN.finditer(text):
        start, end = match.span()
        if any(s <= start < e or s < end <= e for s, e in matched_positions.keys()):
            continue
        
        code = match.group(1)
        if not _contains_hex_letters(code):
            continue
        
        if len(fault_codes) >= max_fault_codes:
            break
        
        matched_positions[(start, end)] = 'hex_4'
        fault_codes.append(code)
    
    # Extract component codes (separate process, doesn't compete with fault codes)
    for match in COMPONENT_PATTERN.finditer(text):
        code = 'T' + match.group(1)
        component_codes.append(_normalize_component_code(code))
    
    # Deduplicate while preserving order (case-insensitive)
    fault_codes = _deduplicate_preserving_order(fault_codes)
    component_codes = _deduplicate_preserving_order(component_codes)
    
    # Limit to max codes
    fault_codes = fault_codes[:max_fault_codes]
    component_codes = component_codes[:max_component_codes]
    
    return {
        'fault_codes': fault_codes,
        'component_codes': component_codes
    }


# ============================================================================
# DATAFRAME AUGMENTATION
# ============================================================================

def augment_dataframe(
    df: pd.DataFrame,
    text_col: str,
    max_codes: int = 5,
    fill_value: str = ''
) -> pd.DataFrame:
    """
    Augment DataFrame with extracted code columns.
    
    Adds new columns:
    - fault_code_lista: Comma-separated list of all fault codes
    - component_code_lista: Comma-separated list of all component codes
    - fault_code_01 to fault_code_05: Individual fault codes
    - component_code_01 to component_code_05: Individual component codes
    
    Args:
        df: Input DataFrame
        text_col: Name of the column containing free text
        max_codes: Maximum codes per row (default 5)
        fill_value: Value to use for empty code positions (default empty string)
    
    Returns:
        DataFrame with new columns added
    """
    df = df.copy()
    
    # Lists to accumulate results
    fault_code_lists = []
    component_code_lists = []
    fault_code_columns = {i: [] for i in range(1, max_codes + 1)}
    component_code_columns = {i: [] for i in range(1, max_codes + 1)}
    
    # Process each row
    for idx, row in df.iterrows():
        text = str(row[text_col]) if pd.notna(row[text_col]) else ''
        
        codes = extract_codes(text, max_fault_codes=max_codes, max_component_codes=max_codes)
        
        # Fault codes
        fault_codes = codes['fault_codes']
        fault_code_lists.append(', '.join(fault_codes))
        for i in range(1, max_codes + 1):
            fault_code_columns[i].append(fault_codes[i - 1] if i - 1 < len(fault_codes) else fill_value)
        
        # Component codes
        component_codes = codes['component_codes']
        component_code_lists.append(', '.join(component_codes))
        for i in range(1, max_codes + 1):
            component_code_columns[i].append(component_codes[i - 1] if i - 1 < len(component_codes) else fill_value)
    
    # Add columns to dataframe
    df['fault_code_lista'] = fault_code_lists
    df['component_code_lista'] = component_code_lists
    
    for i in range(1, max_codes + 1):
        df[f'fault_code_{i:02d}'] = fault_code_columns[i]
        df[f'component_code_{i:02d}'] = component_code_columns[i]
    
    return df


# ============================================================================
# STEP 2: XML DTC LOOKUP (STUBS)
# ============================================================================

def load_dtc_xml(xml_path: str) -> Optional[Dict[str, str]]:
    """
    Load DTC definitions from XML file.
    
    Expected XML structure (stub for now):
    <dtc_definitions>
        <dtc code="DTC0101">
            <heading>Engine Control Module Fault</heading>
            <description>...</description>
        </dtc>
    </dtc_definitions>
    
    Returns:
        Dictionary mapping code -> heading, or None if file not found.
        Stub implementation returns empty dict.
    
    TODO: Implement XML parsing using ElementTree or lxml
    """
    # TODO: Implement XML parsing
    # Example structure to return:
    # {
    #     'DTC0101': 'Engine Control Module Fault',
    #     'EMS23AF': 'Emission System Fault',
    # }
    return {}


def create_dtc_heading_map(dtc_database: Optional[Dict[str, str]]) -> Dict[str, str]:
    """
    Create a lookup map for DTC code -> heading.
    
    Args:
        dtc_database: Dictionary from load_dtc_xml() or similar
    
    Returns:
        Mapping of code (uppercase) to heading description
        
    TODO: This will be used in augment_with_dtc_descriptions()
    """
    if not dtc_database:
        return {}
    
    # Normalize keys to uppercase for case-insensitive lookup
    return {code.upper(): heading for code, heading in dtc_database.items()}


def augment_with_dtc_descriptions(
    df: pd.DataFrame,
    dtc_heading_map: Dict[str, str],
    fault_code_col: str = 'fault_code_lista'
) -> pd.DataFrame:
    """
    Add DTC heading/description columns based on extracted fault codes.
    
    Adds columns:
    - fault_code_01_heading, fault_code_02_heading, etc.
    
    Args:
        df: DataFrame with fault code columns
        dtc_heading_map: Mapping from code to heading (from create_dtc_heading_map)
        fault_code_col: Name of the fault code list column
    
    Returns:
        DataFrame with heading columns added
        
    TODO: Implement after XML loading is complete
    """
    # Placeholder for step 2
    return df
