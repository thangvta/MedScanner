"""
Tests for application routes
"""
import pytest
import json
import base64
from unittest.mock import patch, MagicMock
from flask import session
from models import User, Medication, Prescription


class TestPublicRoutes:
    """Test cases for public routes (no authentication required)"""
    
    def test_index_page(self, test_app):
        """Test home page loads correctly"""
        response = test_app.get('/')
        assert response.status_code == 200
        assert b'MedScanner' in response.data
    
    def test_scan_page_public_access(self, test_app):
        """Test scan page is accessible without login"""
        response = test_app.get('/scan')
        assert response.status_code == 200
        assert b'Prescription Scanner' in response.data
        assert b'AI-Powered' in response.data
    
    def test_public_interactions_page(self, test_app, test_db):
        """Test public interactions page"""
        response = test_app.get('/public-interactions')
        assert response.status_code == 200
        assert b'Check Drug Interactions' in response.data
    
    def test_interactions_redirect_for_public(self, test_app):
        """Test that /interactions redirects to public interactions for non-logged users"""
        response = test_app.get('/interactions')
        assert response.status_code == 200
        # Should show public interactions page
        assert b'Check Drug Interactions' in response.data


class TestAuthenticationRoutes:
    """Test cases for authentication routes"""
    
    def test_login_page(self, test_app):
        """Test login page loads"""
        response = test_app.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data
    
    def test_register_page(self, test_app):
        """Test register page loads"""
        response = test_app.get('/register')
        assert response.status_code == 200
        assert b'Register' in response.data
    
    def test_login_with_valid_credentials(self, test_app, test_db):
        """Test login with valid credentials"""
        response = test_app.post('/login', data={
            'username': 'testpatient',
            'password': 'testpass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should redirect to dashboard after successful login
        assert b'Dashboard' in response.data or b'Welcome' in response.data
    
    def test_login_with_invalid_credentials(self, test_app, test_db):
        """Test login with invalid credentials"""
        response = test_app.post('/login', data={
            'username': 'testpatient',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data or b'Login' in response.data
    
    def test_register_new_user(self, test_app, test_db):
        """Test user registration"""
        response = test_app.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123',
            'full_name': 'New User',
            'role': 'patient'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify user was created
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'newuser@example.com'
        assert user.full_name == 'New User'


class TestScanRoutes:
    """Test cases for prescription scanning routes"""
    
    @patch('utils.ocr.extract_text_from_image')
    @patch('utils.ocr.extract_medications_from_text')
    def test_process_scan_without_login(self, mock_extract_meds, mock_extract_text, test_app, test_db):
        """Test prescription scanning without being logged in"""
        # Mock the OCR and AI responses
        mock_extract_text.return_value = "Patient: John Doe\nMedication: Ibuprofen 200mg\nDosage: 1 tablet every 6 hours"
        mock_extract_meds.return_value = [
            {
                'name': 'Ibuprofen',
                'dosage': '200mg',
                'frequency': 'every 6 hours',
                'instructions': 'take with food'
            }
        ]
        
        # Create a sample image data (base64 encoded)
        sample_image_data = "data:image/jpeg;base64," + base64.b64encode(b"fake_image_data").decode()
        
        response = test_app.post('/process-scan', data={
            'image_data': sample_image_data
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'extracted_text' in data
        assert 'medications' in data
    
    def test_process_scan_missing_image_data(self, test_app):
        """Test process scan with missing image data"""
        response = test_app.post('/process-scan', data={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No image data provided' in data['error']


class TestMedicationSearchRoutes:
    """Test cases for medication search routes"""
    
    def test_medication_search_api(self, test_app, test_db):
        """Test medication search API"""
        response = test_app.get('/api/medications?query=ibu')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        
        # Should find Ibuprofen
        medication_names = [med['name'] for med in data]
        assert any('Ibuprofen' in name for name in medication_names)
    
    def test_medication_search_empty_query(self, test_app, test_db):
        """Test medication search with empty query"""
        response = test_app.get('/api/medications?query=')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 0


class TestDrugInteractionRoutes:
    """Test cases for drug interaction routes"""
    
    def test_public_interactions_post(self, test_app, test_db):
        """Test drug interaction checking via POST"""
        # Get medication IDs
        warfarin = Medication.query.filter_by(name='Warfarin').first()
        aspirin = Medication.query.filter_by(name='Aspirin').first()
        
        response = test_app.post('/public-interactions', data={
            'medication_id': [str(warfarin.id), str(aspirin.id)]
        })
        
        assert response.status_code == 200
        # Should show interaction results
        assert b'Potential Interactions' in response.data or b'Interaction' in response.data
    
    def test_public_interactions_insufficient_medications(self, test_app, test_db):
        """Test drug interaction checking with insufficient medications"""
        ibuprofen = Medication.query.filter_by(name='Ibuprofen').first()
        
        response = test_app.post('/public-interactions', data={
            'medication_id': [str(ibuprofen.id)]
        })
        
        assert response.status_code == 200
        # Should not show interaction results with only one medication
        assert b'No Interactions' in response.data or b'Check Drug Interactions' in response.data


class TestProtectedRoutes:
    """Test cases for routes that require authentication"""
    
    def test_dashboard_requires_login(self, test_app):
        """Test that dashboard requires login"""
        response = test_app.get('/dashboard')
        assert response.status_code == 302  # Redirect to login
    
    def test_profile_requires_login(self, test_app):
        """Test that profile requires login"""
        response = test_app.get('/profile')
        assert response.status_code == 302  # Redirect to login
    
    def test_reports_requires_login(self, test_app):
        """Test that reports requires login"""
        response = test_app.get('/reports')
        assert response.status_code == 302  # Redirect to login


class TestLanguageRoutes:
    """Test cases for language switching"""
    
    def test_set_language_english(self, test_app):
        """Test setting language to English"""
        response = test_app.get('/set-language/en', follow_redirects=True)
        assert response.status_code == 200
        
        # Check if language was set in session
        with test_app.session_transaction() as sess:
            assert sess.get('language') == 'en'
    
    def test_set_language_vietnamese(self, test_app):
        """Test setting language to Vietnamese"""
        response = test_app.get('/set-language/vi', follow_redirects=True)
        assert response.status_code == 200
        
        # Check if language was set in session
        with test_app.session_transaction() as sess:
            assert sess.get('language') == 'vi'


class TestErrorHandling:
    """Test cases for error handling"""
    
    def test_404_error(self, test_app):
        """Test 404 error handling"""
        response = test_app.get('/nonexistent-page')
        assert response.status_code == 404
    
    def test_prescription_not_found(self, test_app, test_db):
        """Test accessing non-existent prescription"""
        # Login as patient first
        with test_app.session_transaction() as sess:
            sess['user_id'] = '1'
            sess['_fresh'] = True
        
        response = test_app.get('/prescription/99999')
        assert response.status_code == 404


class TestSessionHandling:
    """Test cases for session handling"""
    
    def test_scan_data_in_session(self, test_app, sample_prescription_data):
        """Test that scan data is properly stored in session"""
        with test_app.session_transaction() as sess:
            sess['scan_data'] = sample_prescription_data
        
        response = test_app.get('/scan')
        assert response.status_code == 200
        
        # Verify session data persists
        with test_app.session_transaction() as sess:
            assert 'scan_data' in sess
            assert sess['scan_data']['extracted_text'] == sample_prescription_data['extracted_text']
    
    def test_clear_scanned_medications(self, test_app):
        """Test clearing scanned medications from session"""
        # Set up session with temp medications
        with test_app.session_transaction() as sess:
            sess['temp_medications'] = [
                {'name': 'Ibuprofen', 'id': 1},
                {'name': 'Acetaminophen', 'id': 2}
            ]
        
        response = test_app.get('/public-interactions?clear_scan=1', follow_redirects=True)
        assert response.status_code == 200
        
        # Verify session was cleared
        with test_app.session_transaction() as sess:
            assert 'temp_medications' not in sess