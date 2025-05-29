"""
Test configuration and fixtures for MedScanner application
"""
import pytest
import tempfile
import os
from app import app, db
from models import User, Medication, DrugInteraction, Role
from werkzeug.security import generate_password_hash


@pytest.fixture
def test_app():
    """Create and configure a test application."""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp()
    
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    # Set OpenAI API key for testing (will use environment variable)
    if not os.environ.get('OPENAI_API_KEY'):
        app.config['OPENAI_API_KEY'] = 'test-key-for-mocking'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def test_db(test_app):
    """Create test database with sample data."""
    with app.app_context():
        # Clear existing data first
        db.drop_all()
        db.create_all()
        
        # Create roles
        patient_role = Role(name='patient')
        doctor_role = Role(name='doctor')
        pharmacist_role = Role(name='pharmacist')
        
        db.session.add_all([patient_role, doctor_role, pharmacist_role])
        db.session.commit()
        
        # Create test users
        test_patient = User(
            username='testpatient',
            email='patient@test.com',
            password_hash=generate_password_hash('testpass123'),
            full_name='Test Patient'
        )
        test_patient.roles.append(patient_role)
        
        test_doctor = User(
            username='testdoctor',
            email='doctor@test.com',
            password_hash=generate_password_hash('testpass123'),
            full_name='Dr. Test Doctor'
        )
        test_doctor.roles.append(doctor_role)
        
        test_pharmacist = User(
            username='testpharmacist',
            email='pharmacist@test.com',
            password_hash=generate_password_hash('testpass123'),
            full_name='Test Pharmacist'
        )
        test_pharmacist.roles.append(pharmacist_role)
        
        db.session.add_all([test_patient, test_doctor, test_pharmacist])
        db.session.commit()
        
        # Create test medications
        med1 = Medication(
            name='Ibuprofen',
            generic_name='Ibuprofen',
            description='Nonsteroidal anti-inflammatory drug',
            dosage_form='tablet',
            strength='200mg',
            stock_quantity=100
        )
        
        med2 = Medication(
            name='Acetaminophen',
            generic_name='Acetaminophen',
            description='Pain reliever and fever reducer',
            dosage_form='tablet',
            strength='500mg',
            stock_quantity=150
        )
        
        med3 = Medication(
            name='Warfarin',
            generic_name='Warfarin Sodium',
            description='Anticoagulant',
            dosage_form='tablet',
            strength='5mg',
            stock_quantity=50
        )
        
        med4 = Medication(
            name='Aspirin',
            generic_name='Acetylsalicylic Acid',
            description='Pain reliever and blood thinner',
            dosage_form='tablet',
            strength='81mg',
            stock_quantity=200
        )
        
        db.session.add_all([med1, med2, med3, med4])
        db.session.commit()
        
        # Create test drug interactions
        interaction1 = DrugInteraction(
            drug1_id=med3.id,  # Warfarin
            drug2_id=med4.id,  # Aspirin
            severity='severe',
            description='Increased risk of bleeding when taken together'
        )
        
        interaction2 = DrugInteraction(
            drug1_id=med1.id,  # Ibuprofen
            drug2_id=med3.id,  # Warfarin
            severity='moderate',
            description='NSAIDs may increase anticoagulant effects'
        )
        
        db.session.add_all([interaction1, interaction2])
        db.session.commit()
        
        yield db
        
        # Clean up
        db.session.remove()
        db.drop_all()


@pytest.fixture
def auth_headers():
    """Helper function to create authentication headers for testing."""
    def _auth_headers(username, password):
        return {
            'Authorization': f'Basic {username}:{password}'
        }
    return _auth_headers


@pytest.fixture
def sample_prescription_data():
    """Sample prescription data for testing."""
    return {
        'extracted_text': 'Patient: John Doe\nMedication: Ibuprofen 200mg\nDosage: 1 tablet every 6 hours\nMedication: Acetaminophen 500mg\nDosage: 2 tablets every 8 hours',
        'medications': [
            {
                'id': 1,
                'name': 'Ibuprofen',
                'strength': '200mg',
                'dosage_form': 'tablet',
                'dosage': '1 tablet',
                'frequency': 'every 6 hours',
                'instructions': 'take with food'
            },
            {
                'id': 2,
                'name': 'Acetaminophen',
                'strength': '500mg',
                'dosage_form': 'tablet',
                'dosage': '2 tablets',
                'frequency': 'every 8 hours',
                'instructions': 'as needed for pain'
            }
        ]
    }