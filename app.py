from flask import Flask, request, jsonify, render_template
import requests
from PyPDF2 import PdfReader, errors
from io import BytesIO
import csv
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

app = Flask(__name__)

# Google Sheets API setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Path to your credentials file

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
spreadsheet_id = '1v4FnbxnHkUIG0MSo3aHRFFAVHa4l51hcXF_YlLq6PaI'  # Replace with your Google Spreadsheet ID

# List of all possible technologies to check for in the resumes
ALL_TECHNOLOGIES = [
    'Python', 'Java', 'JavaScript', 'C#', 'C++', 'SQL', 'React.js', 'Node.js', 'HTML', 'CSS', 'Bootstrap', 'Express',
    'SQLite', 'Flexbox', 'MongoDB', 'OOPs', 'Redux', 'Git', 'SpringBoot', 'Data', 'Analytics', 'Manual', 'Testing',
    'Selenium', 'Testing', 'User', 'Interface', 'UI' 'XR', 'AI', 'ML', 'AWS', 'Cyber', 'Security', 'Data', 'Structures',
    'Algorithms', 'Django', 'Flask', 'Linux', 'NumPy', 'SAP', 'AngularJS', 'Flutter', 'UX design', 'jQuery', 'Angular',
    'REST', 'API', 'Calls'
]  # Add more as needed

def download_pdf(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BytesIO(response.content)
    except requests.RequestException as e:
        print(f"Error downloading PDF from {url}: {e}")
        return None

def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except errors.PdfReadError as e:
        print(f"Error reading PDF file: {e}")
        return ""

def search_keyword_in_pdfs(data, keywords):
    matched_entries = []
    total_keywords = len(keywords)
    for entry in data:
        url = entry['resume_link']
        user_id = entry['user_id']
        pdf_file = download_pdf(url)
        if not pdf_file:
            continue  # Skip if the PDF could not be downloaded
        
        text = extract_text_from_pdf(pdf_file)
        if not text:
            continue  # Skip if the text could not be extracted
        
        match_count = 0
        matched_technologies = []
        existing_technologies = [tech for tech in ALL_TECHNOLOGIES if re.search(r'\b' + re.escape(tech) + r'\b', text, re.IGNORECASE)]
        
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword).replace(' ', r'\s+') + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                match_count += 1
                matched_technologies.append(keyword)
        
        if match_count > 0:
            percentage = (match_count / total_keywords) * 100
            matched_entries.append({
                'user_id': user_id,
                'resume_link': url,
                'percentage': round(percentage, 2),
                'matched_technologies': matched_technologies,
                'existing_technologies': existing_technologies
            })
    
    matched_entries.sort(key=lambda x: x['percentage'], reverse=True)
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

        values = [['Timestamp', 'User ID', 'Resume Link', 'Percentage', 'Matched Technologies', 'Existing Technologies']]
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for result in results:
            values.append([
                timestamp, 
                result['user_id'], 
                result['resume_link'], 
                result['percentage'], 
                ', '.join(result['matched_technologies']),
                ', '.join(result['existing_technologies'])
            ])

        body = {
            'values': values
        }

        result = sheet.values().append(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A1',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()

        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
