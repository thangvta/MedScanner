"""
Tests for database models
"""
import pytest
from datetime import datetime, date
from models import User, Medication, DrugInteraction, Prescription, PrescriptionMedication, Role
from werkzeug.security import check_password_hash


class TestUser:
    """Test cases for User model"""
    
    def test_user_creation(self, test_db):
        """Test user creation with basic fields"""
        user = User(
            username='newuser',
            email='newuser@test.com',
            password_hash='hashed_password',
            full_name='New User'
        )
        test_db.session.add(user)
        test_db.session.commit()
        
        assert user.id is not None
        assert user.username == 'newuser'
        assert user.email == 'newuser@test.com'
        assert user.full_name == 'New User'
        assert user.created_at is not None
    
    def test_user_password_hashing(self, test_db):
        """Test password hashing functionality"""
        from werkzeug.security import generate_password_hash
        
        password = 'testpassword123'
        hashed = generate_password_hash(password)
        
        user = User(
            username='passwordtest',
            email='password@test.com',
            password_hash=hashed,
            full_name='Password Test'
        )
        test_db.session.add(user)
        test_db.session.commit()
        
        assert check_password_hash(user.password_hash, password)
        assert not check_password_hash(user.password_hash, 'wrongpassword')
    
    def test_user_roles(self, test_db):
        """Test user role assignments"""
        user = User.query.filter_by(username='testpatient').first()
        
        assert user is not None
        assert len(user.roles) == 1
        assert user.roles[0].name == 'patient'
        assert user.has_role('patient')
        assert not user.has_role('doctor')
    
    def test_user_profile_fields(self, test_db):
        """Test user profile fields"""
        user = User.query.filter_by(username='testpatient').first()
        
        # Update profile fields
        user.date_of_birth = date(1990, 1, 1)
        user.weight = 70.5
        user.height = 175.0
        test_db.session.commit()
        
        assert user.date_of_birth == date(1990, 1, 1)
        assert user.weight == 70.5
        assert user.height == 175.0


class TestMedication:
    """Test cases for Medication model"""
    
    def test_medication_creation(self, test_db):
        """Test medication creation"""
        med = Medication(
            name='Test Medication',
            generic_name='test-med',
            description='Test medication description',
            dosage_form='capsule',
            strength='10mg',
            stock_quantity=25,
            minimum_stock_level=5
        )
        test_db.session.add(med)
        test_db.session.commit()
        
        assert med.id is not None
        assert med.name == 'Test Medication'
        assert med.generic_name == 'test-med'
        assert med.dosage_form == 'capsule'
        assert med.strength == '10mg'
        assert med.stock_quantity == 25
        assert med.minimum_stock_level == 5
    
    def test_medication_relationships(self, test_db):
        """Test medication relationships with interactions"""
        warfarin = Medication.query.filter_by(name='Warfarin').first()
        
        assert warfarin is not None
        # Check that warfarin has interactions
        interactions = warfarin.interactions.all()
        assert len(interactions) > 0


class TestDrugInteraction:
    """Test cases for DrugInteraction model"""
    
    def test_drug_interaction_creation(self, test_db):
        """Test drug interaction creation"""
        med1 = Medication.query.filter_by(name='Ibuprofen').first()
        med2 = Medication.query.filter_by(name='Acetaminophen').first()
        
        interaction = DrugInteraction(
            drug1_id=med1.id,
            drug2_id=med2.id,
            severity='mild',
            description='Minor interaction between these medications'
        )
        test_db.session.add(interaction)
        test_db.session.commit()
        
        assert interaction.id is not None
        assert interaction.drug1_id == med1.id
        assert interaction.drug2_id == med2.id
        assert interaction.severity == 'mild'
        assert interaction.description == 'Minor interaction between these medications'
    
    def test_drug_interaction_relationships(self, test_db):
        """Test drug interaction relationships"""
        interaction = DrugInteraction.query.first()
        
        assert interaction is not None
        assert interaction.drug1 is not None
        assert interaction.drug2 is not None
        assert interaction.drug1.name in ['Warfarin', 'Ibuprofen']
        assert interaction.drug2.name in ['Aspirin', 'Warfarin']


class TestPrescription:
    """Test cases for Prescription model"""
    
    def test_prescription_creation(self, test_db):
        """Test prescription creation"""
        patient = User.query.filter_by(username='testpatient').first()
        doctor = User.query.filter_by(username='testdoctor').first()
        
        prescription = Prescription(
            user_id=patient.id,
            doctor_id=doctor.id,
            status='pending',
            date_prescribed=datetime.utcnow()
        )
        test_db.session.add(prescription)
        test_db.session.commit()
        
        assert prescription.id is not None
        assert prescription.user_id == patient.id
        assert prescription.doctor_id == doctor.id
        assert prescription.status == 'pending'
        assert prescription.date_prescribed is not None
    
    def test_prescription_relationships(self, test_db):
        """Test prescription relationships"""
        patient = User.query.filter_by(username='testpatient').first()
        doctor = User.query.filter_by(username='testdoctor').first()
        
        prescription = Prescription(
            user_id=patient.id,
            doctor_id=doctor.id,
            status='filled'
        )
        test_db.session.add(prescription)
        test_db.session.commit()
        
        # Test relationships
        assert prescription.patient == patient
        assert prescription.doctor == doctor
        assert prescription in patient.prescriptions


class TestPrescriptionMedication:
    """Test cases for PrescriptionMedication model"""
    
    def test_prescription_medication_creation(self, test_db):
        """Test prescription medication creation"""
        patient = User.query.filter_by(username='testpatient').first()
        medication = Medication.query.filter_by(name='Ibuprofen').first()
        
        prescription = Prescription(
            user_id=patient.id,
            status='pending'
        )
        test_db.session.add(prescription)
        test_db.session.flush()
        
        prescription_med = PrescriptionMedication(
            prescription_id=prescription.id,
            medication_id=medication.id,
            dosage='1 tablet',
            frequency='twice daily',
            duration='7 days',
            instructions='take with food'
        )
        test_db.session.add(prescription_med)
        test_db.session.commit()
        
        assert prescription_med.id is not None
        assert prescription_med.prescription_id == prescription.id
        assert prescription_med.medication_id == medication.id
        assert prescription_med.dosage == '1 tablet'
        assert prescription_med.frequency == 'twice daily'
        assert prescription_med.duration == '7 days'
        assert prescription_med.instructions == 'take with food'
    
    def test_prescription_medication_relationships(self, test_db):
        """Test prescription medication relationships"""
        patient = User.query.filter_by(username='testpatient').first()
        medication = Medication.query.filter_by(name='Acetaminophen').first()
        
        prescription = Prescription(
            user_id=patient.id,
            status='pending'
        )
        test_db.session.add(prescription)
        test_db.session.flush()
        
        prescription_med = PrescriptionMedication(
            prescription_id=prescription.id,
            medication_id=medication.id,
            dosage='2 tablets',
            frequency='as needed'
        )
        test_db.session.add(prescription_med)
        test_db.session.commit()
        
        # Test relationships
        assert prescription_med.prescription == prescription
        assert prescription_med.medication == medication
        assert prescription_med in prescription.medications