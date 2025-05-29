import os
import logging
import base64
import tempfile
from datetime import datetime
from flask import flash, redirect, render_template, request, url_for, jsonify, session
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from app import app, db
from models import (User, Role, Medication, DrugInteraction, Prescription,
                   PrescriptionMedication, InteractionReport, InteractionDetail,
                   InventoryLog, PatientMedicalHistory, PatientAllergy)
from utils.ocr import extract_text_from_image
from utils.drug_interaction import check_drug_interactions
from utils.dosage import verify_dosage
from utils.inventory import update_inventory

# Home page route
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')
            flash('Login successful!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        role_name = request.form.get('role')
        
        # Validate form inputs
        if not all([username, email, password, confirm_password, role_name]):
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists', 'danger')
            return render_template('register.html')
        
        # Get the role
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            flash('Invalid role selected', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            full_name=full_name
        )
        new_user.roles.append(role)
        
        # Add and commit to database
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    # Get all available roles for the registration form
    roles = Role.query.all()
    return render_template('register.html', roles=roles)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# User dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Different dashboard views based on user role
    if current_user.has_role('patient'):
        # Get patient's prescriptions
        prescriptions = Prescription.query.filter_by(user_id=current_user.id).order_by(Prescription.date_prescribed.desc()).all()
        
        # Get recent interaction reports
        reports = InteractionReport.query.join(Prescription).filter(
            Prescription.user_id == current_user.id
        ).order_by(InteractionReport.created_at.desc()).limit(5).all()
        
        return render_template('dashboard.html', prescriptions=prescriptions, reports=reports)
        
    elif current_user.has_role('doctor'):
        # Get prescriptions created by this doctor
        prescriptions = Prescription.query.filter_by(doctor_id=current_user.id).order_by(Prescription.date_prescribed.desc()).limit(10).all()
        
        # Get count of patients
        patient_count = User.query.join(User.roles).filter(Role.name == 'patient').count()
        
        return render_template('dashboard.html', prescriptions=prescriptions, patient_count=patient_count)
        
    elif current_user.has_role('pharmacist'):
        # Get pending prescriptions
        pending_prescriptions = Prescription.query.filter_by(status='pending').order_by(Prescription.date_prescribed.desc()).limit(10).all()
        
        # Get medications with low stock
        low_stock = Medication.query.filter(Medication.stock_quantity < Medication.minimum_stock_level).all()
        
        return render_template('dashboard.html', pending_prescriptions=pending_prescriptions, low_stock=low_stock)
    
    # Default dashboard if role not recognized
    return render_template('dashboard.html')

# User profile
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update profile information
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        
        # Only update if patient is updating their profile
        if current_user.has_role('patient'):
            try:
                date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date() if request.form.get('date_of_birth') else None
                weight = float(request.form.get('weight')) if request.form.get('weight') else None
                height = float(request.form.get('height')) if request.form.get('height') else None
                
                current_user.date_of_birth = date_of_birth
                current_user.weight = weight
                current_user.height = height
            except (ValueError, TypeError):
                flash('Invalid format for date of birth, weight, or height', 'danger')
                return redirect(url_for('profile'))
        
        # Update common fields
        current_user.full_name = full_name
        
        # Email change requires checking for duplicates
        if email != current_user.email:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already in use', 'danger')
                return redirect(url_for('profile'))
            current_user.email = email
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))
    
    # Get patient allergies and medical history for patients
    allergies = []
    medical_history = []
    if current_user.has_role('patient'):
        allergies = PatientAllergy.query.filter_by(user_id=current_user.id).all()
        medical_history = PatientMedicalHistory.query.filter_by(user_id=current_user.id).all()
    
    return render_template('profile.html', user=current_user, allergies=allergies, medical_history=medical_history)

# Prescription scan routes
@app.route('/scan', methods=['GET'])
def scan_page():
    return render_template('scan.html')

