from flask import Flask, jsonify, request, render_template
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Define the scope and authorize the client
scopes = [
    'https://www.googleapis.com/auth/spreadsheets'
]

try:
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scopes)
    client = gspread.authorize(creds)
except Exception as e:
    print(f"Error loading credentials: {e}")

# Google Sheet ID
sheet_id = "1ZAQLL-jYp36zUWP-fMLumA0GcvENrTNmx4ZQYX2Cg2I"

try:
    sheet = client.open_by_key(sheet_id)
    adult_info_worksheet = sheet.worksheet('AdultInfo')
    parent_guardian_worksheet = sheet.worksheet('Parent-GurdianInfo')  # Corrected worksheet name
except Exception as e:
    print(f"Error accessing the Google Sheet: {e}")

@app.route('/data', methods=['GET'])
def get_data():
    try:
        records = adult_info_worksheet.get_all_records()
        return jsonify(records)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/add_combined_data', methods=['POST'])
def add_combined_data():
    try:
        data = request.json
        adult_data = data['adultData']
        parent_data = data['parentData']
        print("Received data:", data)

        # Validate adult data
        required_adult_fields = ['Name', 'Gender', 'date-of-birth', 'year-of-joining', 'Contact', 'Email', 'Address', 'Ranks']
        for field in required_adult_fields:
            if field not in adult_data or not adult_data[field]:
                print(f"Missing or empty adult field: {field}")
                return jsonify({"error": f"Missing or empty field: {field}"}), 400

        # Validate parent data
        required_parent_fields = ['ParentName', 'ParentContact', 'Relationship', 'NextOfKin', 'NextOfKinContact']
        for field in required_parent_fields:
            if field not in parent_data or not parent_data[field]:
                print(f"Missing or empty parent field: {field}")
                return jsonify({"error": f"Missing or empty field: {field}"}), 400

        # Append adult data
        adult_info_worksheet.append_row([
            adult_data['Name'], adult_data['Gender'], adult_data['date-of-birth'],
            adult_data['year-of-joining'], adult_data['Contact'], adult_data['Email'],
            adult_data['Address'], adult_data['Ranks']
        ])

        # Append parent/guardian data
        parent_guardian_worksheet.append_row([
            parent_data['ParentName'], parent_data['ParentContact'], parent_data['Relationship'],
            parent_data['NextOfKin'], parent_data['NextOfKinContact']
        ])

        return jsonify({"status": "success", "data": data})
    except Exception as e:
        print(f"Error processing request: {e}")  # Log the specific error
        return jsonify({"error": str(e)}), 500

@app.route('/parent_info', methods=['GET'])
def get_parent_info():
    try:
        records = parent_guardian_worksheet.get_all_records()
        return jsonify(records)
    except Exception as e:
        print(f"Error fetching parent info: {e}")  # Log the specific error
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
