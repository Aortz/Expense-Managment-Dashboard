import pypdf
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import re
import os
import pandas as pd

class CreditCardStatementOCR:
    def __init__(self, pdf_path, file_name, temp_image_folder="temp_images"):
        self.pdf_path = pdf_path
        self.temp_image_folder = temp_image_folder
        self.file_name = file_name
        self.text_content = []
        self.data_frame = None

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
        images = convert_from_path(self.pdf_path, poppler_path=r"C:\Users\leeju\Downloads\Release-24.07.0-0\poppler-24.07.0\Library\bin", fmt="png")

        for i, image in enumerate(images):
            if not os.path.exists(os.path.join(self.temp_image_folder, self.file_name)):
                os.makedirs(os.path.join(self.temp_image_folder, self.file_name))
            image_path = os.path.join(self.temp_image_folder, self.file_name, f"page_{i + 1}.png")
            # print(f"Saving image to {image_path}")
            image.save(image_path, 'PNG')
            text = pytesseract.image_to_string(image, config='--psm 6 --oem 1')
            self.text_content.append(text)
            
    def clean_up(self):
        removal_file_path = os.path.join(self.temp_image_folder, self.file_name)
        for file_name in os.listdir(removal_file_path):
            if os.path.isfile(os.path.join(removal_file_path, file_name)):
                print(f"Removing file: {os.path.join(removal_file_path, file_name)}")
                os.remove(os.path.join(removal_file_path, file_name))
        os.rmdir(removal_file_path)
        os.rmdir(self.temp_image_folder)

    def extract_relevant_data(self, regex_patterns):
        extracted_data = []
        full_text = "\n".join(self.text_content)
        for label, pattern in regex_patterns.items():
            if label == "start_marker":
                start_marker = pattern
                start_index = re.search(start_marker, full_text).start()
            elif label == "end_marker":
                end_marker = pattern
                end_index = re.search(end_marker, full_text).start()
        extracted_data = full_text[start_index:end_index+len(end_marker)]    
        return extracted_data
        
    def classify_transactions(self):
        relevant_data = self.extract_relevant_data(regex_patterns)
        # Regular expression to match the start of a transaction (date format: "12 Jul")
        transaction_pattern = r'[0O]\d{1}\w{3}\s\d{2}[\s]?\w{3}'
        # second_transaction_pattern = r'\d{2}\w{3} \d{2} \w{3} (?=\d+\.\d{2})'

        # Split the data based on the transaction pattern
        transactions = re.split(f'(?={transaction_pattern})', relevant_data)

        # Remove any empty strings from the list
        transactions = [transaction.strip() for transaction in transactions if transaction.strip()]
        processed_transactions = []
        date_pattern = r'\d{2}\w{3}[\s]*'
        for transaction in transactions:
            # Substitute "O" with "0" at the beginning of the date if it matches
            fixed_transaction = re.sub(r'\bO(\d{1}\w{3})', r'0\1', transaction)
            # Add a space between the date and the month if it is missing
            # dates = re.findall(date_pattern, fixed_transaction)
            # print(f"Dates: {dates} for transaction: {fixed_transaction}")
            # if dates:
            #     if len(dates) > 1:
            #         fixed_transaction = re.sub(date_pattern, r'\1 \2', fixed_transaction)
            #     elif len(dates) == 1:
            #         fixed_transaction = re.sub(date_pattern, r'\1', fixed_transaction)
            processed_transactions.append(fixed_transaction)

        return processed_transactions
    
    def extract_transactions(self):
        transactions = self.classify_transactions()
        # Define patterns for extracting transaction details
        post_date_pattern = r'\d{2}\w{3}'
        transaction_date_pattern = r'\d{2}[\s]*\w{3}'
        amount_pattern = r'\d+\.\d{2}'
        # description_pattern = r'(?<=\d{2}\w{3}\s\d{2}[\s]?\w{3})(.+?)(?=\d+\.\d{2})'
        description_pattern = r'(?:\d{2}\w{3}\s\d{2}[\s]?\w{3})(.+?)(?=\d+\.\d{2})'
        # Regex pattern to capture everything after the second occurrence of a number with two decimal places
        second_description_pattern = r'(?:.*?\d+\.\d{2})(.+?)(?=Please note that you are bound|Total|$)' # (?!.*?Total)
        # account_summary_pattern = r'Total\s([\d,]+\.\d{2})\s([\d,]+\.\d{2})\s([\d,]+\.\d{2})'

        # Initialize variables to store extracted data
        extracted_data = []
        # Iterate over the transactions and extract relevant data
        for i, transaction in enumerate(transactions):
            # print(f"Transaction {i + 1}: {transaction}")
            # Check if the current item matches the regex pattern
            # print(f"Transaction {i} match post date: {re.search(post_date_pattern, transaction)}")
            # print(f"Transaction {i} match transaction date: {re.search(transaction_date_pattern, transaction)}")
            # print(f"Transaction {i} match amount: {re.search(amount_pattern, transaction)}")
            # print(f"Transaction {i} match description: {re.search(description_pattern, transaction)}")
            if not re.search(post_date_pattern, transaction) or not re.search(transaction_date_pattern, transaction) or not re.search(amount_pattern, transaction) or not re.search(description_pattern, transaction):
                continue  # Skip to the next iteration if the pattern is not found
            else:
                stripped_transaction = transaction.replace(',', '')  # Remove commas from the transaction
                # print(f"Transaction {i}: {stripped_transaction}")
                dates = re.findall(post_date_pattern, stripped_transaction)
                post_date = dates[0]
                # print(f"Post date for transaction {i}: {post_date}")
                dates = re.findall(transaction_date_pattern, stripped_transaction)
                transaction_date = dates[1]
                # print(f"Transaction date for transaction {i}: {transaction_date}")

                # Find all matches of the pattern in the current string
                matches = re.findall(amount_pattern, stripped_transaction)
                balance = matches[0]  # Get the last match (amount) from the list
                # print(f"Amount for transaction {i}: {balance}")

                # amount = re.search(amount_pattern, stripped_transaction).group()
                description = re.search(description_pattern, stripped_transaction).group(1).strip()
                match = re.search(second_description_pattern, stripped_transaction, re.DOTALL)
                if match:
                    description_after_second = match.group(1).strip()
                    description_after_second = re.sub(r'\n', ' ', description_after_second)
                    final_description = f"{description} {description_after_second}"
                else:
                    final_description = description
                # print(f"Description for transaction {i}: {final_description}")
                # print(f"Transaction {i+1}, Date: {date}, Balance: {balance}, Description: {final_description}")
                # Append the extracted data to the list
                extracted_data.append({
                    "Post Date": post_date,
                    "Transaction Date": transaction_date,
                    "Description": final_description,
                    "Transaction Amount": float(balance),
                })
                # if re.search(account_summary_pattern, transaction):
                #     match = re.search(account_summary_pattern, transaction)
                #     total_withdrawal = match.group(1)
                #     total_deposit = match.group(2)
                #     final_balance = match.group(3)
                #     extracted_data.append({
                #         "Total Withdrawal": float(total_withdrawal.replace(',', '')),
                #         "Total Deposit": float(total_deposit.replace(',', '')),
                #         "Final Balance": float(final_balance.replace(',', ''))
                #     })
        # print(f"Extracted data: {extracted_data}")
        return extracted_data
    
    def format_dates_in_dataframe(self, df):
        # Define the pattern to match "05Aug" and replace it with "05 Aug"
        pattern = r'(\d{2})(\w{3})'
        replacement = r'\1 \2'
        
        # Function to apply the regex substitution
        def format_date_column(column):
            return column.apply(lambda x: re.sub(pattern, replacement, x) if isinstance(x, str) else x)
        
        # Apply the function to the "Post Date" and "Transaction Date" columns
        if 'Post Date' in df.columns:
            df['Post Date'] = format_date_column(df['Post Date'])
        
        if 'Transaction Date' in df.columns:
            df['Transaction Date'] = format_date_column(df['Transaction Date'])

        return df
    
    def extract_transaction_amount(self):
        array_of_transactions = self.extract_transactions()
        # print(f"Array of transactions: {array_of_transactions}")
        total_outstanding_balance = 0
        # print(f"Number of transactions: {len(array_of_transactions)}")
        for transaction in array_of_transactions:
            total_outstanding_balance += transaction["Transaction Amount"]

        print(f"Total outstanding balance: {total_outstanding_balance}")
        
        # Create DataFrame
        self.data_frame = pd.DataFrame(array_of_transactions)
        # Format the dates in the DataFrame
        self.data_frame = self.format_dates_in_dataframe(self.data_frame)
        return self.data_frame
    
    def export_to_csv(self):
        if not os.path.exists(os.path.join("../CSV", self.file_name)):
            os.makedirs(os.path.join("../CSV", self.file_name))
        self.data_frame.to_csv(f"../CSV/{self.file_name}/{self.file_name}.csv", index=False)
        print(f"Exported data to CSV: ../CSV/{self.file_name}/{self.file_name}.csv")
        # return f"../CSV/{self.file_name}.csv"
    
    def process_bank_statement(self, use_ocr=False, regex_patterns=None, save_images=True):
        if use_ocr:
            self.perform_ocr_on_images()
        else:
            self.extract_text_from_pdf()

        if regex_patterns:
            return self.extract_transaction_amount()
        else:
            return "\n".join(self.text_content)


