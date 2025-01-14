

## Functions
- **User Registration:** Securely register users with username and password.
- **Login Authentication:** Generate JWT tokens for authenticated users.
- **File Upload:** Supports uploading `.jpeg` and `.jpg` files.
- **WebSocket Communication:** 
  - Real-time chat via WebSocket.
  - Video stream handling with base64-encoded image frames.
- **Session Management:** Ensures secure login and logout workflows.
- **Database Initialization:** SQLite-based user and file storage.

## Technologies Used
- FastAPI
- SQLite
- JWT (JSON Web Tokens)
- CORS Middleware
- OpenCV
- PIL (Pillow)
- Numpy
- Logging
- Python's `async` capabilities for WebSocket handling

## Prerequisites
- Python 3.9 or higher
- Virtual environment (recommended)
- SQLite (pre-installed with Python)

## Project Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the FastAPI application:
   ```bash
   uvicorn main:app --reload
   ```

## Endpoints
### User Endpoints
- **Register:** `POST /register`
  - Request body: `{ "username": "<username>", "password": "<password>" }`
  - Response: `{ "message": "User registered successfully" }`

- **Login:** `POST /api/user/login`
  - Request body: `{ "username": "<username>", "password": "<password>" }`
  - Response: `{ "message": "Correct password", "access_token": "<token>", "token_type": "bearer" }`

### File Endpoints
- **Upload Files:** `POST /api/user/upload-files`
  - Accepts: Multiple `.jpeg` or `.jpg` files.
  - Response: `{ "message": "<n> file(s) uploaded successfully" }`

### WebSocket Endpoints
- **Chat:** `ws://<host>:<port>/api/ws/chat`
  - Supports real-time text-based chat.

- **Video Stream:** `ws://<host>:<port>/api/ws/video`
  - Accepts base64-encoded image frames and processes them.

## Database Initialization
The database is automatically initialized with the following tables:
- **Users Table:** Stores `username` and `password`.
- **Files Table:** Stores `id`, `filename`, `content_type`, and `data`.

## Security Practices
- **JWT Authentication:** Protects sensitive endpoints.
- **Password Hashing:** Consider using `bcrypt` for secure password storage.
- **CORS Configuration:** Ensure only trusted origins in production.

## Logging
Logging is configured to provide insights into application events, such as WebSocket connections and errors.

## Future Enhancements
- Implement password hashing using `bcrypt`.
- Add support for other file types in uploads.
- Enhance WebSocket handling with ConnectionManager for broadcasting.
- Integrate unit tests for robust testing.

## Troubleshooting
- Ensure the virtual environment is activated to avoid global package conflicts.
- Confirm SQLite databases (`users.db` and `files.db`) are properly initialized.
