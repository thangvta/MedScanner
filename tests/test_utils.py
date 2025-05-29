"""
Tests for utility functions
"""
import pytest
from unittest.mock import patch, MagicMock
from utils.dosage import parse_dosage, calculate_age, verify_dosage
from utils.drug_interaction import check_drug_interactions
from utils.inventory import update_inventory, get_low_stock_medications
from datetime import date, datetime
from models import Medication, DrugInteraction


class TestDosageUtils:
    """Test cases for dosage utility functions"""
    
    def test_parse_dosage_with_mg(self):
        """Test parsing dosage with milligrams"""
        value, unit = parse_dosage("10mg")
        assert value == 10.0
        assert unit == "mg"
    
    def test_parse_dosage_with_spaces(self):
        """Test parsing dosage with spaces"""
        value, unit = parse_dosage("5 ml")
        assert value == 5.0
        assert unit == "ml"
    
    def test_parse_dosage_with_tablets(self):
        """Test parsing dosage with tablets"""
        value, unit = parse_dosage("2 tablets")
        assert value == 2.0
        assert unit == "tablets"
    
    def test_parse_dosage_invalid_format(self):
        """Test parsing invalid dosage format"""
        value, unit = parse_dosage("invalid dosage")
        assert value is None
        assert unit is None
    
    def test_calculate_age(self):
        """Test age calculation"""
        birth_date = date(1990, 1, 1)
        age = calculate_age(birth_date)
        
        # Age should be reasonable (between 30-40 as of 2024)
        assert isinstance(age, int)
        assert 30 <= age <= 40
    
    def test_calculate_age_recent_birthday(self):
        """Test age calculation for recent birthday"""
        # Someone born exactly 25 years ago
        birth_date = date(datetime.now().year - 25, datetime.now().month, datetime.now().day)
        age = calculate_age(birth_date)
        assert age == 25
    
    def test_verify_dosage_normal_adult(self, test_db):
        """Test dosage verification for normal adult"""
        medication = Medication.query.filter_by(name='Ibuprofen').first()
        
        result = verify_dosage(medication, "200mg", weight=70, age=30)
        
        assert isinstance(result, dict)
        assert 'is_safe' in result
        assert 'warnings' in result
        assert 'recommendations' in result
    
    def test_verify_dosage_pediatric(self, test_db):
        """Test dosage verification for pediatric patient"""
        medication = Medication.query.filter_by(name='Acetaminophen').first()
        
        result = verify_dosage(medication, "500mg", weight=20, age=8)
        
        assert isinstance(result, dict)
        assert 'is_safe' in result
        # Should have warnings for pediatric dosing
        assert len(result['warnings']) > 0
    
    def test_verify_dosage_elderly(self, test_db):
        """Test dosage verification for elderly patient"""
        medication = Medication.query.filter_by(name='Warfarin').first()
        
        result = verify_dosage(medication, "5mg", weight=65, age=80)
        
        assert isinstance(result, dict)
        assert 'is_safe' in result
        # Should have warnings for elderly patients
        assert len(result['warnings']) > 0


class TestDrugInteractionUtils:
    """Test cases for drug interaction utility functions"""
    
    def test_check_drug_interactions_with_known_interaction(self, test_db):
        """Test checking interactions between medications with known interactions"""
        warfarin = Medication.query.filter_by(name='Warfarin').first()
        aspirin = Medication.query.filter_by(name='Aspirin').first()
        
        result = check_drug_interactions([warfarin.id, aspirin.id])
        
        assert isinstance(result, dict)
        assert 'interactions' in result
        assert 'severity_summary' in result
        
        # Should find the severe interaction between Warfarin and Aspirin
        assert len(result['interactions']) > 0
        assert any(interaction.severity == 'severe' for interaction in result['interactions'])
    
    def test_check_drug_interactions_no_interactions(self, test_db):
        """Test checking interactions between medications with no known interactions"""
        ibuprofen = Medication.query.filter_by(name='Ibuprofen').first()
        acetaminophen = Medication.query.filter_by(name='Acetaminophen').first()
        
        result = check_drug_interactions([ibuprofen.id, acetaminophen.id])
        
        assert isinstance(result, dict)
        assert 'interactions' in result
        # These medications should have no direct interactions in our test data
        assert len(result['interactions']) == 0
    
    def test_check_drug_interactions_single_medication(self, test_db):
        """Test checking interactions with single medication"""
        ibuprofen = Medication.query.filter_by(name='Ibuprofen').first()
        
        result = check_drug_interactions([ibuprofen.id])
        
        assert isinstance(result, dict)
        assert 'interactions' in result
        # Single medication should have no interactions
        assert len(result['interactions']) == 0
    
    def test_check_drug_interactions_with_patient_allergies(self, test_db):
        """Test checking interactions including patient allergies"""
        patient = 1  # Test patient ID
        warfarin = Medication.query.filter_by(name='Warfarin').first()
        
        result = check_drug_interactions([warfarin.id], patient_id=patient)
        
        assert isinstance(result, dict)
        assert 'interactions' in result
        assert 'allergy_warnings' in result


