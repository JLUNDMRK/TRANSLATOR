"""
Example usage of the code_extract module.

This demo shows how to:
1. Extract codes from text using extract_codes()
2. Augment a DataFrame with extracted codes using augment_dataframe()
3. Save results to Excel
"""

from pathlib import Path
import pandas as pd
from src.pipeline.code_extract import extract_codes, augment_dataframe


def example_1_extract_from_text():
    """Example 1: Extract codes from a single text string."""
    print("=" * 60)
    print("EXAMPLE 1: Extract codes from text")
    print("=" * 60)
    
    text = """
    Motorfelet DTC0101 registreras ibland tillsammans med komponenten T123.
    Systemfel: EMS23AF och ECA0101 observeras också.
    Sekundär kod: 12345 registrerad under testning.
    Hex-kod 23AFh identifierad i loggfiler.
    """
    
    codes = extract_codes(text)
    
    print(f"Text:\n{text}\n")
    print(f"Extracted fault codes: {codes['fault_codes']}")
    print(f"Extracted component codes: {codes['component_codes']}")
    print()


def example_2_augment_dataframe():
    """Example 2: Augment DataFrame with extracted codes."""
    print("=" * 60)
    print("EXAMPLE 2: Augment DataFrame")
    print("=" * 60)
    
    # Create sample DataFrame
    df = pd.DataFrame({
        'claim_id': [1, 2, 3],
        'description': [
            'Engine error DTC0101 with component T123 affected',
            'System fault EMS23AF detected in ECA0101 subsystem',
            'Multiple issues: DTC0102, T987, and code 12345'
        ],
        'status': ['open', 'review', 'closed']
    })
    
    print("Original DataFrame:")
    print(df)
    print()
    
    # Augment with code extraction
    result = augment_dataframe(df, 'description', max_codes=5)
    
    print("Augmented DataFrame (showing code columns):")
    code_cols = [c for c in result.columns if 'code' in c.lower()]
    print(result[['claim_id', 'status'] + code_cols])
    print()


def example_3_create_sample_excel():
    """Example 3: Create and process sample Excel file."""
    print("=" * 60)
    print("EXAMPLE 3: Create and process Excel file")
    print("=" * 60)
    
    # Create sample data
    df = pd.DataFrame({
        'Claim No': ['CLM001', 'CLM002', 'CLM003', 'CLM004'],
        'Date': ['2025-01-15', '2025-01-16', '2025-01-17', '2025-01-18'],
        'Description': [
            'Motor error DTC 0101 och DTC-0102 registrerad',
            'Komponent T123 och T987 påverkas av EMS23AF',
            'System fel med kod 12345 och hex 23AFh',
            'Normal operation, no errors detected'
        ]
    })
    
    # Save to Excel
    input_file = Path('sample_claims.xlsx')
    df.to_excel(input_file, index=False)
    print(f"Created sample file: {input_file}")
    print(f"\nOriginal data ({len(df)} rows):")
    print(df[['Claim No', 'Description']])
    print()
    
    # Process with code extraction
    result = augment_dataframe(df, 'Description', max_codes=5)
    
    # Save output
    output_file = Path('sample_claims_extracted.xlsx')
    result.to_excel(output_file, index=False)
    
    print(f"Saved augmented file: {output_file}")
    print(f"\nExtracted codes summary:")
    print(result[['Claim No', 'fault_code_lista', 'component_code_lista']])
    print()


if __name__ == '__main__':
    example_1_extract_from_text()
    example_2_augment_dataframe()
    example_3_create_sample_excel()
    
    print("=" * 60)
    print("Examples complete!")
    print("\nTo use via CLI:")
    print("  python -m src.pipeline.extract_cli --in input.xlsx --out output.xlsx --col Description")
    print()
