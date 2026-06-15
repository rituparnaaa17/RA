
import requests
import pandas as pd
import io

def create_sample_excel():
    data = {
        "Reg.No": ["RA2111003010001", "RA2111003010002", "RA2111003010003", "RA2111003010004"],
        "Name": ["Student A", "Student B", "Student C", "Student D"],
        "Subject 1": ["95", "85", "45", "92"],
        "Subject 2": ["88", "75", "50", "80"],
        "Subject 3": ["90", "92", "40", "85"],
        "No. of subjects fail": [0, 0, 2, 0]
    }
    df = pd.DataFrame(data)
    
    # Save to buffer
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output

def test_workflow():
    base_url = "http://localhost:8000/api"
    
    print("1. Creating sample Excel...")
    excel_file = create_sample_excel()
    
    print("2. Uploading file...")
    files = {'file': ('test_report.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    data = {"dept": "CSE", "year": "3", "sem": "5", "section": "A", "faculty_advisor_name": "Test Faculty"}
    
    try:
        # Auth token would be needed in real scenario if we enforce it strictly, 
        # but my auth.py implementation checks for Bearer token. 
        # I need to generate a valid token or bypass for this test script?
        # The auth.py checks: jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
        # I should generate a token.
        
        from jose import jwt
        secret_key = "your-super-secret-key" # Default in config.py
        token = jwt.encode({"email": "faculty@srmist.edu.in"}, secret_key, algorithm="HS256")
        headers = {"Authorization": f"Bearer {token}"}
        
        res = requests.post(f"{base_url}/reports/upload", files=files, data=data, headers=headers)
        if res.status_code != 200:
            print(f"Upload failed: {res.text}")
            return
            
        report_id = res.json()["report_id"]
        print(f"   Upload successful. Report ID: {report_id}")
        
        print("3. Processing report...")
        res = requests.post(f"{base_url}/reports/{report_id}/process", headers=headers)
        if res.status_code != 200:
            print(f"Processing failed: {res.text}")
            return
        print("   Processing successful.")
        
        print("4. Fetching report data...")
        res = requests.get(f"{base_url}/reports/{report_id}", headers=headers)
        if res.status_code != 200:
             print(f"Fetch failed: {res.text}")
             return
             
        report_data = res.json()
        print(f"   Success! Fetched data for {report_data['meta']['dept']}.")
        print(f"   Pass Percentage: {report_data['computed']['overall_summary']['success_percent']}%")
        
        print("5. Checking Print View...")
        res = requests.get(f"{base_url}/reports/{report_id}/print", headers=headers)
        if res.status_code == 200:
            print("   Print view rendered successfully.")
        else:
            print(f"   Print view failed: {res.status_code}")

    except Exception as e:
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    test_workflow()
