from app import db
from flask_login import UserMixin
from datetime import datetime

# Association table for user-roles
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    def __repr__(self):
        return f'<Role {self.name}>'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    roles = db.relationship('Role', secondary=user_roles, lazy='subquery',
                            backref=db.backref('users', lazy=True))
    
    # For patient role
    date_of_birth = db.Column(db.Date, nullable=True)
    weight = db.Column(db.Float, nullable=True)  # in kg
    height = db.Column(db.Float, nullable=True)  # in cm
    
    # User's prescriptions (as a patient)
    prescriptions = db.relationship('Prescription', backref='patient', lazy=True, foreign_keys='Prescription.user_id')
    
    def has_role(self, role_name):
        """Check if user has specific role"""
        return any(role.name == role_name for role in self.roles)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    generic_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    dosage_form = db.Column(db.String(50))  # e.g., tablet, capsule, liquid
    strength = db.Column(db.String(50))  # e.g., 10mg, 500mg
    
    # Inventory related
    stock_quantity = db.Column(db.Integer, default=0)
    minimum_stock_level = db.Column(db.Integer, default=10)
    
    # Relationships
    prescriptions = db.relationship('PrescriptionMedication', backref='medication', lazy=True)
    interactions = db.relationship(
        'DrugInteraction',
        primaryjoin="or_(Medication.id==DrugInteraction.drug1_id, Medication.id==DrugInteraction.drug2_id)",
        lazy='dynamic'
    )
    
    def __repr__(self):
        return f'<Medication {self.name} {self.strength}>'


class DrugInteraction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    drug1_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=False)
    drug2_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # mild, moderate, severe
    description = db.Column(db.Text, nullable=False)
    
    # Relationships
    drug1 = db.relationship('Medication', foreign_keys=[drug1_id])
    drug2 = db.relationship('Medication', foreign_keys=[drug2_id])
    
    def __repr__(self):
        return f'<DrugInteraction {self.severity}: {self.drug1_id} - {self.drug2_id}>'


class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    date_prescribed = db.Column(db.DateTime, default=datetime.utcnow)
    date_filled = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, filled, cancelled
    scan_image_path = db.Column(db.String(255), nullable=True)
    
    # Relationships
    medications = db.relationship('PrescriptionMedication', backref='prescription', lazy=True)
    doctor = db.relationship('User', foreign_keys=[doctor_id])
    interaction_reports = db.relationship('InteractionReport', backref='prescription', lazy=True)
    
    def __repr__(self):
        return f'<Prescription {self.id} for User {self.user_id}>'


class PrescriptionMedication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescription.id'), nullable=False)
    medication_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=False)
    dosage = db.Column(db.String(50))  # e.g., "1 tablet", "5ml"
    frequency = db.Column(db.String(50))  # e.g., "twice daily", "every 4 hours"
    duration = db.Column(db.String(50))  # e.g., "7 days", "1 month"
    instructions = db.Column(db.Text)
    
    def __repr__(self):
        return f'<PrescriptionMedication {self.id}>'


class InteractionReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescription.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    summary = db.Column(db.Text)
    has_interactions = db.Column(db.Boolean, default=False)
    has_dosage_issues = db.Column(db.Boolean, default=False)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    details = db.relationship('InteractionDetail', backref='report', lazy=True)
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])
    
    def __repr__(self):
        return f'<InteractionReport {self.id} for Prescription {self.prescription_id}>'


class InteractionDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('interaction_report.id'), nullable=False)
    drug1_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=True)
    drug2_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=True)
    interaction_type = db.Column(db.String(20))  # drug-drug, dosage, allergy
    severity = db.Column(db.String(20))  # mild, moderate, severe
    description = db.Column(db.Text)
    recommendation = db.Column(db.Text)
    
    # Relationships
    drug1 = db.relationship('Medication', foreign_keys=[drug1_id])
    drug2 = db.relationship('Medication', foreign_keys=[drug2_id])
    
    def __repr__(self):
        return f'<InteractionDetail {self.id} - {self.interaction_type}>'


class InventoryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medication_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=False)
    quantity_change = db.Column(db.Integer, nullable=False)  # positive for addition, negative for removal
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    recorded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reason = db.Column(db.String(100))  # e.g., "prescription filled", "stock adjustment"
    
    # Relationships
    medication = db.relationship('Medication')
    recorded_by = db.relationship('User')
    
    def __repr__(self):
        return f'<InventoryLog {self.id} - {self.medication_id}: {self.quantity_change}>'


class PatientMedicalHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    condition = db.Column(db.String(100), nullable=False)
    diagnosed_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20))  # active, resolved, chronic
    notes = db.Column(db.Text)
    
    # Relationship
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<PatientMedicalHistory {self.id} - User: {self.user_id}, Condition: {self.condition}>'


class PatientAllergy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    allergen = db.Column(db.String(100), nullable=False)
    reaction = db.Column(db.String(100))
    severity = db.Column(db.String(20))  # mild, moderate, severe
    
    # Relationship
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<PatientAllergy {self.id} - User: {self.user_id}, Allergen: {self.allergen}>'
