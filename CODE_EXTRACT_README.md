# Code Extraction Module

## Overview

The `code_extract` module provides functionality to automatically extract **fault codes** and **component codes** from free-text descriptions in Excel files. This is useful for structuring unstructured claim or error data.

## Features

### Fault Code Detection
Supports multiple fault code formats:

- **DTC format**: `DTC0101`, `DTC-0101`, `DTC 0101`
- **Prefix codes**: `EMS23AF`, `ECA0101`, `BMS1A2B`, `ICL0505`
- **Hex with suffix**: `23AFh`, `23AFH`
- **Decimal (5 digits)**: `12345`
- **Hex (4 digits with A-F)**: `23AF`

### Component Code Detection
Detects component codes in T-series format:
- `T123`, `T-123`, `T 123`, etc. → normalized to `T123`

### Normalization
- Removes extra separators (dashes, spaces, underscores)
- Converts to uppercase for consistency
- Deduplicates codes (case-insensitive)
- Maintains order of first occurrence

## Usage

### Method 1: Python Code

```python
from src.pipeline.code_extract import extract_codes, augment_dataframe
import pandas as pd

# Extract codes from text
text = "Engine error DTC0101 affecting component T123"
codes = extract_codes(text)
print(codes)
# Output: {'fault_codes': ['DTC0101'], 'component_codes': ['T123']}

# Augment DataFrame
df = pd.read_excel('claims.xlsx')
result = augment_dataframe(df, text_col='description')
result.to_excel('claims_extracted.xlsx')
```

### Method 2: Command Line

```bash
# Basic usage
python -m src.pipeline.extract_cli --in input.xlsx --out output.xlsx --col description

# Custom options
python -m src.pipeline.extract_cli \
    --in claims.xlsx \
    --out claims_extracted.xlsx \
    --col "claim_text" \
    --max-codes 10 \
    --fill-value "N/A"

# Show help
python -m src.pipeline.extract_cli --help
```

### Method 3: Examples

```bash
python examples_code_extract.py
```

## Output Columns

When augmenting a DataFrame, the following columns are added:

- **fault_code_lista**: Comma-separated list of all fault codes
- **component_code_lista**: Comma-separated list of all component codes
- **fault_code_01 to fault_code_05**: Individual fault codes (up to 5, or configured max)
- **component_code_01 to component_code_05**: Individual component codes

Example:
```
| description                        | fault_code_lista    | component_code_lista |
|------------------------------------|-------------------|------------------|
| DTC0101 in component T123          | DTC0101           | T123             |
| EMS23AF and ECA0101 in T987        | EMS23AF, ECA0101  | T987             |
```

## API Reference

### `extract_codes(text, max_fault_codes=5, max_component_codes=5)`

Extract fault codes and component codes from text.

**Parameters:**
- `text` (str): Input text to extract codes from
- `max_fault_codes` (int): Maximum number of fault codes to return (default: 5)
- `max_component_codes` (int): Maximum number of component codes (default: 5)

**Returns:**
```python
{
    'fault_codes': ['DTC0101', 'EMS23AF', ...],
    'component_codes': ['T123', 'T987', ...]
}
```

### `augment_dataframe(df, text_col, max_codes=5, fill_value='')`

Augment DataFrame with extracted code columns.

**Parameters:**
- `df` (pd.DataFrame): Input DataFrame
- `text_col` (str): Name of column containing free text
- `max_codes` (int): Maximum codes per row (default: 5)
- `fill_value` (str): Value for empty code positions (default: '')

**Returns:**
- pd.DataFrame with new code columns added

## Regex Patterns

The module uses the following regex patterns for code detection (in priority order):

1. **DTC**: `\bDTC[\s\-_]?([0-9A-Fa-f][\s\-_0-9A-Fa-f]{3,5})\b`
2. **Prefix codes**: `\b([A-Z]{2,5})[\s\-_]?([0-9A-Fa-f]{3,6})\b` (with common word filtering)
3. **Hex with h-suffix**: `\b([0-9A-Fa-f]{3,6})[hH]\b`
4. **Decimal 5-digit**: `\b(\d{5})\b`
5. **Hex 4-digit (with A-F)**: `\b([0-9A-Fa-f]{4})\b` (only if contains A-F)
6. **Component**: `\bT[\s\-_]?(\d{3,})\b`

## Testing

Run the comprehensive test suite:

```bash
pytest tests/test_code_extract.py -v
```

Test coverage includes:
- Normalization helpers (4 tests)
- DTC code extraction (5 tests)
- Prefix code extraction (5 tests)
- Hex and decimal detection (7 tests)
- Component code extraction (6 tests)
- Mixed and complex texts (5 tests)
- Edge cases (8 tests)
- DataFrame augmentation (5 tests)
- Regression tests (3 tests)

**Total: 48 tests**

## Limitations

- Maximum 5 codes per type by default (configurable)
- Excludes common English words as false positives (code, data, mail, etc.)
- Requires structured patterns; very unusual code formats may not be detected
- No context awareness (e.g., can't distinguish between similar codes in different contexts)

## Future Enhancements (Step 2)

- [ ] Load and parse DTC definitions from XML files
- [ ] Create lookup map for DTC codes → descriptions/headings
- [ ] Augment output with DTC heading information
- [ ] Support for additional code formats
- [ ] Confidence scoring for extracted codes

## Examples

### Example 1: Swedish Text
```
Input: "Motorfelet DTC 0101 registreras tillsammans med komponenten T123."
Output: {'fault_codes': ['DTC0101'], 'component_codes': ['T123']}
```

### Example 2: Multiple Codes
```
Input: "System error DTC0102, EMS23AF, and component T987 affected"
Output: {
    'fault_codes': ['DTC0102', 'EMS23AF'],
    'component_codes': ['T987']
}
```

### Example 3: Various Formats
```
Input: "Errors: DTC-0101, 23AFh (hex), code 12345 (decimal), T-123 (component)"
Output: {
    'fault_codes': ['DTC0101', '23AF', '12345'],
    'component_codes': ['T123']
}
```

## Contributing

When adding new code formats or modifying patterns:
1. Add corresponding unit tests
2. Update this documentation
3. Ensure backward compatibility with existing tests
4. Test with Swedish and English text samples

## License

See main project LICENSE file.