# Example usage
if __name__ == "__main__":
    pdf_filename = "Aug_Credit_Card_Statements"
    pdf_file = f"../PDF/{pdf_filename}.pdf"
    ocr_processor = CreditCardStatementOCR(pdf_path=pdf_file, file_name=pdf_filename)
    card_name = "Lady's Card".upper()
    # Regex patterns for extracting relevant data (e.g., dates, amounts, etc.)
    regex_patterns = {
        # "Dates": r"\d{2}/\d{2}/\d{4}",
        # "Amounts": r"\$\d{1,3}(,\d{3})*(\.\d{2})?",
        # "Account Numbers": r"Account Number: \d{4}-\d{4}-\d{4}-\d{4}"
        "start_marker": card_name,
        "end_marker": f"total balance for {card_name}".upper()
    }

    # Process the bank statement (OCR or text extraction)
    extracted_data = ocr_processor.process_bank_statement(use_ocr=True, regex_patterns=regex_patterns)
    # extracted_data = ocr_processor.process_bank_statement(use_ocr=False, regex_patterns=None)
    print(extracted_data.tail())
    # Export the extracted data to a CSV file
    csv_file = ocr_processor.export_to_csv()
    # print(ocr_processor.text_content)

    # Clean up temporary files
    ocr_processor.clean_up()
