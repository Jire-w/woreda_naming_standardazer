import pandas as pd
from rapidfuzz import process, fuzz

def load_reference_data(path="data/reference.csv"):
    """
    Load and clean the reference data for region, zone, and woreda standardization.
    """
    df = pd.read_csv(path)
    
    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()

    # Ensure string values and clean whitespace
    for col in ['region', 'zone', 'woreda']:
        df[col] = df[col].astype(str).str.strip().str.lower()

    return df

def match_and_correct(user_df, reference_df, threshold=80, region_zone_threshold=90):
    """
    Match and correct Woreda names based on fuzzy matching against a reference dataset.
    
    Parameters:
        user_df (DataFrame): Input data with columns ['region', 'zone', 'woreda']
        reference_df (DataFrame): Cleaned reference data
        threshold (int): Match score threshold for woreda name
        region_zone_threshold (int): Match score threshold for region-zone pair
        
    Returns:
        corrected_df (DataFrame): Original dataframe with an added 'Standardized_Woreda' column
        unmatched_df (DataFrame): Rows that couldn't be matched
    """

    # Clean user input columns
    user_df.columns = user_df.columns.str.strip().str.lower()
    
    unmatched_rows = []
    corrected_woredas = []

    # Precompute region-zone strings from reference data
    reference_region_zone_pairs = (
        reference_df[['region', 'zone']]
        .drop_duplicates()
        .apply(lambda x: f"{x['region']}_{x['zone']}", axis=1)
        .tolist()
    )

    # Iterate through user rows
    for _, row in user_df.iterrows():
        user_region = str(row.get('region', '')).strip().lower()
        user_zone = str(row.get('zone', '')).strip().lower()
        user_woreda = str(row.get('woreda', '')).strip().lower()

        best_matched_ref_region = ''
        best_matched_ref_zone = ''
        current_woreda_match = ''

        # Step 1: Fuzzy match region-zone
        if user_region and user_zone:
            user_rz = f"{user_region}_{user_zone}"
            rz_match = process.extractOne(user_rz, reference_region_zone_pairs, scorer=fuzz.ratio)
            
            if rz_match:
                rz_best_match, rz_score, _ = rz_match
                if rz_score >= region_zone_threshold:
                    best_matched_ref_region, best_matched_ref_zone = rz_best_match.split('_', 1)

        # Step 2: Match woreda within the matched region and zone
        if best_matched_ref_region and best_matched_ref_zone and user_woreda:
            subset = reference_df[
                (reference_df['region'] == best_matched_ref_region) &
                (reference_df['zone'] == best_matched_ref_zone)
            ]

            if not subset.empty:
                woreda_choices = subset['woreda'].tolist()
                w_match = process.extractOne(user_woreda, woreda_choices, scorer=fuzz.token_set_ratio)
                
                if w_match:
                    best_woreda_match, w_score, _ = w_match
                    if w_score >= threshold:
                        current_woreda_match = best_woreda_match

        # Step 3: Append result
        if current_woreda_match:
            corrected_woredas.append(current_woreda_match.title())
        else:
            corrected_woredas.append('')
            unmatched_rows.append(row.to_dict())

    # Add corrected column
    user_df['Standardized_Woreda'] = corrected_woredas

    # Create DataFrame of unmatched rows
    unmatched_df = pd.DataFrame(unmatched_rows)

    return user_df, unmatched_df
