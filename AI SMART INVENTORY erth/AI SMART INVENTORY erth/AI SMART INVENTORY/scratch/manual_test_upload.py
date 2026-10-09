import requests

url = "http://localhost:8000/api/v1/ingestion/upload"
files = {
    'sales_file': open('data/sales_history.csv', 'rb'),
    'inventory_file': open('data/inventory.csv', 'rb'),
    'suppliers_file': open('data/suppliers.csv', 'rb')
}
response = requests.post(url, files=files)
print(response.status_code)
print(response.json())