@app.route('/process-scan', methods=['POST'])
def process_scan():
    # Check if the post request has the image data
    if 'image_data' not in request.form:
        return jsonify({'error': 'No image data provided'}), 400
    
    try:
        # Get the base64 image data
        image_data = request.form['image_data'].split(',')[1]
        image_bytes = base64.b64decode(image_data)
        
        # Create a temporary file to save the image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(image_bytes)
            temp_file_path = temp_file.name
        
        # Extract text from the image using enhanced OCR with AI capabilities
        extracted_text = extract_text_from_image(temp_file_path)
        
        # Extract structured medication information using AI
        from utils.ocr import extract_medications_from_text
        detected_medications = extract_medications_from_text(extracted_text)
        
        # Map the detected medications to database entries if possible
        medications = []
        
        if detected_medications:
            # First try to match detected medications with our database
            for med_info in detected_medications:
                # Try to find the medication in the database
                med_matches = Medication.query.filter(
                    Medication.name.ilike(f'%{med_info["name"]}%') |
                    Medication.generic_name.ilike(f'%{med_info["name"]}%')
                ).all()
                
                if med_matches:
                    # Use database entries
                    for med in med_matches:
                        medications.append({
                            'id': med.id,
                            'name': med.name,
                            'strength': med.strength,
                            'dosage_form': med.dosage_form,
                            'dosage': med_info.get('dosage', ''),
                            'frequency': med_info.get('frequency', ''),
                            'instructions': med_info.get('instructions', '')
                        })
                else:
                    # Medication not found in database, create a temporary entry
                    # In a real app, you might want to add new medications to the database
                    # or notify pharmacy staff about unknown medications
                    medications.append({
                        'id': f'temp_{len(medications)}',  # Temporary ID
                        'name': med_info.get('name', 'Unknown Medication'),
                        'strength': med_info.get('dosage', ''),
                        'dosage_form': '',
                        'dosage': med_info.get('dosage', ''),
                        'frequency': med_info.get('frequency', ''),
                        'instructions': med_info.get('instructions', '')
                    })
        
        # If AI extraction didn't work, fall back to the simple method
        if not medications:
            logging.info("AI medication extraction didn't find medications, using fallback method")
            for line in extracted_text.split('\n'):
                line = line.strip()
                if line and ('medication:' in line.lower() or 'drug:' in line.lower()):
                    parts = line.split(':')
                    if len(parts) > 1:
                        med_name = parts[1].strip()
                        med_matches = Medication.query.filter(
                            Medication.name.ilike(f'%{med_name}%')
                        ).all()
                        
                        if med_matches:
                            for med in med_matches:
                                medications.append({
                                    'id': med.id,
                                    'name': med.name,
                                    'strength': med.strength,
                                    'dosage_form': med.dosage_form
                                })
        
        # Clean up the temporary file
        os.unlink(temp_file_path)
        
        # Save the scan data to session for later processing
        session['scan_data'] = {
            'extracted_text': extracted_text,
            'medications': medications
        }
        
        return jsonify({
            'success': True,
            'extracted_text': extracted_text,
            'medications': medications
        })
    
    except Exception as e:
        logging.error(f"Error processing scan: {str(e)}")
        return jsonify({'error': f'Error processing image: {str(e)}'}), 500

