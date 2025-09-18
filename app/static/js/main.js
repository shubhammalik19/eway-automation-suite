/**
 * EwayAuto - Main JavaScript using jQuery and jQuery UI
 */

$(document).ready(function() {
    // Initialize the application
    initializeApp();
    
    // Start checking auth status periodically
    setInterval(checkAuthStatus, 30000); // Check every 30 seconds
});

// Global variables
let currentSession = null;
let operationWebSocket = null;

/**
 * Initialize the application
 */
function initializeApp() {
    console.log('Initializing EwayAuto application...');
    
    // Initialize jQuery UI components
    initializeJQueryUI();
    
    // Bind events
    bindEvents();
    
    // Check existing session
    checkSessionStatus();
    
    // Check auth status immediately
    checkAuthStatus();
    
    // Load dashboard stats
    loadDashboardStats();
    
    // Initialize dashboard (no login form needed)
}

/**
 * Check authentication status and update UI
 */
function checkAuthStatus() {
    $.ajax({
        url: '/api/auth/status',
        method: 'GET',
        success: function(response) {
            updateAuthUI(response);
        },
        error: function(xhr, status, error) {
            console.error('Auth status check failed:', error);
            updateAuthUI({ success: false, logged_in: false });
        }
    });
}

/**
 * Update authentication UI based on status
 */
function updateAuthUI(authStatus) {
    const statusIcon = $('#session-status i');
    const statusText = $('#status-text');
    const authButton = $('#auth-button');
    
    if (authStatus.success && authStatus.logged_in) {
        // User is logged in
        statusIcon.removeClass('text-danger').addClass('text-success');
        statusText.text(`Logged In (${authStatus.active_sessions} sessions)`);
        
        authButton.html('<i class="fas fa-sign-out-alt"></i> Logout')
                  .removeClass('btn-outline-light')
                  .addClass('btn-outline-warning')
                  .attr('onclick', 'handleLogout()');
    } else {
        // User is not logged in
        statusIcon.removeClass('text-success').addClass('text-danger');
        statusText.text('Not Logged In');
        
        authButton.html('<i class="fas fa-sign-in-alt"></i> Login')
                  .removeClass('btn-outline-warning')
                  .addClass('btn-outline-light')
                  .attr('onclick', 'handleLogin()');
    }
}

/**
 * Handle login button click
 */
function handleLogin() {
    const button = $('#auth-button');
    const originalText = button.html();
    
    // Show loading state
    button.html('<i class="fas fa-spinner fa-spin"></i> Starting Login...').prop('disabled', true);
    
    $.ajax({
        url: '/api/auth/trigger-login',
        method: 'POST',
        success: function(response) {
            if (response.success) {
                showNotification('Login browser opened! Complete the login process in the browser window.', 'info');
                
                // Start checking for successful login
                const checkInterval = setInterval(() => {
                    checkAuthStatus();
                }, 3000);
                
                // Stop checking after 5 minutes
                setTimeout(() => {
                    clearInterval(checkInterval);
                }, 300000);
                
            } else {
                showNotification('Failed to start login process: ' + response.message, 'error');
            }
        },
        error: function(xhr, status, error) {
            console.error('Login trigger failed:', error);
            showNotification('Failed to start login process', 'error');
        },
        complete: function() {
            // Restore button
            button.html(originalText).prop('disabled', false);
        }
    });
}

/**
 * Handle logout button click
 */
function handleLogout() {
    if (!confirm('Are you sure you want to logout and clear all sessions?')) {
        return;
    }
    
    const button = $('#auth-button');
    const originalText = button.html();
    
    // Show loading state
    button.html('<i class="fas fa-spinner fa-spin"></i> Logging out...').prop('disabled', true);
    
    $.ajax({
        url: '/api/auth/logout',
        method: 'POST',
        success: function(response) {
            if (response.success) {
                showNotification(`Logged out successfully. Cleared ${response.cleared_sessions} sessions.`, 'success');
                checkAuthStatus(); // Update UI immediately
            } else {
                showNotification('Logout failed: ' + response.message, 'error');
            }
        },
        error: function(xhr, status, error) {
            console.error('Logout failed:', error);
            showNotification('Logout failed', 'error');
        },
        complete: function() {
            // Restore button
            button.html(originalText).prop('disabled', false);
        }
    });
}

