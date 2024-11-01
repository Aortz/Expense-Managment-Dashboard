import pypdf
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import re
import os
import pandas as pd

class BankStatementOCR:
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
            print(f"Saving image to {image_path}")
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
                if re.search(account_summary_pattern, transaction):
                    match = re.search(account_summary_pattern, transaction)
                    total_withdrawal = match.group(1)
                    total_deposit = match.group(2)
                    final_balance = match.group(3)
                    extracted_data.append({
                        "Total Withdrawal": float(total_withdrawal.replace(',', '')),
                        "Total Deposit": float(total_deposit.replace(',', '')),
                        "Final Balance": float(final_balance.replace(',', ''))
                    })

        return extracted_data
    
    def extract_transaction_amount(self):
        array_of_transactions = self.extract_transactions()
        withdrawal_amount = []
        deposit_amount = []
        current_balance = 0
        # print(f"Number of transactions: {len(array_of_transactions)}")
        for i, transaction in enumerate(array_of_transactions):
            # print(f"Transaction {i}: {transaction}")
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

        # print(array_of_transactions[-1])
        # Add final balance to the last transaction
        print(f"After processing, the last transaction is: {array_of_transactions[-1]}")
        print(f"Second last transaction: {array_of_transactions[-2]}")
        if array_of_transactions[-2]["Account Balance"] == array_of_transactions[-1]["Final Balance"]:
            array_of_transactions[-2]["Total Withdrawal"] = array_of_transactions[-1]["Total Withdrawal"]
            array_of_transactions[-2]["Total Deposit"] = array_of_transactions[-1]["Total Deposit"]
        
        for i in range(len(array_of_transactions)-2):
            array_of_transactions[i]["Total Withdrawal"] = 0
            array_of_transactions[i]["Total Deposit"] = 0

        # Create DataFrame
        self.data_frame = pd.DataFrame(array_of_transactions[:-1])
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
    pdf_filename = "July_Accounts"
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
    print(extracted_data.tail())
    # Export the extracted data to a CSV file
    # csv_file = ocr_processor.export_to_csv()
    # print(ocr_processor.text_content)

    # Clean up temporary files
    ocr_processor.clean_up()
