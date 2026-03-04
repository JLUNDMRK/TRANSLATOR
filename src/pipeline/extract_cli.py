"""
Command-line interface for code extraction from Excel files.

Usage:
    python -m src.pipeline.extract_cli --in input.xlsx --out output.xlsx --col "claim_text"
    python -m src.pipeline.extract_cli --help
"""

import argparse
import sys
from pathlib import Path
import pandas as pd

from code_extract import augment_dataframe


def main():
    """CLI entry point for code extraction."""
    parser = argparse.ArgumentParser(
        description='Extract fault and component codes from Excel files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Extract from 'description' column, save to output.xlsx:
    python -m src.pipeline.extract_cli --in claims.xlsx --out claims_extracted.xlsx --col description
  
  Extract from 'claim_text' column:
    python -m src.pipeline.extract_cli --in input.xlsx --out output.xlsx --col claim_text
        """
    )
    
    parser.add_argument(
        '--in', '--input',
        dest='input_file',
        required=True,
        help='Input Excel file path'
    )
    
    parser.add_argument(
        '--out', '--output',
        dest='output_file',
        required=True,
        help='Output Excel file path'
    )
    
    parser.add_argument(
        '--col', '--column',
        dest='text_column',
        default='description',
        help='Name of the text column to extract codes from (default: description)'
    )
    
    parser.add_argument(
        '--max-codes',
        dest='max_codes',
        type=int,
        default=5,
        help='Maximum number of codes to extract per type (default: 5)'
    )
    
    parser.add_argument(
        '--fill-value',
        dest='fill_value',
        default='',
        help='Value to use for empty code columns (default: empty string)'
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    if input_path.suffix.lower() not in ['.xlsx', '.xls']:
        print(f"Error: Input file must be Excel format (.xlsx or .xls)", file=sys.stderr)
        sys.exit(1)
    
    try:
        print(f"Reading Excel file: {input_path}")
        df = pd.read_excel(input_path)
        
        # Validate column exists
        if args.text_column not in df.columns:
            print(f"Error: Column '{args.text_column}' not found in Excel file", file=sys.stderr)
            print(f"Available columns: {', '.join(df.columns)}", file=sys.stderr)
            sys.exit(1)
        
        print(f"Processing {len(df)} rows from column '{args.text_column}'...")
        
        # Augment dataframe
        result_df = augment_dataframe(
            df,
            text_col=args.text_column,
            max_codes=args.max_codes,
            fill_value=args.fill_value
        )
        
        # Save output
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Writing output file: {output_path}")
        result_df.to_excel(output_path, index=False)
        
        # Print summary
        print("\n" + "="*60)
        print("EXTRACTION SUMMARY")
        print("="*60)
        print(f"Rows processed: {len(result_df)}")
        print(f"Columns added: {len(result_df.columns) - len(df.columns)}")
        
        # Count codes
        fault_code_counts = result_df['fault_code_lista'].str.split(', ').apply(len)
        component_code_counts = result_df['component_code_lista'].str.split(', ').apply(len)
        
        print(f"Total fault codes extracted: {fault_code_counts.sum()}")
        print(f"Total component codes extracted: {component_code_counts.sum()}")
        print(f"Rows with fault codes: {(fault_code_counts > 0).sum()}")
        print(f"Rows with component codes: {(component_code_counts > 0).sum()}")
        
        print("\nNew columns added:")
        new_cols = [c for c in result_df.columns if c not in df.columns]
        for col in new_cols[:10]:  # Show first 10
            print(f"  - {col}")
        if len(new_cols) > 10:
            print(f"  ... and {len(new_cols) - 10} more")
        
        print("\n✓ Done! Output saved to:", output_path)
        
    except Exception as e:
        print(f"Error during processing: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
