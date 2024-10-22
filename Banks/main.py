from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import importlib
from werkzeug.utils import secure_filename
import traceback
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Configure your PostgreSQL connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/your_database')

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def convert_pdf(bank_name, pdf_path):
    try:
        if bank_name == "UOB":
            # Dynamically import the correct script
            module = importlib.import_module(f"{bank_name}.Scripts.BankStatementOCR")
            # Create an instance of BankStatementOCR
            ocr_processor = module.BankStatementOCR(pdf_path=pdf_path, file_name=os.path.basename(pdf_path))
            # Define regex patterns (you may want to make this configurable)
            regex_patterns = {
                "start_marker": "Account Transaction Details = Transaction Details",
                "end_marker": "End of Transaction Details"
            }
            
            # Process the bank statement
            result = ocr_processor.process_bank_statement(use_ocr=True, regex_patterns=regex_patterns)
            
            # Clean up temporary files
            ocr_processor.clean_up()
            
            return result
        elif bank_name == "Citi":
            # Dynamically import the correct script
            module = importlib.import_module(f"{bank_name}.Scripts.CreditCardStatementOCR")
            # Create an instance of CreditCardStatementOCR
            ocr_processor = module.CreditCardStatementOCR(pdf_path=pdf_path, file_name=os.path.basename(pdf_path))
            # Define regex patterns (you may want to make this configurable)
            regex_patterns = {
                "start_marker": "Account Transaction Details = Transaction Details",
                "end_marker": "End of Transaction Details"
            }
            
    except ImportError:
        print(f"Error: No script found for bank {bank_name}")
        return None
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return None

def upload_to_postgres(df, table_name):
    """
    Upload a pandas DataFrame to PostgreSQL after ensuring the Date column is not empty.
    
    :param df: pandas DataFrame to upload
    :param table_name: name of the table to create/update in PostgreSQL
    :return: True if successful, False otherwise
    """
    try:
        # Check if 'Date' column exists
        if 'Date' not in df.columns:
            print("Error: 'Date' column not found in the DataFrame")
            return False

        # print(df["Date"])

        # Remove rows where 'Date' is null or empty
        df_clean = df.dropna(subset=['Date'])

        # Check if any rows remain after removing null dates
        if df_clean.empty:
            print("Error: All rows have been removed due to null or empty dates")
            return False

        # Check if any dates were removed
        if len(df_clean) < len(df):
            print(f"Warning: {len(df) - len(df_clean)} rows were removed due to null or empty dates")

        # Ensure 'Date' column is in datetime format
        df_clean['Date'] = pd.to_datetime(df_clean['Date'], errors='coerce')

        # Remove any rows where date conversion failed
        df_clean = df_clean.dropna(subset=['Date'])

        if df_clean.empty:
            print("Error: No valid dates remain after conversion")
            return False

        engine = create_engine(DATABASE_URL)
        df_clean.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"Successfully uploaded {len(df_clean)} rows to PostgreSQL")
        return True
    except SQLAlchemyError as e:
        print(f"An error occurred while uploading to PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

@app.route('/convert', methods=['POST'])
def convert_pdf_api():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if 'bank' not in request.form:
            return jsonify({'error': 'Bank name not provided'}), 400
        
        bank_name = request.form['bank']
        
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            result = convert_pdf(bank_name, file_path)
            if result is not None:
                # Upload the DataFrame to PostgreSQL
                table_name = f"{bank_name.lower()}_transactions"
                if upload_to_postgres(result, table_name):
                    return jsonify({'message': 'Conversion successful and data uploaded to PostgreSQL'}), 200
                else:
                    return jsonify({'error': 'Conversion successful but failed to upload to PostgreSQL'}), 500
            else:
                return jsonify({'error': 'Conversion failed'}), 500
    except Exception as e:
        # Log the full stack trace of the error
        error_message = traceback.format_exc()
        print(f"Error processing file: {error_message}")
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)