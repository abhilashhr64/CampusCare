import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from src.main import app
from src.core.database import SessionApp, migrator_engine
from src.modules.identity.service import IdentityService, GoogleLoginRequest


def test_google_login_rejects_personal_email():
    """Rule NR-5 & Identity: Personal email addresses (@gmail.com, etc.) are strictly rejected.
    Users must authenticate with their official college email ID.
    """
    client = TestClient(app)
    payload = {
        "email": "student123@gmail.com",
        "full_name": "Test Student",
    }
    response = client.post("/api/v1/auth/google", json=payload)
    assert response.status_code == 400
    assert "personal email account" in response.json()["detail"]
    assert "college mail ID" in response.json()["detail"]


def test_google_login_existing_student_routes_to_user_dashboard():
    """College student signing in with college mail ID receives USER dashboard routing."""
    client = TestClient(app)
    payload = {
        "email": "aarav.sharma@apex.edu",
        "full_name": "Aarav Sharma",
    }
    response = client.post("/api/v1/auth/google", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_type"] == "USER"
    assert data["user"]["email"] == "aarav.sharma@apex.edu"
    assert data["user"]["is_email_verified"] is True
    assert "STUDENT" in data["user"]["roles"]
    assert data["session_token"] is not None


def test_google_login_admin_routes_to_admin_dashboard():
    """College admin signing in with college mail ID receives ADMIN dashboard routing."""
    client = TestClient(app)
    payload = {
        "email": "admin@apex.edu",
        "full_name": "Dr. S. K. Raman",
    }
    response = client.post("/api/v1/auth/google", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_type"] == "ADMIN"
    assert data["user"]["email"] == "admin@apex.edu"
    assert "COLLEGE_ADMIN" in data["user"]["roles"]


def test_google_login_new_college_email_auto_provisions_student_role():
    """Rule NR-5: A newly registered college email through Google OIDC auto-provisions as STUDENT.
    Verified email alone NEVER grants elevated staff or admin privileges.
    """
    client = TestClient(app)
    random_id = uuid.uuid4().hex[:6]
    new_email = f"freshman_{random_id}@apex.edu"
    payload = {
        "email": new_email,
        "full_name": "Freshman Student",
    }
    response = client.post("/api/v1/auth/google", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_type"] == "USER"
    assert data["user"]["email"] == new_email
    assert data["user"]["roles"] == ["STUDENT"]
    assert "COLLEGE_ADMIN" not in data["user"]["roles"]
    assert "DEPARTMENT_ADMIN" not in data["user"]["roles"]
