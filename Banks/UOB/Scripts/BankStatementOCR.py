import pypdf
import pytesseract
import shutil
from pdf2image import convert_from_path
from PIL import Image
import re
import os
import pandas as pd
from datetime import datetime

class BankStatementOCR:
    def __init__(self, pdf_path, file_name, temp_image_folder="temp_images"):
        self.pdf_path = pdf_path
        self.temp_image_folder = temp_image_folder
        self.file_name = file_name
        self.text_content = []
        self.data_frame = None
        self.regex_patterns = None

        if not os.path.exists(temp_image_folder):
            os.makedirs(temp_image_folder)

    def extract_text_from_pdf(self):
        with open(self.pdf_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            for page in range(len(reader.pages)):
                page_obj = reader.pages[page]
                text = page_obj.extract_text()
                self.text_content.append(text)

    def perform_ocr_on_images(self):
        # Convert PDF pages to images and perform OCR on each image
        images = convert_from_path(self.pdf_path, poppler_path=r'/usr/bin/', fmt="png")

        # Create or clear the temporary folder for this file
        temp_file_folder = os.path.join(self.temp_image_folder, self.file_name)
        if os.path.exists(temp_file_folder):
            # Remove all contents of the folder
            self.clean_up()
        else:
            os.makedirs(temp_file_folder)

        for i, image in enumerate(images):
            image_path = os.path.join(temp_file_folder, f"page_{i + 1}.png")
            image.save(image_path, 'PNG')
            text = pytesseract.image_to_string(image, config='--psm 6 --oem 1')
            self.text_content.append(text)
            
    def clean_up(self):
        removal_file_path = os.path.join(self.temp_image_folder, self.file_name)
        for file_name in os.listdir(removal_file_path):
            file_path = os.path.join(removal_file_path, file_name)
            try:
                if os.path.exists(file_path):
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
        shutil.rmtree(self.temp_image_folder)

    def extract_relevant_data(self):
        extracted_data = []
        full_text = "\n".join(self.text_content)
        for label, pattern in self.regex_patterns.items():
            if label == "start_marker":
                start_marker = pattern
                start_index = re.search(start_marker, full_text).start()
            elif label == "end_marker":
                end_marker = pattern
                end_index = re.search(end_marker, full_text).start()
        extracted_data = full_text[start_index:end_index+len(end_marker)]    
        return extracted_data
        
    def classify_transactions(self):
        relevant_data = self.extract_relevant_data()
        # Regular expression to match the start of a transaction (date format: "12 Jul")
        transaction_pattern = r'\d{2} \w{3} (?=[A-Za-z])'

        # Split the data based on the transaction pattern
        transactions = re.split(f'(?={transaction_pattern})', relevant_data)

        # Remove any empty strings from the list
        transactions = [transaction.strip() for transaction in transactions if transaction.strip()]

        return transactions
    
    def extract_transactions(self):
        transactions = self.classify_transactions()
        # Define patterns for extracting transaction details
        date_pattern = r'\d{2} \w{3}'
        amount_pattern = r'\d+\.\d{2}'
        description_pattern = r'(?<=\d{2} \w{3} )(.+?)(?=\d+\.\d{2})'
        # Regex pattern to capture everything after the second occurrence of a number with two decimal places
        second_description_pattern = r'(?:.*?\d+\.\d{2}){2}(.+?)(?=Please note that you are bound|Total|$)' # (?!.*?Total)
        account_summary_pattern = r'Total\s([\d,]+\.\d{2})\s([\d,]+\.\d{2})\s([\d,]+\.\d{2})'

        # Initialize variables to store extracted data
        extracted_data = []
        # Iterate over the transactions and extract relevant data
        for i, transaction in enumerate(transactions):
            # print(f"Transaction {i + 1}: {transaction}")
            # Check if the current item matches the regex pattern
            if not re.search(date_pattern, transaction) or not re.search(amount_pattern, transaction) or not re.search(description_pattern, transaction):
                continue  # Skip to the next iteration if the pattern is not found
            else:
                stripped_transaction = transaction.replace(',', '')  # Remove commas from the transaction
                # print(f"Transaction: {stripped_transaction}")
                date = re.search(date_pattern, stripped_transaction).group()
                # Find all matches of the pattern in the current string
                matches = re.findall(amount_pattern, stripped_transaction)
                balance = matches[-1]  # Get the last match (amount) from the list
                # amount = re.search(amount_pattern, stripped_transaction).group()
                description = re.search(description_pattern, stripped_transaction).group().strip()
                match = re.search(second_description_pattern, stripped_transaction, re.DOTALL)
                if match:
                    description_after_second = match.group(1).strip()
                    description_after_second = re.sub(r'\n', ' ', description_after_second)
                    final_description = f"{description} {description_after_second}"
                else:
                    final_description = description
                # print(f"Transaction {i+1}, Date: {date}, Balance: {balance}, Description: {final_description}")
                # Append the extracted data to the list
                extracted_data.append({
                    "Date": date,
                    "Description": final_description,
                    "Account Balance": float(balance),
                })

        return extracted_data
    
    def process_dates(self):
        # First, ensure the 'Date' column exists
        if 'Date' not in self.data_frame.columns:
            raise ValueError("'Date' column not found in the DataFrame")

        # Convert 'Date' column to string type first to ensure consistent processing
        self.data_frame['Date'] = self.data_frame['Date'].astype(str)

        # Function to parse dates with flexible format
        def parse_date(date_string):
            date_formats = ["%d-%b", "%d %b", "%d/%m", "%d-%m", "%d.%m"]
            for fmt in date_formats:
                try:
                    date = datetime.strptime(date_string, fmt)
                    # If parsing succeeds, return the date with the current year
                    return date.replace(year=datetime.now().year)
                except ValueError:
                    continue
            # If all parsing attempts fail, return None
            return None

        # Apply the parse_date function to the 'Date' column
        self.data_frame['Date'] = self.data_frame['Date'].apply(parse_date)

        # Check for any remaining NaT values
        nat_count = self.data_frame['Date'].isna().sum()
        if nat_count > 0:
            print(f"Warning: {nat_count} date(s) could not be parsed.")

        # Optionally, you can drop rows with NaT dates
        # self.data_frame = self.data_frame.dropna(subset=['Date'])

        return self.data_frame
    
    def convert_pdf_to_df(self):
        array_of_transactions = self.extract_transactions()
        withdrawal_amount = []
        deposit_amount = []
        current_balance = 0
        # print(f"Number of transactions: {len(array_of_transactions)}")
        for i, transaction in enumerate(array_of_transactions):
            print(f"Transaction {i}: {transaction}")
            if i == 0:
                withdrawal_amount.append(0)
                deposit_amount.append(0)
                current_balance = float(transaction["Account Balance"])
            elif i >= len(array_of_transactions) - 1:
                pass
            else:
                # print(f"Currently on transaction {i}")
                if float(current_balance) > float(transaction["Account Balance"]):
                    withdrawal = float(current_balance) - float(transaction["Account Balance"]) 
                    withdrawal_amount.append(withdrawal)
                    deposit_amount.append(0)
                    current_balance = transaction["Account Balance"]
                else:
                    deposit = float(transaction["Account Balance"]) - float(current_balance)
                    deposit_amount.append(deposit)
                    withdrawal_amount.append(0)
                    current_balance = transaction["Account Balance"]

        for i in range(len(array_of_transactions)-1):
            array_of_transactions[i]["Withdrawal Amount"] = withdrawal_amount[i]
            array_of_transactions[i]["Deposit Amount"] = deposit_amount[i]
        

        # Create DataFrame
        self.data_frame = pd.DataFrame(array_of_transactions[:-1])
        self.data_frame = self.process_dates()
        return self.data_frame
    
    def export_to_csv(self):
        if not os.path.exists(os.path.join("../CSV", self.file_name)):
            os.makedirs(os.path.join("../CSV", self.file_name))
        self.data_frame.to_csv(f"../CSV/{self.file_name}/{self.file_name}.csv", index=False)
        # return f"../CSV/{self.file_name}.csv"
    
    def process_bank_statement(self, use_ocr=False, regex_patterns=None, save_images=True):
        if use_ocr:
            self.perform_ocr_on_images()
        else:
            self.extract_text_from_pdf()

        if regex_patterns:
            self.regex_patterns = regex_patterns
            return self.convert_pdf_to_df()
        else:
            return "\n".join(self.text_content)
        
        


# Example usage
if __name__ == "__main__":
    pdf_filename = "Aug_Accounts"
    pdf_file = f"../PDF/{pdf_filename}.pdf"
    ocr_processor = BankStatementOCR(pdf_path=pdf_file, file_name=pdf_filename)

    # Regex patterns for extracting relevant data (e.g., dates, amounts, etc.)
    regex_patterns = {
        # "Dates": r"\d{2}/\d{2}/\d{4}",
        # "Amounts": r"\$\d{1,3}(,\d{3})*(\.\d{2})?",
        # "Account Numbers": r"Account Number: \d{4}-\d{4}-\d{4}-\d{4}"
        "start_marker": "Account Transaction Details = Transaction Details",
        "end_marker": "End of Transaction Details"
    }

    # Process the bank statement (OCR or text extraction)
    # extracted_data = ocr_processor.perform_ocr_on_images(use_ocr=False, regex_patterns=regex_patterns)
    extracted_data = ocr_processor.process_bank_statement(use_ocr=True, regex_patterns=regex_patterns)
    # Export the extracted data to a CSV file
    csv_file = ocr_processor.export_to_csv()
    # print(ocr_processor.text_content)

