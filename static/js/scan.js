// scan.js - JavaScript for the prescription scanning functionality

let scanner = null;
let videoStream = null;

/**
 * Initialize the prescription scanner
 */
function initScanner() {
    const scanButton = document.getElementById('scan-button');
    const cameraSelect = document.getElementById('camera-select');
    const videoElement = document.getElementById('camera-feed');
    const captureButton = document.getElementById('capture-button');
    const scanResult = document.getElementById('scan-result');
    const scanPreview = document.getElementById('scan-preview');
    const loadingIndicator = document.getElementById('loading-indicator');
    const medListContainer = document.getElementById('medication-list');
    
    // Check if required elements exist
    if (!scanButton || !videoElement || !captureButton) {
        console.error('Required scanner elements not found');
        return;
    }
    
    // Function to get available cameras
    const getAvailableCameras = async () => {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            
            // Clear and populate the camera select dropdown
            if (cameraSelect) {
                cameraSelect.innerHTML = '';
                videoDevices.forEach((device, index) => {
                    const option = document.createElement('option');
                    option.value = device.deviceId;
                    option.text = device.label || `Camera ${index + 1}`;
                    cameraSelect.appendChild(option);
                });
            }
            
            return videoDevices;
        } catch (error) {
            console.error('Error getting cameras:', error);
            showAlert('Error accessing cameras: ' + error.message, 'danger');
            return [];
        }
    };
    
    // Function to start the camera
    const startCamera = async (deviceId = null) => {
        try {
            if (videoStream) {
                // Stop any existing stream
                videoStream.getTracks().forEach(track => track.stop());
            }
            
            const constraints = {
                video: deviceId ? { deviceId: { exact: deviceId } } : true,
                audio: false
            };
            
            videoStream = await navigator.mediaDevices.getUserMedia(constraints);
            videoElement.srcObject = videoStream;
            
            // Show video container and capture button
            document.getElementById('camera-container').classList.remove('d-none');
            captureButton.classList.remove('d-none');
            
            return true;
        } catch (error) {
            console.error('Error starting camera:', error);
            showAlert('Error starting camera: ' + error.message, 'danger');
            return false;
        }
    };
    
    // Camera selection change
    if (cameraSelect) {
        cameraSelect.addEventListener('change', () => {
            const deviceId = cameraSelect.value;
            startCamera(deviceId);
        });
    }
    
    // Scan button click
    scanButton.addEventListener('click', async () => {
        const cameras = await getAvailableCameras();
        
        if (cameras.length === 0) {
            showAlert('No cameras found on your device', 'warning');
            return;
        }
        
        // Start with the first camera or the selected one
        const deviceId = cameraSelect ? cameraSelect.value : cameras[0].deviceId;
        const started = await startCamera(deviceId);
        
        if (started) {
            // Hide the scan button and show the capture button
            scanButton.classList.add('d-none');
            captureButton.classList.remove('d-none');
        }
    });
    
    // Capture button click
    captureButton.addEventListener('click', () => {
        // Create a canvas and draw the video frame
        const canvas = document.createElement('canvas');
        canvas.width = videoElement.videoWidth;
        canvas.height = videoElement.videoHeight;
        
        const context = canvas.getContext('2d');
        context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
        
        // Get the image as base64 data URL
        const imageDataUrl = canvas.toDataURL('image/jpeg');
        
        // Show preview
        scanPreview.src = imageDataUrl;
        scanPreview.classList.remove('d-none');
        
        // Show loading indicator
        loadingIndicator.classList.remove('d-none');
        
        // Send the image for processing
        processScan(imageDataUrl);
    });
    
    /**
     * Process the scanned prescription image
     * @param {string} imageDataUrl - Base64 encoded image data
     */
    function processScan(imageDataUrl) {
        // Create form data for the image
        const formData = new FormData();
        formData.append('image_data', imageDataUrl);
        
        // Send to the server for OCR processing
        fetch('/process-scan', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading indicator
            loadingIndicator.classList.add('d-none');
            
            if (data.error) {
                showAlert('Error processing image: ' + data.error, 'danger');
                return;
            }
            
            // Display extracted text
            if (scanResult) {
                scanResult.classList.remove('d-none');
                scanResult.textContent = data.extracted_text;
            }
            
            // Display detected medications
            if (medListContainer && data.medications && data.medications.length > 0) {
                // Create a form for the detected medications
                let formHtml = '<div class="card mb-4"><div class="card-header bg-success text-white">';
                formHtml += '<h4 class="mb-0"><i class="fas fa-pills me-2"></i>AI-Detected Medications</h4></div>';
                formHtml += '<div class="card-body">';
                formHtml += '<form id="medications-form" action="/confirm-prescription" method="post">';
                formHtml += '<div class="list-group mb-4">';
                
                data.medications.forEach((med, index) => {
                    const isTemporary = String(med.id).startsWith('temp_');
                    const badgeClass = isTemporary ? 'badge bg-warning' : 'badge bg-success';
                    const badgeText = isTemporary ? 'New Medication' : 'In Database';
                    
                    formHtml += `
                    <div class="list-group-item ${isTemporary ? 'border-warning' : ''}">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="medication_id" id="med-${med.id}" value="${med.id}" checked>
                                <label class="form-check-label" for="med-${med.id}">
                                    <strong>${med.name}</strong> ${med.strength || ''} ${med.dosage_form || ''}
                                </label>
                            </div>
                            <span class="${badgeClass}">${badgeText}</span>
                        </div>
                        <div class="row mt-2">
                            <div class="col-md-6 mb-2">
                                <label for="dosage-${med.id}" class="form-label">Dosage</label>
                                <input type="text" class="form-control" id="dosage-${med.id}" name="dosage" 
                                       value="${med.dosage || ''}" placeholder="e.g., 1 tablet, 5ml">
                            </div>
                            <div class="col-md-6 mb-2">
                                <label for="frequency-${med.id}" class="form-label">Frequency</label>
                                <input type="text" class="form-control" id="frequency-${med.id}" name="frequency" 
                                       value="${med.frequency || ''}" placeholder="e.g., twice daily">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-2">
                                <label for="duration-${med.id}" class="form-label">Duration</label>
                                <input type="text" class="form-control" id="duration-${med.id}" name="duration" placeholder="e.g., 7 days">
                            </div>
                            <div class="col-md-6 mb-2">
                                <label for="instructions-${med.id}" class="form-label">Instructions</label>
                                <input type="text" class="form-control" id="instructions-${med.id}" name="instructions" 
                                       value="${med.instructions || ''}" placeholder="e.g., take with food">
                            </div>
                        </div>
                    </div>
                    `;
                });
                
                formHtml += '</div>';
                formHtml += '<div class="d-flex justify-content-between">';
                formHtml += '<button type="button" id="add-medication-btn" class="btn btn-outline-primary"><i class="fas fa-plus me-2"></i>Add Medication</button>';
                formHtml += '<button type="submit" class="btn btn-primary"><i class="fas fa-save me-2"></i>Save Prescription</button>';
                formHtml += '</div></form></div></div>';
                
                medListContainer.innerHTML = formHtml;
                medListContainer.classList.remove('d-none');
                
                // Add event listener for "Add Medication" button
                const addMedBtn = document.getElementById('add-medication-btn');
                if (addMedBtn) {
                    addMedBtn.addEventListener('click', () => {
                        // Show modal with medication search
                        showAlert('Manual medication entry is not yet implemented. This feature will allow adding medications not detected by AI.', 'info');
                    });
                }
            } else if (medListContainer) {
                medListContainer.innerHTML = `
                <div class="alert alert-info">
                    <h5><i class="fas fa-info-circle me-2"></i>No medications detected</h5>
                    <p>The AI couldn't identify medications in the scanned prescription. Please try:</p>
                    <ul>
                        <li>Scanning again with better lighting</li>
                        <li>Making sure the prescription text is clearly visible</li>
                        <li>Using a different angle</li>
                        <li>Manually entering medications if scanning doesn't work</li>
                    </ul>
                    <button id="scan-again-btn" class="btn btn-primary"><i class="fas fa-redo me-2"></i>Scan Again</button>
                </div>`;
                medListContainer.classList.remove('d-none');
                
                // Add event listener for the "Scan Again" button
                const scanAgainBtn = document.getElementById('scan-again-btn');
                if (scanAgainBtn) {
                    scanAgainBtn.addEventListener('click', () => {
                        // Reset the UI for another scan
                        scanResult.classList.add('d-none');
                        scanPreview.classList.add('d-none');
                        medListContainer.classList.add('d-none');
                        document.getElementById('text-extraction-heading').classList.add('d-none');
                        
                        // Show scan button if hidden
                        const scanButton = document.getElementById('scan-button');
                        if (scanButton.classList.contains('d-none')) {
                            scanButton.classList.remove('d-none');
                        }
                    });
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            loadingIndicator.classList.add('d-none');
            showAlert('An error occurred while processing the image', 'danger');
        });
    }
}

/**
 * Stop all camera streams
 */
function stopCameraStream() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
}

// Cleanup when navigating away
window.addEventListener('beforeunload', stopCameraStream);
