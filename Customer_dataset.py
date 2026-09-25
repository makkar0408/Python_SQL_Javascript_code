from pathlib import Path
from google.cloud import storage
import sys
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = BASE_DIR / "customer_data.csv"
OUTPUT_PATH = BASE_DIR / "customer_dataset_cleaned.csv"
OUTPUT_FILE = "customer_dataset_cleaned.csv"


def clean_customer_dataset(input_path: Path = DEFAULT_INPUT) -> pd.DataFrame:
	"""Read the data, tidy it up, and save the cleaned file."""

	print("reading", input_path)
	data = pd.read_csv(input_path)
	data.columns = data.columns.str.strip()

	# Get rid of rows that are exact copies.
	data = data.drop_duplicates().copy()

	# Clean the dates
	data["OrderDate"] = pd.to_datetime(
		data["OrderDate"], dayfirst=True, errors="coerce"
	)
	
	# Clean numeric columns.
	for column in ("OrderAmount", "Quantity"):
		data[column] = data[column].astype(str).str.strip().replace("One Hundred Pounds", 100)
		data[column] = data[column].astype(str).str.strip().replace("Three",3)
		data[column] = pd.to_numeric(data[column], errors="coerce")

   # Fill in missing values with some reasonable defaults.
	data["Quantity"] = data["Quantity"].fillna(4)
	data["OrderAmount"] = data["OrderAmount"].fillna(350)
	data["ProductID"] = data["ProductID"].fillna(1000)
	data["OrderDate"] = data["OrderDate"].fillna(pd.to_datetime("2023-09-01"))

	data["TotalOrderValue"] = data["OrderAmount"] * data["Quantity"]
	data["OrderDate"] = data["OrderDate"].dt.strftime("%Y-%m-%d")
	data.to_csv(OUTPUT_PATH, index=False)
	print(f"Cleaned dataset saved to {OUTPUT_PATH}")

	upload_to_gcs(OUTPUT_PATH)

	return data

def upload_to_gcs(filepath):
	"""Uploads a file to Google Cloud Storage."""
	client = storage.Client.from_service_account_json(
        r"C:\Users\gagan\OneDrive\Desktop\harpreet\Data Engineering\customer-data-pipeline-509614-957c89998d1f.json")

	bucket = client.bucket("customer-data-bucket-123")
	blob = bucket.blob(OUTPUT_FILE)
	blob.upload_from_filename(filepath)

	print(f"File {filepath} uploaded  in bucket {bucket}.")

if __name__ == "__main__":
	source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
	clean_customer_dataset(source)	
	
