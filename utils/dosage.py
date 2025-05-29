import logging
import re
from datetime import datetime

def parse_dosage(dosage_str):
    """
    Parse a dosage string into a numeric value and unit
    
    Args:
        dosage_str (str): Dosage string (e.g., "10mg", "5 ml")
        
    Returns:
        tuple: (value, unit) or (None, None) if parsing fails
    """
    try:
        # Remove whitespace and convert to lowercase
        dosage_str = dosage_str.strip().lower()
        
        # Regular expression to extract numeric value and unit
        match = re.match(r"(\d+\.?\d*)\s*([a-z]+)", dosage_str)
        
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            return value, unit
        
        # Try to extract just a number if no unit is specified
        numeric_match = re.match(r"(\d+\.?\d*)", dosage_str)
        if numeric_match:
            return float(numeric_match.group(1)), None
            
        return None, None
    
    except Exception as e:
        logging.error(f"Error parsing dosage: {str(e)}")
        return None, None

def calculate_age(birth_date):
    """
    Calculate age from birth date
    
    Args:
        birth_date (datetime.date): Date of birth
        
    Returns:
        int: Age in years
    """
    if not birth_date:
        return None
        
    today = datetime.now().date()
    age = today.year - birth_date.year
    
    # Adjust age if birthday hasn't occurred yet this year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
        
    return age

def verify_dosage(medication, dosage_str, weight=None, age=None):
    """
    Verify if the dosage is appropriate based on patient information
    
    Args:
        medication (Medication): Medication object
        dosage_str (str): Dosage string (e.g., "10mg", "5 ml")
        weight (float, optional): Patient weight in kg
        age (int, optional): Patient age in years
        
    Returns:
        dict: Results of dosage verification
    """
    result = {
        'is_appropriate': True,
        'warnings': [],
        'recommendations': []
    }
    
    try:
        # Parse the dosage
        dosage_value, dosage_unit = parse_dosage(dosage_str)
        
        if not dosage_value:
            result['is_appropriate'] = False
            result['warnings'].append("Unable to parse dosage value")
            return result
            
        # Get medication strength for comparison
        strength_value, strength_unit = parse_dosage(medication.strength)
        
        # If units don't match, we might need to convert
        if dosage_unit and strength_unit and dosage_unit != strength_unit:
            result['warnings'].append(f"Dosage unit ({dosage_unit}) doesn't match medication strength unit ({strength_unit})")
        
        # Check for weight-based dosing if weight is provided
        if weight:
            # Example logic for common medications
            if "ibuprofen" in medication.name.lower():
                # Typical dosage 5-10 mg/kg every 6-8 hours
                max_daily_dose_per_kg = 40  # mg/kg/day
                if (dosage_unit == "mg" or strength_unit == "mg") and dosage_value > (weight * max_daily_dose_per_kg / 4):
                    result['is_appropriate'] = False
                    result['warnings'].append(f"Dosage exceeds maximum recommended dose for weight ({weight} kg)")
                    result['recommendations'].append(f"Maximum recommended dose: {weight * 10} mg per dose")
            
            elif "acetaminophen" in medication.name.lower() or "paracetamol" in medication.generic_name.lower():
                # Typically 10-15 mg/kg every 4-6 hours
                max_daily_dose_per_kg = 75  # mg/kg/day
                if (dosage_unit == "mg" or strength_unit == "mg") and dosage_value > (weight * max_daily_dose_per_kg / 5):
                    result['is_appropriate'] = False
                    result['warnings'].append(f"Dosage exceeds maximum recommended dose for weight ({weight} kg)")
                    result['recommendations'].append(f"Maximum recommended dose: {weight * 15} mg per dose")
        
        # Check age-specific considerations
        if age is not None:
            # Pediatric considerations
            if age < 12:
                if "aspirin" in medication.name.lower():
                    result['is_appropriate'] = False
                    result['warnings'].append("Aspirin is not recommended for children under 12 due to risk of Reye's syndrome")
                
                elif "ibuprofen" in medication.name.lower() and age < 6:
                    # Check if dose is appropriate for children
                    if dosage_value > 100 and (dosage_unit == "mg" or strength_unit == "mg"):
                        result['is_appropriate'] = False
                        result['warnings'].append(f"Dosage may be too high for a {age}-year-old child")
            
            # Geriatric considerations            
            elif age > 65:
                # Elderly often need lower doses
                if "warfarin" in medication.name.lower():
                    if dosage_value > 5 and (dosage_unit == "mg" or strength_unit == "mg"):
                        result['warnings'].append("Elderly patients may require lower warfarin doses")
                        result['recommendations'].append("Consider starting with a lower dose and monitoring closely")
        
        # General high-dose warnings
        if strength_value and strength_unit == dosage_unit:
            if dosage_value > 4 * strength_value:
                result['warnings'].append(f"Dosage ({dosage_value} {dosage_unit}) is more than 4x the standard strength ({strength_value} {strength_unit})")
                result['is_appropriate'] = False
        
        return result
            
    except Exception as e:
        logging.error(f"Error verifying dosage: {str(e)}")
        return {
            'error': str(e),
            'is_appropriate': False,
            'warnings': ["Error occurred during dosage verification"],
            'recommendations': ["Verify dosage manually"]
        }