@app.route('/confirm-prescription', methods=['POST'])
def confirm_prescription():
    if 'scan_data' not in session:
        flash('No prescription scan data found', 'danger')
        return redirect(url_for('scan_page'))
    
    # Get form data
    medication_ids = request.form.getlist('medication_id')
    dosages = request.form.getlist('dosage')
    frequencies = request.form.getlist('frequency')
    durations = request.form.getlist('duration')
    instructions_list = request.form.getlist('instructions')
    
    if not medication_ids:
        flash('No medications selected', 'danger')
        return redirect(url_for('scan_page'))
    
    # For non-logged in users, redirect to public interactions with medication data
    if not current_user.is_authenticated:
        # Store temporary scanned medications in session for the public interaction check
        temp_medications = []
        for i, med_id in enumerate(medication_ids):
            # Check if it's a temporary ID 
            if med_id.startswith('temp_'):
                med_name = request.form.get(f'med_name_{i}', 'Unknown Medication')
                temp_medications.append({
                    'name': med_name,
                    'temp_id': med_id
                })
            else:
                try:
                    medication = Medication.query.get(med_id)
                    if medication:
                        temp_medications.append({
                            'name': medication.name,
                            'id': medication.id
                        })
                except Exception as e:
                    logging.error(f"Error retrieving medication {med_id}: {str(e)}")
        
        # Store in session
        session['temp_medications'] = temp_medications
        
        # Clear scan data
        session.pop('scan_data', None)
        
        # Redirect to public interaction checker with detected medications
        flash('Medications detected. You can check their interactions below, or create an account to save this prescription.', 'info')
        return redirect(url_for('public_interactions'))
    
    try:
        # Create a new prescription for logged-in users
        new_prescription = Prescription(
            user_id=current_user.id,
            status='pending',
            date_prescribed=datetime.utcnow()
        )
        
        # If current user is a doctor, set as the prescribing doctor
        if current_user.has_role('doctor'):
            new_prescription.doctor_id = current_user.id
        
        db.session.add(new_prescription)
        db.session.flush()  # Flush to get the prescription ID
        
        # Add medications to the prescription
        for i, med_id in enumerate(medication_ids):
            try:
                medication = Medication.query.get(med_id)
                if not medication:
                    continue
                
                dosage = dosages[i] if i < len(dosages) else ''
                frequency = frequencies[i] if i < len(frequencies) else ''
                duration = durations[i] if i < len(durations) else ''
                instructions = instructions_list[i] if i < len(instructions_list) else ''
                
                prescription_med = PrescriptionMedication(
                    prescription_id=new_prescription.id,
                    medication_id=med_id,
                    dosage=dosage,
                    frequency=frequency,
                    duration=duration,
                    instructions=instructions
                )
                db.session.add(prescription_med)
            except Exception as e:
                logging.error(f"Error adding medication {med_id} to prescription: {str(e)}")
        
        # Commit changes
        db.session.commit()
        
        # Clear scan data from session
        session.pop('scan_data', None)
        
        # Generate interaction report
        generate_interaction_report(new_prescription.id)
        
        flash('Prescription saved successfully', 'success')
        return redirect(url_for('view_prescription', prescription_id=new_prescription.id))
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error saving prescription: {str(e)}")
        flash(f'Error saving prescription: {str(e)}', 'danger')
        return redirect(url_for('scan_page'))

