import logging
from models import Medication, DrugInteraction, PatientAllergy, User

def check_drug_interactions(medication_ids, patient_id=None):
    """
    Check for drug interactions between medications and with patient allergies
    
    Args:
        medication_ids (list): List of medication IDs to check
        patient_id (int, optional): Patient user ID to check for allergies
        
    Returns:
        dict: Results of interaction check with severity and descriptions
    """
    results = {
        'interactions': [],
        'allergies': [],
        'has_severe_interaction': False
    }
    
    try:
        # Check for drug-drug interactions
        for i, med1_id in enumerate(medication_ids):
            for med2_id in medication_ids[i+1:]:
                # Query for interactions between these medications in either direction
                interaction = DrugInteraction.query.filter(
                    ((DrugInteraction.drug1_id == med1_id) & (DrugInteraction.drug2_id == med2_id)) |
                    ((DrugInteraction.drug1_id == med2_id) & (DrugInteraction.drug2_id == med1_id))
                ).first()
                
                if interaction:
                    # Get medication names for the results
                    med1 = Medication.query.get(med1_id)
                    med2 = Medication.query.get(med2_id)
                    
                    if med1 and med2:
                        results['interactions'].append({
                            'drug1_id': med1_id,
                            'drug2_id': med2_id,
                            'drug1_name': med1.name,
                            'drug2_name': med2.name,
                            'severity': interaction.severity,
                            'description': interaction.description
                        })
                        
                        # Check if this is a severe interaction
                        if interaction.severity == 'severe':
                            results['has_severe_interaction'] = True
        
        # Check for allergies if patient ID is provided
        if patient_id:
            patient_allergies = PatientAllergy.query.filter_by(user_id=patient_id).all()
            
            for medication_id in medication_ids:
                medication = Medication.query.get(medication_id)
                if not medication:
                    continue
                
                for allergy in patient_allergies:
                    # Simple string matching for demonstration purposes
                    # In a real application, you'd have a more sophisticated matching system
                    if (allergy.allergen.lower() in medication.name.lower() or 
                        (medication.generic_name and allergy.allergen.lower() in medication.generic_name.lower())):
                        
                        results['allergies'].append({
                            'medication_id': medication_id, 
                            'medication_name': medication.name,
                            'allergen': allergy.allergen,
                            'severity': allergy.severity,
                            'reaction': allergy.reaction
                        })
                        
                        # Allergies are always considered severe
                        results['has_severe_interaction'] = True
        
        return results
    
    except Exception as e:
        logging.error(f"Error checking drug interactions: {str(e)}")
        return {
            'error': str(e),
            'interactions': [],
            'allergies': [],
            'has_severe_interaction': False
        }