/**
 * Handle auth button click (dynamic function)
 */
function handleAuthAction() {
    // This function is called by the button onclick, but we redirect to specific handlers
    const isLoggedIn = $('#session-status i').hasClass('text-success');
    
    if (isLoggedIn) {
        handleLogout();
    } else {
        handleLogin();
    }
}

/**
 * Load CAPTCHA automatically
 */
function loadCaptchaAutomatically() {
    console.log('Auto-loading CAPTCHA...');
    refreshCaptcha();
}

/**
 * Initialize jQuery UI components
 */
function initializeJQueryUI() {
    // Initialize datepickers for any date inputs
    $('.datepicker').datepicker({
        dateFormat: 'dd/mm/yy',
        changeMonth: true,
        changeYear: true,
        yearRange: '-10:+2'
    });
    
    // Initialize tooltips
    $('[title]').tooltip({
        position: { my: "left+15 center", at: "right center" }
    });
    
    // Initialize progress bars
    $('.progress-bar').progressbar({
        value: 0
    });
}

/**
 * Bind event handlers
 */
function bindEvents() {
    // CAPTCHA refresh button
    $('#refresh-captcha').on('click', refreshCaptcha);
    
    // CAPTCHA input - prevent uppercase and force lowercase
    $(document).on('input', '#captcha-input', function() {
        const $this = $(this);
        const value = $this.val();
        const lowerValue = value.toLowerCase();
        if (value !== lowerValue) {
            $this.val(lowerValue);
        }
    });
    
    // Feature card clicks
    $('.feature-card').on('click', handleFeatureClick);
    
    // File upload handling
    $(document).on('change', '.file-upload', handleFileUpload);
    
    // Modal events
    $('#progress-modal').on('hidden.bs.modal', function() {
        // Clean up when modal is closed
        if (operationWebSocket) {
            operationWebSocket.close();
        }
    });
    
    // Auto-refresh session every 5 minutes
    setInterval(checkSessionStatus, 5 * 60 * 1000);
}

/**
 * Handle login form submission
 */
/**
 * Show CAPTCHA section and load image
 */
function showCaptcha(captchaImageData, captchaImageUrl) {
    const $captchaSection = $('#captcha-section');
    const $captchaImage = $('#captcha-image');
    const $captchaLoading = $('#captcha-loading');
    const $captchaInput = $('#captcha-input');
    
    // Show the CAPTCHA section
    $captchaSection.removeClass('d-none');
    
    // Enable the CAPTCHA input and make it required
    $captchaInput.prop('disabled', false).attr('required', true);
    
    if (captchaImageData) {
        // Hide loading, show image with base64 data
        $captchaLoading.addClass('d-none');
        $captchaImage.removeClass('d-none');
        $captchaImage.attr('src', 'data:image/png;base64,' + captchaImageData);
        
        // Focus on CAPTCHA input
        $captchaInput.focus();
    } else if (captchaImageUrl) {
        // Hide loading, show image with URL
        $captchaLoading.addClass('d-none');
        $captchaImage.removeClass('d-none');
        $captchaImage.attr('src', captchaImageUrl);
        
        // Focus on CAPTCHA input
        $captchaInput.focus();
    } else {
        // Show loading state
        $captchaLoading.removeClass('d-none');
        $captchaImage.addClass('d-none');
        
        // Try to fetch CAPTCHA
        refreshCaptcha();
    }
}

/**
 * Refresh CAPTCHA image
 */