class TestInventoryUtils:
    """Test cases for inventory utility functions"""
    
    def test_update_inventory_increase(self, test_db):
        """Test increasing inventory stock"""
        medication = Medication.query.filter_by(name='Ibuprofen').first()
        initial_stock = medication.stock_quantity
        
        success = update_inventory(medication.id, 50, "Stock replenishment", user_id=1)
        
        assert success is True
        
        # Refresh from database
        test_db.session.refresh(medication)
        assert medication.stock_quantity == initial_stock + 50
    
    def test_update_inventory_decrease(self, test_db):
        """Test decreasing inventory stock"""
        medication = Medication.query.filter_by(name='Acetaminophen').first()
        initial_stock = medication.stock_quantity
        
        success = update_inventory(medication.id, -25, "Prescription filled", user_id=1)
        
        assert success is True
        
        # Refresh from database
        test_db.session.refresh(medication)
        assert medication.stock_quantity == initial_stock - 25
    
    def test_update_inventory_insufficient_stock(self, test_db):
        """Test decreasing inventory below zero"""
        medication = Medication.query.filter_by(name='Warfarin').first()
        
        # Try to remove more stock than available
        success = update_inventory(medication.id, -1000, "Test removal", user_id=1)
        
        # Should still succeed but stock should not go negative
        assert success is True
        
        # Refresh from database
        test_db.session.refresh(medication)
        assert medication.stock_quantity >= 0
    
    def test_get_low_stock_medications(self, test_db):
        """Test getting medications with low stock"""
        # Set a medication to low stock
        medication = Medication.query.filter_by(name='Warfarin').first()
        medication.stock_quantity = 5
        medication.minimum_stock_level = 10
        test_db.session.commit()
        
        low_stock_meds = get_low_stock_medications()
        
        assert isinstance(low_stock_meds, list)
        # Should include our low stock medication
        low_stock_names = [med.name for med in low_stock_meds]
        assert 'Warfarin' in low_stock_names
    
    def test_get_low_stock_medications_with_threshold(self, test_db):
        """Test getting medications with custom threshold"""
        # Set medications to different stock levels
        ibuprofen = Medication.query.filter_by(name='Ibuprofen').first()
        ibuprofen.stock_quantity = 15
        test_db.session.commit()
        
        # Use custom threshold of 20
        low_stock_meds = get_low_stock_medications(threshold=20)
        
        assert isinstance(low_stock_meds, list)
        # Should include medications below threshold of 20
        low_stock_names = [med.name for med in low_stock_meds]
        assert 'Ibuprofen' in low_stock_names


class TestOCRUtils:
    """Test cases for OCR utility functions (mocked)"""
    
    @patch('utils.ocr.openai_client')
    @patch('utils.ocr.cv2.imread')
    def test_extract_text_from_image_success(self, mock_imread, mock_openai):
        """Test successful text extraction from image"""
        from utils.ocr import extract_text_from_image
        
        # Mock OpenCV image reading
        mock_imread.return_value = MagicMock()
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Patient: John Doe\nMedication: Ibuprofen 200mg"
        mock_openai.chat.completions.create.return_value = mock_response
        
        result = extract_text_from_image("/fake/path/image.jpg")
        
        assert isinstance(result, str)
        assert "Patient: John Doe" in result
        assert "Ibuprofen" in result
    
    @patch('utils.ocr.openai_client')
    def test_extract_medications_from_text_success(self, mock_openai):
        """Test successful medication extraction from text"""
        from utils.ocr import extract_medications_from_text
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"medications": [{"name": "Ibuprofen", "dosage": "200mg", "frequency": "twice daily", "instructions": "take with food"}]}'
        mock_openai.chat.completions.create.return_value = mock_response
        
        result = extract_medications_from_text("Patient: John Doe\nMedication: Ibuprofen 200mg")
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]['name'] == 'Ibuprofen'
        assert result[0]['dosage'] == '200mg'
    
    @patch('utils.ocr.openai_client')
    def test_extract_medications_from_text_invalid_json(self, mock_openai):
        """Test medication extraction with invalid JSON response"""
        from utils.ocr import extract_medications_from_text
        
        # Mock OpenAI response with invalid JSON
        mock_response = MagicMock()
        mock_response.choices[0].message.content = 'invalid json response'
        mock_openai.chat.completions.create.return_value = mock_response
        
        result = extract_medications_from_text("Some prescription text")
        
        assert isinstance(result, list)
        assert len(result) == 0  # Should return empty list for invalid JSON
    
    @patch('utils.ocr.openai_client')
    def test_extract_medications_api_error(self, mock_openai):
        """Test medication extraction when API fails"""
        from utils.ocr import extract_medications_from_text
        
        # Mock OpenAI API error
        mock_openai.chat.completions.create.side_effect = Exception("API Error")
        
        result = extract_medications_from_text("Some prescription text")
        
        assert isinstance(result, list)
        assert len(result) == 0  # Should return empty list on error