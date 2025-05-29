import logging
from datetime import datetime

from app import db
from models import Medication, InventoryLog

def update_inventory(medication_id, quantity_change, reason, user_id=None):
    """
    Update medication inventory and log the change
    
    Args:
        medication_id (int): ID of medication to update
        quantity_change (int): Amount to add or remove (positive or negative)
        reason (str): Reason for inventory change
        user_id (int, optional): ID of user making the change
        
    Returns:
        bool: Success status
    """
    try:
        # Get the medication
        medication = db.session.get(Medication, medication_id)
        if not medication:
            logging.error(f"Medication with ID {medication_id} not found")
            return False
        
        # Update the stock quantity
        new_quantity = medication.stock_quantity + quantity_change
        
        # Don't allow negative inventory
        if new_quantity < 0:
            logging.warning(f"Attempted to reduce inventory below zero for medication {medication_id}")
            return False
            
        medication.stock_quantity = new_quantity
        
        # Create inventory log entry
        log_entry = InventoryLog(
            medication_id=medication_id,
            quantity_change=quantity_change,
            timestamp=datetime.utcnow(),
            recorded_by_id=user_id,
            reason=reason
        )
        
        # Add and commit changes
        db.session.add(log_entry)
        db.session.commit()
        
        logging.info(f"Inventory updated for medication {medication_id}: {quantity_change} units, new total: {new_quantity}")
        return True
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating inventory: {str(e)}")
        return False

def get_low_stock_medications(threshold=None):
    """
    Get list of medications with stock levels below threshold
    
    Args:
        threshold (int, optional): Override default minimum stock levels
        
    Returns:
        list: Medications with low stock
    """
    try:
        if threshold is not None:
            # Use provided threshold
            low_stock = Medication.query.filter(
                Medication.stock_quantity < threshold
            ).all()
        else:
            # Use each medication's defined minimum stock level
            low_stock = Medication.query.filter(
                Medication.stock_quantity < Medication.minimum_stock_level
            ).all()
            
        return low_stock
        
    except Exception as e:
        logging.error(f"Error getting low stock medications: {str(e)}")
        return []
