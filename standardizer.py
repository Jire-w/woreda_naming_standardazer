# standardizer.py
import pandas as pd
from rapidfuzz import process, fuzz

def match_and_merge_two_datasets(df1, df2, key_cols, threshold=80):
    """
    Fuzzy matches and merges two datasets based on a list of key columns.

    Parameters:
        df1 (DataFrame): The first dataset (left side of the merge).
        df2 (DataFrame): The second dataset (right side of the merge).
        key_cols (list of str): The list of columns to use for matching.
        threshold (int): Match score threshold for the final key component.

    Returns:
        DataFrame: A merged dataframe with all columns from both inputs.
        DataFrame: A dataframe with unmatched rows from df1.
        DataFrame: A dataframe with unmatched rows from df2.
    """
    # Normalize key columns in both dataframes
    for df in [df1, df2]:
        df.columns = df.columns.str.strip().str.lower()
        for col in key_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.lower()

    # Rename columns in df2 to avoid conflicts during merge, keeping key_cols as-is
    df2_renamed = df2.copy()
    for col in df2.columns:
        if col not in key_cols:
            df2_renamed.rename(columns={col: f'dataset2_{col}'}, inplace=True)

    # Prepare for merging and tracking unmatched rows
    matched_rows = []
    unmatched_df1_rows = []
    matched_indices_df2 = set()

    # Create a list of full concatenated strings from df2 for fuzzy matching
    # Handle missing values by filling them with an empty string
    df2_choices = df2[key_cols].fillna('').apply(
        lambda x: '_'.join(x.astype(str)), axis=1
    ).tolist()

    # Iterate through df1 and find matches in df2
    for index1, row1 in df1.iterrows():
        # Create a single query string for the current row in df1
        query_string = '_'.join(str(row1.get(col, '')).strip().lower() for col in key_cols)

        # Find the best fuzzy match in df2
        best_match = process.extractOne(query_string, df2_choices, scorer=fuzz.token_set_ratio)

        if best_match and best_match[1] >= threshold:
            # Match found, get the original row from df2
            _, score, match_index2 = best_match
            
            # Check if this df2 row has already been matched
            if match_index2 not in matched_indices_df2:
                matched_row2 = df2_renamed.iloc[match_index2].to_dict()

                # Merge the two rows
                combined_row = {**row1.to_dict(), **matched_row2}
                matched_rows.append(combined_row)
                matched_indices_df2.add(match_index2)
            else:
                # This df2 row is a duplicate match, so df1 row is considered unmatched
                unmatched_df1_rows.append(row1.to_dict())
        else:
            # No good match found for this row in df1
            unmatched_df1_rows.append(row1.to_dict())

    # Create the final merged DataFrame
    merged_df = pd.DataFrame(matched_rows)
    unmatched_df1 = pd.DataFrame(unmatched_df1_rows)

    # Find unmatched rows in df2 by looking for indices that were not matched
    unmatched_indices_df2 = [i for i in range(len(df2)) if i not in matched_indices_df2]
    unmatched_df2 = df2.iloc[unmatched_indices_df2]

    return merged_df, unmatched_df1, unmatched_df2
