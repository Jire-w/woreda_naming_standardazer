# standardizer.py
import pandas as pd
from rapidfuzz import process, fuzz
import os

# Define the relative path to the reference file
REFERENCE_FILE_PATH = os.path.join(os.path.dirname(__file__), "data", "reference.csv")

def load_reference_data():
    """
    Loads the reference data from the CSV file.
    
    Returns:
        DataFrame: The reference dataset.
    Raises:
        FileNotFoundError: If the reference file does not exist.
        pd.errors.EmptyDataError: If the file is empty.
    """
    if not os.path.exists(REFERENCE_FILE_PATH):
        raise FileNotFoundError(f"Reference file not found at: {REFERENCE_FILE_PATH}")
    
    try:
        ref_df = pd.read_csv(REFERENCE_FILE_PATH)
        ref_df.columns = ref_df.columns.str.strip().str.lower()
        required_cols = ['region', 'zone', 'woreda']
        if not all(col in ref_df.columns for col in required_cols):
            raise ValueError(f"Reference file must contain columns: {', '.join(required_cols)}")
        return ref_df
    except pd.errors.EmptyDataError:
        raise pd.errors.EmptyDataError("The reference file is empty.")

def match_and_correct(user_df, threshold=80, region_zone_threshold=90):
    """
    Corrects Woreda names in a user dataframe by fuzzy matching against a reference list.
    
    Parameters:
        user_df (DataFrame): The user's dataset to be corrected.
        threshold (int): The fuzzy matching threshold for woreda names.
        region_zone_threshold (int): The fuzzy matching threshold for region/zone.
        
    Returns:
        tuple: A tuple containing two DataFrames: the corrected DataFrame and a DataFrame of unmatched rows.
    """
    try:
        reference_df = load_reference_data()
    except (FileNotFoundError, ValueError) as e:
        # Re-raise the exception to be caught and handled by the Streamlit app
        raise e

    # Create a new DataFrame for the corrected data
    corrected_df = user_df.copy()
    corrected_df['standardized_region'] = ""
    corrected_df['standardized_zone'] = ""
    corrected_df['standardized_woreda'] = ""
    corrected_df['match_score'] = 0.0

    unmatched_rows = []

    # Create a concatenated key string for the reference data
    reference_df['concatenated_key'] = reference_df['region'] + "_" + reference_df['zone'] + "_" + reference_df['woreda']
    reference_choices = reference_df['concatenated_key'].tolist()

    for index, row in user_df.iterrows():
        user_region = str(row.get('region', '')).strip().lower()
        user_zone = str(row.get('zone', '')).strip().lower()
        user_woreda = str(row.get('woreda', '')).strip().lower()

        # Concatenate the user's data for a single fuzzy match lookup
        query_string = f"{user_region}_{user_zone}_{user_woreda}"

        best_match = process.extractOne(query_string, reference_choices, scorer=fuzz.token_set_ratio)

        if best_match and best_match[1] >= threshold:
            # Match found, get the original row from the reference data
            match_string, score, ref_index = best_match
            matched_ref_row = reference_df.iloc[ref_index]

            # Update the corrected_df with standardized names and score
            corrected_df.loc[index, 'standardized_region'] = matched_ref_row['region']
            corrected_df.loc[index, 'standardized_zone'] = matched_ref_row['zone']
            corrected_df.loc[index, 'standardized_woreda'] = matched_ref_row['woreda']
            corrected_df.loc[index, 'match_score'] = score
        else:
            # No match found, add to unmatched list
            unmatched_rows.append(row.to_dict())

    unmatched_df = pd.DataFrame(unmatched_rows)
    
    # Drop the temporary concatenated key column from the reference DataFrame before returning
    reference_df.drop(columns=['concatenated_key'], inplace=True)
    
    return corrected_df, unmatched_df
