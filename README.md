# GitHub Profile Viewer

A Django web application that searches GitHub users through the public GitHub REST API, displays their profile information and 10 most recently updated repositories, and enables logged-in users to bookmark profiles.

Built with a custom GitHub Dark theme using the project logo and Bootstrap 5.

---

## Features

- **GitHub Search (`/`)**: Search any valid GitHub username using a `GET` request (`?q=username`).
- **Profile Display**:
  - Avatar, full name, username handle (`@username`)
  - Bio, follower count, public repo count, and direct GitHub profile link
- **Repository Listing**:
  - 10 most recently updated public repositories
  - Name, link, description, language indicator with colored dots, and star count
- **Error Handling**: Friendly error banners for:
  - User not found
  - Rate limit exceeded (403/429)
  - Network timeouts (5s timeout)
  - Offline/no connection
- **Bookmarks (`/bookmarks/`)**:
  - Logged-in users can bookmark profiles (POST only)
  - Duplicate bookmarks are prevented per user (`unique_together = ('user', 'username')`)
  - Users can only view and delete their own bookmarks
  - **Saved Badge**: Indicates on search page if profile is already bookmarked
  - **Personal Notes**: Users can add and edit custom personal notes on any bookmarked profile
- **Authentication**:
  - Login (`/accounts/login/`)
  - Logout (`/accounts/logout/`)
  - Registration / Sign Up (`/signup/`)
- **Admin**:
  - `BookmarkedProfile` registered with `list_display` and `search_fields` at `/admin/`

---

## Setup & Run Instructions

### 1. Activate Virtual Environment
On Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```
Or on macOS / Linux:
```bash
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Migrations
```bash
python manage.py migrate
```

### 4. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 5. Run the Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## Running Tests
Run the automated test suite:
```bash
python manage.py test
```
