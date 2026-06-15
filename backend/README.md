
# SRM Result Analysis Backend (v2)

Production-ready backend with MySQL support and simplified authentication.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r backend/requirements.txt
    ```

2.  **Environment Variables**:
    Set these in your environment or a `.env` file (if you add python-dotenv).
    
    -   `DATABASE_URL`: Connection string.
        -   **MySQL**: `mysql+pymysql://user:password@host/db_name`
        -   **SQLite (Default)**: `sqlite:///./result_analysis.db`
    -   `AUTH_SECRET_KEY`: The secret token your frontend must send.
        -   Default: `mysupersecret`

3.  **Run Server**:
    ```bash
    uvicorn backend.main:app --reload
    ```

## Authentication

All API calls (except `/`) require a Bearer token matching `AUTH_SECRET_KEY`.

**Header**:
`Authorization: Bearer mysupersecret`

### Example Curl
```bash
curl -X POST http://localhost:8000/api/reports/upload \
  -H "Authorization: Bearer mysupersecret" \
  -F "file=@./test.xlsx"
```

## Database (MySQL)
Ensure your MySQL server is running and you have created the database referenced in `DATABASE_URL`. The backend will attempt to create tables automatically (`Base.metadata.create_all`).

## API Endpoints
-   `POST /api/reports/upload` (Multipart)
-   `POST /api/reports/{id}/process`
-   `PUT /api/reports/{id}/edits` (JSON)
-   `GET /api/reports/{id}`
-   `GET /api/reports/{id}/print`
