from flask import Flask, request, jsonify, render_template
import requests
from PyPDF2 import PdfReader
from io import BytesIO
import csv
import re
import os
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

# Google Sheets API setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Path to your credentials file

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
spreadsheet_id = '1v4FnbxnHkUIG0MSo3aHRFFAVHa4l51hcXF_YlLq6PaI'  # Replace with your Google Spreadsheet ID

def download_pdf(url):
    response = requests.get(url)
    response.raise_for_status()  # Ensure the request was successful
    return BytesIO(response.content)

def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def search_keyword_in_pdfs(data, keywords):
    matched_entries = []
    for entry in data:
        url = entry['resume_link']
        user_id = entry['user_id']
        pdf_file = download_pdf(url)
        text = extract_text_from_pdf(pdf_file)
        for keyword in keywords:
            # Use regular expression to find exact phrase match
            if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
                matched_entries.append({'user_id': user_id, 'resume_link': url})
                break  # Stop checking other keywords if one matches
    return matched_entries

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and file.filename.endswith('.csv'):
        data = []
        stream = file.stream.read().decode("UTF8")
        csv_reader = csv.reader(stream.splitlines())
        for row in csv_reader:
            if row:  # skip empty rows
                data.append({'user_id': row[0], 'resume_link': row[1]})
        return jsonify(data), 200
    else:
        return jsonify({'error': 'File type not allowed'}), 400

@app.route('/search_keyword', methods=['POST'])
def search_keyword():
    data = request.json.get('data')
    keywords = request.json.get('keywords')
    if not keywords or not data:
        return jsonify({'error': 'Keywords and PDF URLs are required'}), 400
    matched_entries = search_keyword_in_pdfs(data, keywords)
    return jsonify(matched_entries), 200

@app.route('/save_results', methods=['POST'])
def save_results():
    results = request.json.get('results')
    if not results:
        return jsonify({'error': 'No results to save'}), 400

    try:
        service = build('sheets', 'v4', credentials=credentials)
        sheet = service.spreadsheets()

        # Prepare the data to be saved
        values = [['User ID', 'Resume Link', 'Checked']]
        for result in results:
            values.append([result['user_id'], result['resume_link'], 'TRUE' if result['checked'] else 'FALSE'])

        body = {
            'values': values
        }

        # Save the data to Google Sheets
        result = sheet.values().append(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A1',  # Adjust the range as needed
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()

        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