function refreshCaptcha() {
    const $captchaLoading = $('#captcha-loading');
    const $captchaImage = $('#captcha-image');
    const $captchaInput = $('#captcha-input');
    
    console.log('Refreshing CAPTCHA...');
    
    // Show loading state
    $captchaLoading.removeClass('d-none');
    $captchaImage.addClass('d-none');
    $captchaInput.val('');
    
    // Request new CAPTCHA
    $.ajax({
        url: '/api/auth/captcha',
        method: 'GET',
        timeout: 10000, // 10 second timeout
        success: function(response) {
            console.log('CAPTCHA response received:', response);
            if (response.success && response.captcha_image) {
                $captchaLoading.addClass('d-none');
                $captchaImage.removeClass('d-none');
                $captchaImage.attr('src', 'data:image/png;base64,' + response.captcha_image);
                $captchaInput.focus();
                console.log('CAPTCHA displayed successfully');
            } else {
                console.error('CAPTCHA response error:', response);
                showMessage($('#login-message'), 'Failed to load CAPTCHA: ' + (response.message || 'Unknown error'), 'danger');
            }
        },
        error: function(xhr, status, error) {
            console.error('CAPTCHA request failed:', status, error);
            $captchaLoading.addClass('d-none');
            showMessage($('#login-message'), 'Failed to refresh CAPTCHA. Please try again.', 'danger');
        }
    });
}

/**
 * Handle feature card clicks
 */
function handleFeatureClick() {
    const feature = $(this).data('feature');
    
    switch(feature) {
        case 'extend-single':
            showSingleExtensionModal();
            break;
        case 'bulk-extend':
            showBulkExtensionModal();
            break;
        case 'vehicle-data':
            showVehicleDataModal();
            break;
        default:
            console.warn('Unknown feature:', feature);
    }
}

/**
 * Show single E-way extension modal
 */
function showSingleExtensionModal() {
    const modalHtml = `
        <div class="modal fade" id="single-extension-modal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-file-invoice"></i> Single E-way Extension
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="single-extension-form">
                            <div class="mb-3">
                                <label for="ewb-number" class="form-label">E-way Bill Number</label>
                                <input type="text" class="form-control" id="ewb-number" 
                                       placeholder="12345678901" maxlength="12" required>
                            </div>
                            <div class="mb-3">
                                <label for="vehicle-number" class="form-label">Vehicle Number (Optional)</label>
                                <input type="text" class="form-control" id="vehicle-number" 
                                       placeholder="MH01AA1234">
                            </div>
                            <div class="mb-3">
                                <label for="kilometers" class="form-label">Kilometers (Optional)</label>
                                <input type="number" class="form-control" id="kilometers" 
                                       placeholder="150" step="0.1">
                            </div>
                            <div class="mb-3">
                                <label for="reason" class="form-label">Extension Reason</label>
                                <select class="form-control" id="reason">
                                    <option value="Vehicle Breakdown">Vehicle Breakdown</option>
                                    <option value="Traffic Jam">Traffic Jam</option>
                                    <option value="Other">Other</option>
                                </select>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="submitSingleExtension()">
                            <i class="fas fa-play"></i> Extend E-way Bill
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    $('#single-extension-modal').remove();
    
    // Add modal to DOM and show
    $('body').append(modalHtml);
    $('#single-extension-modal').modal('show');
    
    // Initialize form validation
    $('#single-extension-form').on('submit', function(e) {
        e.preventDefault();
        submitSingleExtension();
    });
}

/**
 * Show bulk extension modal
 */
function showBulkExtensionModal() {
    const modalHtml = `
        <div class="modal fade" id="bulk-extension-modal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-table"></i> Bulk CSV Extension
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label for="csv-file" class="form-label">Select CSV File</label>
                            <input type="file" class="form-control file-upload" id="csv-file" 
                                   accept=".csv" required>
                            <div class="form-text">
                                Expected columns: EWB.No, Valid Untill, From Place, To Place, Document No
                            </div>
                        </div>
                        <div class="form-check mb-3">
                            <input class="form-check-input" type="checkbox" id="filter-today" checked>
                            <label class="form-check-label" for="filter-today">
                                Process only bills expiring today
                            </label>
                        </div>
                        <div id="csv-preview" class="d-none">
                            <h6>CSV Preview:</h6>
                            <div class="table-responsive">
                                <table class="table table-sm table-bordered" id="csv-preview-table">
                                    <thead></thead>
                                    <tbody></tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-success" id="start-bulk-extension" disabled>
                            <i class="fas fa-upload"></i> Start Bulk Extension
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    $('#bulk-extension-modal').remove();
    
    // Add modal to DOM and show
    $('body').append(modalHtml);
    $('#bulk-extension-modal').modal('show');
    
    // Bind file upload handler
    $('#csv-file').on('change', handleCSVFileSelect);
    $('#start-bulk-extension').on('click', submitBulkExtension);
}

