
from jose import jwt
from backend.config import config

def generate_valid_token(email="faculty@srmist.edu.in"):
    """
    Generates a valid JWT token for testing/dev purposes.
    """
    token = jwt.encode({"email": email}, config.SECRET_KEY, algorithm="HS256")
    return token

if __name__ == "__main__":
    token = generate_valid_token()
    print("\n=== GENERATED AUTH TOKEN ===")
    print(f"\n{token}\n")
    print("============================")
    print("Copy the above token and use it in the 'Authorize' button at http://127.0.0.1:8000/docs\n")