@app.route('/prescription/<int:prescription_id>')
@login_required
def view_prescription(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    
    # Check if user is authorized to view this prescription
    if not (current_user.id == prescription.user_id or 
            current_user.has_role('doctor') or 
            current_user.has_role('pharmacist')):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get interaction reports for this prescription
    reports = InteractionReport.query.filter_by(prescription_id=prescription_id).order_by(InteractionReport.created_at.desc()).all()
    
    return render_template('interactions.html', prescription=prescription, reports=reports)

# Drug Interaction routes
@app.route('/interactions')
def interactions():
    # Check if user is logged in
    if current_user.is_authenticated:
        # For patients - show their prescriptions and interaction reports
        if current_user.has_role('patient'):
            prescriptions = Prescription.query.filter_by(user_id=current_user.id).order_by(Prescription.date_prescribed.desc()).all()
            return render_template('interactions.html', prescriptions=prescriptions)
        
        # For doctors and pharmacists - show all prescriptions
        prescriptions = Prescription.query.order_by(Prescription.date_prescribed.desc()).limit(20).all()
        return render_template('interactions.html', prescriptions=prescriptions)
    else:
        # For public users, show the public interaction checker
        return render_template('public_interactions.html')

# Public drug interaction checker (no login required)
@app.route('/public-interactions', methods=['GET', 'POST'])
def public_interactions():
    results = None
    scanned_medications = None
    
    # Clear session if requested
    clear_scan = request.args.get('clear_scan', False)
    if clear_scan:
        session.pop('temp_medications', None)
        flash('Scanned medications cleared', 'info')
        return redirect(url_for('public_interactions'))
    
    # Check if we have medications from a scan
    if 'temp_medications' in session:
        scanned_medications = session.get('temp_medications')
    
    if request.method == 'POST':
        # Get selected medication IDs from form
        medication_ids = request.form.getlist('medication_id')
        
        if len(medication_ids) >= 2:
            results = check_drug_interactions(medication_ids)
    
    # Get common drug interactions to display
    common_interactions = DrugInteraction.query.filter_by(severity='severe').limit(5).all()
    
    # Get all medications for the selector
    all_medications = Medication.query.order_by(Medication.name).all()
    
    return render_template('public_interactions.html', 
                         results=results, 
                         common_interactions=common_interactions,
                         all_medications=all_medications,
                         scanned_medications=scanned_medications)

# API endpoint to search medications
@app.route('/api/medications')
def search_medications():
    query = request.args.get('query', '')
    if len(query) < 2:
        return jsonify([])
    
    # Search for medications matching the query
    medications = Medication.query.filter(
        (Medication.name.ilike(f'%{query}%')) | 
        (Medication.generic_name.ilike(f'%{query}%'))
    ).limit(10).all()
    
    # Format results
    results = []
    for med in medications:
        results.append({
            'id': med.id,
            'name': med.name,
            'generic_name': med.generic_name,
            'strength': med.strength,
            'dosage_form': med.dosage_form
        })
    
    return jsonify(results)

def generate_interaction_report(prescription_id):
    """Generate a new interaction report for a prescription"""
    prescription = Prescription.query.get(prescription_id)
    if not prescription:
        return None
    
    # Get medications in prescription
    medications = [pm.medication for pm in prescription.medications]
    if not medications:
        return None
    
    # Create new report
    report = InteractionReport(
        prescription_id=prescription_id,
        created_at=datetime.utcnow(),
        has_interactions=False,
        has_dosage_issues=False,
        summary="Prescription analyzed."
    )
    db.session.add(report)
    db.session.flush()
    
    # Check for drug-drug interactions
    interactions_found = False
    for i, med1 in enumerate(medications):
        for j, med2 in enumerate(medications[i+1:], i+1):
            # Query for interactions between these medications
            interaction = DrugInteraction.query.filter(
                ((DrugInteraction.drug1_id == med1.id) & (DrugInteraction.drug2_id == med2.id)) |
                ((DrugInteraction.drug1_id == med2.id) & (DrugInteraction.drug2_id == med1.id))
            ).first()
            
            if interaction:
                interactions_found = True
                # Record the interaction
                detail = InteractionDetail(
                    report_id=report.id,
                    drug1_id=med1.id,
                    drug2_id=med2.id,
                    interaction_type='drug-drug',
                    severity=interaction.severity,
                    description=interaction.description,
                    recommendation="Consult with healthcare provider before taking these medications together."
                )
                db.session.add(detail)
    
    # Check for patient allergies if patient data is available
    patient = User.query.get(prescription.user_id)
    if patient:
        allergies = PatientAllergy.query.filter_by(user_id=patient.id).all()
        for allergy in allergies:
            for med in medications:
                # Simple string matching for demo purposes
                # In a real app, you'd have a more sophisticated allergen matching system
                if allergy.allergen.lower() in med.name.lower() or allergy.allergen.lower() in med.generic_name.lower():
                    interactions_found = True
                    detail = InteractionDetail(
                        report_id=report.id,
                        drug1_id=med.id,
                        interaction_type='allergy',
                        severity=allergy.severity,
                        description=f"Patient is allergic to {allergy.allergen}",
                        recommendation="Do not administer this medication to this patient."
                    )
                    db.session.add(detail)
    
    # Check for dosage issues
    dosage_issues = False
    for pm in prescription.medications:
        # This is a simplified check - in a real app, you'd have more complex logic
        try:
            med = pm.medication
            dosage_ok = True
            
            # If we have patient data, do more specific checks
            if patient and patient.weight and patient.date_of_birth:
                # Example of a dosage check
                if 'mg' in pm.dosage and int(pm.dosage.split('mg')[0].strip()) > 1000:
                    dosage_ok = False
            
            if not dosage_ok:
                dosage_issues = True
                detail = InteractionDetail(
                    report_id=report.id,
                    drug1_id=med.id,
                    interaction_type='dosage',
                    severity='moderate',
                    description=f"Dosage of {pm.dosage} may be inappropriate",
                    recommendation="Review medication dosage before administration."
                )
                db.session.add(detail)
        except Exception as e:
            logging.error(f"Error checking dosage: {str(e)}")
    
    # Update report summary
    if interactions_found or dosage_issues:
        report.has_interactions = interactions_found
        report.has_dosage_issues = dosage_issues
        summary_parts = []
        if interactions_found:
            summary_parts.append("Drug interactions detected")
        if dosage_issues:
            summary_parts.append("Dosage issues detected")
        report.summary = ". ".join(summary_parts) + ". Review recommended."
    else:
        report.summary = "No interactions or dosage issues detected."
    
    db.session.commit()
    return report

# Dosage verification routes
@app.route('/dosage')
@login_required
def dosage():
    # This is mainly for doctors and pharmacists
    if not (current_user.has_role('doctor') or current_user.has_role('pharmacist')):
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all medications for dosage reference
    medications = Medication.query.order_by(Medication.name).all()
    
    return render_template('dosage.html', medications=medications)

@app.route('/verify-dosage', methods=['POST'])
@login_required
def verify_dosage_route():
    if not (current_user.has_role('doctor') or current_user.has_role('pharmacist')):
        return jsonify({'error': 'Unauthorized'}), 403
    
    medication_id = request.form.get('medication_id')
    dosage = request.form.get('dosage')
    patient_weight = request.form.get('patient_weight')
    patient_age = request.form.get('patient_age')
    
    if not all([medication_id, dosage]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        # Get the medication
        medication = Medication.query.get(medication_id)
        if not medication:
            return jsonify({'error': 'Medication not found'}), 404
        
        # Convert weight and age to numbers if provided
        weight = float(patient_weight) if patient_weight else None
        age = int(patient_age) if patient_age else None
        
        # Call the dosage verification utility
        result = verify_dosage(medication, dosage, weight, age)
        
        return jsonify(result)
    
    except Exception as e:
        logging.error(f"Error verifying dosage: {str(e)}")
        return jsonify({'error': f'Error verifying dosage: {str(e)}'}), 500

# Inventory tracking routes
@app.route('/inventory')
@login_required
def inventory():
    # Only pharmacists should access inventory
    if not current_user.has_role('pharmacist'):
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    medications = Medication.query.order_by(Medication.name).all()
    
    # Get recent inventory logs
    logs = InventoryLog.query.order_by(InventoryLog.timestamp.desc()).limit(10).all()
    
    return render_template('inventory.html', medications=medications, logs=logs)

@app.route('/update-inventory', methods=['POST'])
@login_required
def update_inventory_route():
    if not current_user.has_role('pharmacist'):
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    medication_id = request.form.get('medication_id')
    quantity_change = request.form.get('quantity_change')
    reason = request.form.get('reason')
    
    if not all([medication_id, quantity_change, reason]):
        flash('All fields are required', 'danger')
        return redirect(url_for('inventory'))
    
    try:
        medication = Medication.query.get(medication_id)
        if not medication:
            flash('Medication not found', 'danger')
            return redirect(url_for('inventory'))
        
        # Convert quantity to integer
        quantity = int(quantity_change)
        
        # Update inventory
        update_inventory(medication.id, quantity, reason, current_user.id)
        
        flash('Inventory updated successfully', 'success')
    except Exception as e:
        flash(f'Error updating inventory: {str(e)}', 'danger')
    
    return redirect(url_for('inventory'))

# Reporting routes
@app.route('/reports')
@login_required
def reports():
    # All users can access reports, but content varies by role
    if current_user.has_role('patient'):
        # Patients see only their own reports
        interaction_reports = InteractionReport.query.join(Prescription).filter(
            Prescription.user_id == current_user.id
        ).order_by(InteractionReport.created_at.desc()).limit(20).all()
    elif current_user.has_role('doctor'):
        # Doctors see reports for their patients
        interaction_reports = InteractionReport.query.join(Prescription).filter(
            Prescription.doctor_id == current_user.id
        ).order_by(InteractionReport.created_at.desc()).limit(20).all()
    else:
        # Pharmacists see all reports
        interaction_reports = InteractionReport.query.order_by(InteractionReport.created_at.desc()).limit(20).all()
    
    return render_template('reports.html', reports=interaction_reports)

@app.route('/report/<int:report_id>')
@login_required
def view_report(report_id):
    report = InteractionReport.query.get_or_404(report_id)
    prescription = Prescription.query.get(report.prescription_id)
    
    # Verify user has permission to view this report
    if (current_user.has_role('patient') and prescription.user_id != current_user.id and 
        not (current_user.has_role('doctor') or current_user.has_role('pharmacist'))):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('reports.html', report=report, prescription=prescription)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# Initialize database with sample data
@app.cli.command("init-db")
def init_db_command():
    """Initialize the database with sample data."""
    # Add sample medications
    medications = [
        {
            "name": "Ibuprofen", 
            "generic_name": "Ibuprofen",
            "description": "Non-steroidal anti-inflammatory drug",
            "dosage_form": "tablet",
            "strength": "200mg",
            "stock_quantity": 100
        },
        {
            "name": "Acetaminophen", 
            "generic_name": "Paracetamol",
            "description": "Pain reliever and fever reducer",
            "dosage_form": "tablet",
            "strength": "500mg",
            "stock_quantity": 150
        },
        {
            "name": "Aspirin", 
            "generic_name": "Acetylsalicylic acid",
            "description": "Pain reliever, anti-inflammatory, and anti-platelet",
            "dosage_form": "tablet",
            "strength": "325mg",
            "stock_quantity": 75
        },
        {
            "name": "Lisinopril", 
            "generic_name": "Lisinopril",
            "description": "ACE inhibitor for high blood pressure",
            "dosage_form": "tablet",
            "strength": "10mg",
            "stock_quantity": 50
        },
        {
            "name": "Warfarin", 
            "generic_name": "Warfarin",
            "description": "Anticoagulant",
            "dosage_form": "tablet",
            "strength": "5mg",
            "stock_quantity": 30
        }
    ]
    
    for med_data in medications:
        med = Medication.query.filter_by(name=med_data["name"], strength=med_data["strength"]).first()
        if not med:
            med = Medication(**med_data)
            db.session.add(med)
    
    # Add sample drug interactions
    interactions = [
        {
            "drug1_name": "Warfarin",
            "drug2_name": "Aspirin",
            "severity": "severe",
            "description": "Increased risk of bleeding when taking warfarin with aspirin."
        },
        {
            "drug1_name": "Lisinopril",
            "drug2_name": "Ibuprofen",
            "severity": "moderate",
            "description": "NSAIDs like ibuprofen may reduce the efficacy of ACE inhibitors like lisinopril."
        },
        {
            "drug1_name": "Warfarin",
            "drug2_name": "Ibuprofen",
            "severity": "severe",
            "description": "Increased risk of bleeding when taking warfarin with NSAIDs like ibuprofen."
        },
        {
            "drug1_name": "Acetaminophen",
            "drug2_name": "Warfarin",
            "severity": "moderate",
            "description": "Frequent use of acetaminophen can increase the effect of warfarin, potentially leading to an increased risk of bleeding."
        },
        {
            "drug1_name": "Ibuprofen",
            "drug2_name": "Aspirin",
            "severity": "moderate",
            "description": "Taking NSAIDs like ibuprofen with aspirin can increase the risk of stomach bleeding and ulcers."
        }
    ]
    
    for interaction_data in interactions:
        drug1 = Medication.query.filter_by(name=interaction_data["drug1_name"]).first()
        drug2 = Medication.query.filter_by(name=interaction_data["drug2_name"]).first()
        
        if drug1 and drug2:
            # Check if interaction already exists
            existing = DrugInteraction.query.filter(
                ((DrugInteraction.drug1_id == drug1.id) & (DrugInteraction.drug2_id == drug2.id)) |
                ((DrugInteraction.drug1_id == drug2.id) & (DrugInteraction.drug2_id == drug1.id))
            ).first()
            
            if not existing:
                interaction = DrugInteraction(
                    drug1_id=drug1.id,
                    drug2_id=drug2.id,
                    severity=interaction_data["severity"],
                    description=interaction_data["description"]
                )
                db.session.add(interaction)
    
    db.session.commit()
    print("Database initialized with sample data.")

# Create a command to initialize the database
with app.app_context():
    app.cli.command("init-db")(init_db_command)