/**
 * Handle file upload changes
 */
function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const $input = $(this);
    const fileType = $input.attr('accept');
    
    // Validate file type
    if (fileType && !file.type.match(fileType.replace('*', ''))) {
        showAlert(`Invalid file type. Expected: ${fileType}`, 'danger');
        $input.val('');
        return;
    }
    
    // Update UI to show selected file
    const fileName = file.name;
    const $label = $input.siblings('.form-label');
    if ($label.length) {
        $label.text(`Selected: ${fileName}`);
    }
    
    console.log('File selected:', fileName, 'Size:', file.size, 'bytes');
}

/**
 * Handle CSV file selection
 */
function handleCSVFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const csvContent = e.target.result;
        previewCSV(csvContent);
        $('#start-bulk-extension').prop('disabled', false);
    };
    reader.readAsText(file);
}

/**
 * Preview CSV content
 */
function previewCSV(csvContent) {
    const lines = csvContent.split('\n').filter(line => line.trim());
    if (lines.length < 2) return;
    
    const headers = lines[0].split(',');
    const rows = lines.slice(1, 6); // Show first 5 rows
    
    let headerHtml = '<tr>';
    headers.forEach(header => {
        headerHtml += `<th>${header.trim()}</th>`;
    });
    headerHtml += '</tr>';
    
    let bodyHtml = '';
    rows.forEach(row => {
        const cells = row.split(',');
        bodyHtml += '<tr>';
        cells.forEach(cell => {
            bodyHtml += `<td>${cell.trim()}</td>`;
        });
        bodyHtml += '</tr>';
    });
    
    $('#csv-preview-table thead').html(headerHtml);
    $('#csv-preview-table tbody').html(bodyHtml);
    $('#csv-preview').removeClass('d-none');
}

/**
 * Submit single extension request
 */
function submitSingleExtension() {
    const data = {
        ewb_number: $('#ewb-number').val(),
        vehicle_number: $('#vehicle-number').val() || null,
        kilometers: parseFloat($('#kilometers').val()) || null,
        reason: $('#reason').val()
    };
    
    if (!data.ewb_number) {
        showAlert('Please enter E-way Bill number', 'danger');
        return;
    }
    
    startOperation('single-extension', data);
    $('#single-extension-modal').modal('hide');
}

/**
 * Submit bulk extension request
 */
function submitBulkExtension() {
    const fileInput = $('#csv-file')[0];
    if (!fileInput.files[0]) {
        showAlert('Please select a CSV file', 'danger');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const data = {
            csv_data: btoa(e.target.result), // Base64 encode
            filename: fileInput.files[0].name,
            filter_today_only: $('#filter-today').is(':checked')
        };
        
        startOperation('bulk-extension', data);
        $('#bulk-extension-modal').modal('hide');
    };
    reader.readAsText(fileInput.files[0]);
}

/**
 * Start an operation with progress tracking
 */
