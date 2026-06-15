
import requests
import pandas as pd
import io
import time

BASE_URL = "http://localhost:8000/api"
AUTH_TOKEN = "mysupersecret"
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}

def create_valid_excel():
    data = {
        "Reg.No": ["RA211", "RA212"],
        "Name": ["Student A", "Student B"],
        "Maths": [95, 85],
        "Science": [90, 80],
        "No. of subjects fail": [0, 0]
    }
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame(data).to_excel(writer, index=False)
    output.seek(0)
    return output

def create_blank_excel():
    data = {"Reg.No": [], "Name": [], "Maths": [], "No. of subjects fail": []}
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame(data).to_excel(writer, index=False)
    output.seek(0)
    return output

def create_irrelevant_excel():
    data = {"Col1": [1, 2], "Col2": [3, 4]} # Missing Reg.No
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame(data).to_excel(writer, index=False)
    output.seek(0)
    return output

def test_full_flow():
    print("\n--- TEST: UPLOAD PRE-REQUISITES (MySQL & Running Server) ---")
    print("Assuming server running on localhost:8000 and DB is ready (SQLite or MySQL).")

    # 1. Test Auth Failure
    print("\n[1] Testing Auth Failure...")
    r = requests.get(f"{BASE_URL}/reports/1", headers={"Authorization": "Bearer wrong"})
    if r.status_code == 401:
        print("    PASS: Rejected invalid token.")
    else:
        print(f"    FAIL: Expected 401, got {r.status_code}")

    # 2. Upload Valid File
    print("\n[2] Uploading VALID File...")
    files = {'file': ('valid.xlsx', create_valid_excel(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    data = {"dept": "MECH"}
    r = requests.post(f"{BASE_URL}/reports/upload", files=files, data=data, headers=HEADERS)
    if r.status_code == 200:
        rid = r.json()['report_id']
        print(f"    PASS: Uploaded, ID={rid}")
        
        # Process It
        print("    Processing...")
        r2 = requests.post(f"{BASE_URL}/reports/{rid}/process", headers=HEADERS)
        if r2.status_code == 200:
            print("    PASS: Processed.")
        else:
            print(f"    FAIL: Processing failed: {r2.text}")
    else:
        print(f"    FAIL: Upload failed {r.text}")

    # 3. Upload Blank File (Should succeed with empty report)
    print("\n[3] Uploading BLANK File...")
    files = {'file': ('blank.xlsx', create_blank_excel(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    r = requests.post(f"{BASE_URL}/reports/upload", files=files, data={"dept": "CSE"}, headers=HEADERS)
    
    if r.status_code == 200:
        rid = r.json()['report_id']
        print(f"    PASS: Uploaded Blank, ID={rid}")
        
        # Process
        r2 = requests.post(f"{BASE_URL}/reports/{rid}/process", headers=HEADERS)
        if r2.status_code == 200:
            print("    PASS: Processed Blank (Graceful handling).")
            # Verify data is empty structure
            r3 = requests.get(f"{BASE_URL}/reports/{rid}", headers=HEADERS)
            res = r3.json()
            if res['computed']['overall_summary']['total_students'] == 0:
                 print("    PASS: Validated empty computation.")
            else:
                 print("    FAIL: Computed data not empty.")
        else:
            print(f"    FAIL: Processing blank failed {r2.text}")
    else:
        print(f"    FAIL: Upload blank failed {r.text}")

    # 4. Upload Irrelevant File (Should fail processing)
    print("\n[4] Uploading IRRELEVANT File...")
    files = {'file': ('bad.xlsx', create_irrelevant_excel(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    r = requests.post(f"{BASE_URL}/reports/upload", files=files, data={"dept": "IT"}, headers=HEADERS)
    rid = r.json()['report_id']
    
    # Process - Expect 400
    r2 = requests.post(f"{BASE_URL}/reports/{rid}/process", headers=HEADERS)
    if r2.status_code == 400:
        print(f"    PASS: Correctly rejected irrelevant file. Msg: {r2.json()['detail']}")
    else:
        print(f"    FAIL: Expected 400, got {r2.status_code}")

if __name__ == "__main__":
    try:
        test_full_flow()
    except Exception as e:
        print(f"Test crashed: {e}")
