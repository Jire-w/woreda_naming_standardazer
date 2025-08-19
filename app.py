# standardizer.py
import pandas as pd
from rapidfuzz import process, fuzz

def match_and_merge_two_datasets(df1, df2, col_mapping1, col_mapping2, threshold=80):
    """
    Fuzzy matches and merges two datasets based on a list of key columns.
    
    Parameters:
        df1 (DataFrame): The first dataset (left side of the merge).
        df2 (DataFrame): The second dataset (right side of the merge).
        col_mapping1 (dict): A dictionary mapping required keys to actual column names in df1.
        col_mapping2 (dict): A dictionary mapping required keys to actual column names in df2.
        threshold (int): Match score threshold for the final key component.

    Returns:
        DataFrame: A merged dataframe with all columns from both inputs.
        DataFrame: A dataframe with unmatched rows from df1.
        DataFrame: A dataframe with unmatched rows from df2.
    """
    # Create copies of the dataframes to avoid modifying the originals
    df1_copy = df1.copy()
    df2_copy = df2.copy()
    
    # Standardize column names based on the provided mapping
    for req_col, actual_col in col_mapping1.items():
        if actual_col != req_col:
            df1_copy.rename(columns={actual_col: req_col}, inplace=True)
            df1_copy[req_col] = df1_copy[req_col].astype(str).str.strip().str.lower()
            
    for req_col, actual_col in col_mapping2.items():
        if actual_col != req_col:
            df2_copy.rename(columns={actual_col: req_col}, inplace=True)
            df2_copy[req_col] = df2_copy[req_col].astype(str).str.strip().str.lower()
    
    # Now, the key columns in both dataframes are standardized to the same name
    key_cols = list(col_mapping1.keys())
    
    # Rename columns in df2 to avoid conflicts during merge, keeping key_cols as-is
    df2_renamed = df2_copy.copy()
    for col in df2_renamed.columns:
        if col not in key_cols:
            df2_renamed.rename(columns={col: f'dataset2_{col}'}, inplace=True)

    # Prepare for merging and tracking unmatched rows
    matched_rows = []
    unmatched_df1_rows = []
    matched_indices_df2 = set()
    
    # Create a list of full concatenated strings from df2 for fuzzy matching
    df2_choices = df2_copy[key_cols].fillna('').apply(
        lambda x: '_'.join(x.astype(str)), axis=1
    ).tolist()

    # Iterate through df1 and find matches in df2
    for index1, row1 in df1_copy.iterrows():
        query_string = '_'.join(str(row1.get(col, '')).strip() for col in key_cols)

        best_match = process.extractOne(query_string, df2_choices, scorer=fuzz.token_set_ratio)

        if best_match and best_match[1] >= threshold:
            _, score, match_index2 = best_match
            if match_index2 not in matched_indices_df2:
                # Add original columns from df1
                combined_row = df1.iloc[index1].to_dict()
                
                # Add original columns from df2
                combined_row.update({f'dataset2_{col}': val for col, val in df2.iloc[match_index2].to_dict().items()})
                matched_rows.append(combined_row)
                matched_indices_df2.add(match_index2)
            else:
                unmatched_df1_rows.append(df1.iloc[index1].to_dict())
        else:
            unmatched_df1_rows.append(df1.iloc[index1].to_dict())

    merged_df = pd.DataFrame(matched_rows)
    unmatched_df1 = pd.DataFrame(unmatched_df1_rows)

    unmatched_indices_df2 = [i for i in range(len(df2)) if i not in matched_indices_df2]
    unmatched_df2 = df2.iloc[unmatched_indices_df2]

    return merged_df, unmatched_df1, unmatched_df2