function startOperation(operationType, data) {
    // Show progress modal
    $('#progress-modal').modal('show');
    updateOperationProgress(0, 'Starting operation...');
    
    // Start the operation
    $.ajax({
        url: `/api/automation/${operationType}`,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function(response) {
            if (response.operation_id) {
                // Start WebSocket for progress updates
                connectToOperationWebSocket(response.operation_id);
            }
        },
        error: function(xhr, status, error) {
            const errorMsg = xhr.responseJSON?.detail || 'Operation failed to start';
            updateOperationProgress(0, 'Error: ' + errorMsg);
            setTimeout(() => {
                $('#progress-modal').modal('hide');
            }, 3000);
        }
    });
}

/**
 * Connect to WebSocket for operation progress
 */
function connectToOperationWebSocket(operationId) {
    const wsUrl = `ws://localhost:8000/ws/operation/${operationId}`;
    operationWebSocket = new WebSocket(wsUrl);
    
    operationWebSocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.type === 'progress') {
            updateOperationProgress(data.progress, data.message, data.details);
        } else if (data.type === 'completed') {
            updateOperationProgress(100, 'Operation completed successfully!');
            setTimeout(() => {
                $('#progress-modal').modal('hide');
                loadDashboardStats(); // Refresh stats
            }, 2000);
        } else if (data.type === 'error') {
            updateOperationProgress(data.progress || 0, 'Error: ' + data.message);
            setTimeout(() => {
                $('#progress-modal').modal('hide');
            }, 3000);
        }
    };
    
    operationWebSocket.onerror = function(error) {
        updateOperationProgress(0, 'Connection error');
        setTimeout(() => {
            $('#progress-modal').modal('hide');
        }, 3000);
    };
}

/**
 * Update operation progress
 */
function updateOperationProgress(progress, status, details = '') {
    $('#operation-progress').css('width', progress + '%');
    $('#operation-status').text(status);
    $('#operation-details').text(details);
}

/**
 * Check session status
 */
function checkSessionStatus() {
    $.ajax({
        url: '/api/auth/session',
        method: 'GET',
        success: function(response) {
            if (response.is_logged_in) {
                updateSessionIndicator(true, response.username);
                if ($('#dashboard-section').hasClass('d-none')) {
                    showDashboard();
                }
            } else {
                updateSessionIndicator(false);
                showLogin();
            }
        },
        error: function() {
            updateSessionIndicator(false);
            showLogin();
        }
    });
}

/**
 * Update session indicator in navbar
 */
function updateSessionIndicator(isLoggedIn, username = '') {
    const $indicator = $('#session-status');
    
    if (isLoggedIn) {
        $indicator.html(`
            <i class="fas fa-circle text-success"></i> 
            Logged in as ${username}
        `);
    } else {
        $indicator.html(`
            <i class="fas fa-circle text-danger"></i> 
            Not Logged In
        `);
    }
}

/**
 * Show dashboard section
 */
function showDashboard() {
    $('#dashboard-section').removeClass('d-none');
    loadDashboardStats();
}

/**
 * Show login section
 */
function showLogin() {
    $('#dashboard-section').removeClass('d-none');
}

/**
 * Load dashboard statistics
 */
function loadDashboardStats() {
    $.ajax({
        url: '/api/dashboard/stats',
        method: 'GET',
        success: function(stats) {
            $('#total-bills').text(stats.total_eway_bills);
            $('#pending-extensions').text(stats.pending_extensions);
            $('#successful-extensions').text(stats.successful_extensions);
            $('#failed-extensions').text(stats.failed_extensions);
        },
        error: function() {
            console.warn('Failed to load dashboard stats');
        }
    });
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Add alert to top of page
    $('body').prepend(alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        $('.alert').alert('close');
    }, 5000);
}

/**
 * Show message in a specific container
 */
function showMessage($container, message, type = 'info') {
    const messageHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    $container.html(messageHtml);
}
