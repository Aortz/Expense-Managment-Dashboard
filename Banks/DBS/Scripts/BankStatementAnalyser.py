from pdf2image import convert_from_path
from PIL import Image
import pandas as pd
import re

class BankStatementAnalyser:
    def __init__(self, csv_path, file_name, temp_image_folder="temp_images"):
        self.csv_path = csv_path
        self.temp_image_folder = temp_image_folder
        self.file_name = file_name
        self.data_frame = None

    def import_csv(self):
        self.data_frame = pd.read_csv(self.csv_path)

    def export_csv(self, csv_path):
        self.data_frame.to_csv(csv_path, index=False)


    def description_regex(self, description):
        # Define regex patterns for different components
        date_pattern = r'\d{2} \w{3}'
        reference_pattern = r'\d{4} \d{7}'
        merchant_pattern = r'SHOPEE SINGAPORE|GPAY SINGAPORE'
        
        # Initialize categories
        transaction_type = 'Unknown'
        date = 'Unknown'
        reference_number = 'Unknown'
        merchant = 'Unknown'
        payment_method = 'Unknown'
        location = 'Unknown'
        
        # Extract date
        date_match = re.search(date_pattern, description)
        if date_match:
            date = date_match.group(0)
        
        # Extract reference number
        reference_match = re.search(reference_pattern, description)
        if reference_match:
            reference_number = reference_match.group(0)
        
        # Extract merchant
        merchant_match = re.search(merchant_pattern, description)
        if merchant_match:
            merchant = merchant_match.group(0)
            if 'GPAY' in merchant:
                payment_method = 'GPAY'
            if 'SHOPEE' in merchant:
                merchant = 'Shopee Singapore'
        
        # Extract payment method
        if 'GPAY' in description:
            payment_method = 'GPAY'
        
        # Extract location
        if 'SG' in description:
            location = 'Singapore (SG)'
        
        # Classify transaction type
        if 'DR-Debit Card' in description:
            transaction_type = 'Debit Card Purchase'
        else:
            transaction_type = 'Miscellaneous Expense'
        
        return {
            'Transaction Type': transaction_type,
            'Date': date,
            'Reference Number': reference_number,
            'Merchant': merchant,
            'Payment Method': payment_method,
            'Location': location
        }
    
    def classify_transactions(self):
        self.import_csv()
        transactions = self.data_frame['Description']
        classified_transactions = []
        for transaction in transactions:
            # print(f"Transaction: {transaction}")
            classified_transaction = self.description_regex(transaction.strip())
            classified_transactions.append(classified_transaction)
        
        for i, transaction in enumerate(classified_transactions):
            for key, value in transaction.items():
                # print(f"{key}: {value}")
                self.data_frame.loc[i, key] = value

        return self.data_frame

    

if __name__ == "__main__":
    csv_filename = "July_Accounts"
    csv_file = f"../CSV/{csv_filename}/{csv_filename}.csv"
    bank_analyser = BankStatementAnalyser(csv_path=csv_file, file_name=csv_filename)
    df = bank_analyser.classify_transactions()
    print(df.tail())