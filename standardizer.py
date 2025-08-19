# app.py
from flask import Flask, request, render_template, send_file
import pandas as pd
from io import BytesIO
from standardizer import match_and_merge  # Import the function from your new file
import yaml

app = Flask(__name__)

# Load configuration from config.yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/match', methods=['POST'])
def match_data():
    if 'file1' not in request.files or 'file2' not in request.files:
        return "Please upload both datasets.", 400

    file1 = request.files['file1']
    file2 = request.files['file2']

    try:
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)
    except Exception as e:
        return f"Error reading files. Please ensure they are in a valid CSV format. Error: {e}", 400

    # Get key columns from configuration
    key_columns = config['matching']['key_columns']
    threshold = config['matching']['threshold']
    multi_level_threshold = config['matching']['multi_level_threshold']

    # Call the core matching function from the standardizer module
    merged_df, unmatched_df1, unmatched_df2 = match_and_merge(
        df1,
        df2,
        key_columns,
        threshold,
        multi_level_threshold
    )

    # Prepare data for download
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        merged_df.to_excel(writer, sheet_name='Merged Data', index=False)
        unmatched_df1.to_excel(writer, sheet_name='Unmatched (Dataset 1)', index=False)
        unmatched_df2.to_excel(writer, sheet_name='Unmatched (Dataset 2)', index=False)

    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='merged_data.xlsx'
    )

if __name__ == '__main__':
    app.run(debug=True)
