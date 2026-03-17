/* =============================================
   QueueSense - API Module
   Handles all API requests to the backend
   ============================================= */

// API Configuration
const API_PORT = 5000;
const API_BASE = (() => {
    // If we're already on the backend port, use relative paths
    if (window.location.port == API_PORT) return '/api';
    // Fallback for local development or file protocol
    const host = window.location.hostname || '127.0.0.1';
    const cleanHost = (host === 'localhost') ? '127.0.0.1' : host;
    return `http://${cleanHost}:${API_PORT}/api`;
})();
console.log('%c[QueueSense] API Connected:', 'color: #39FF14; font-weight: bold;', API_BASE);

// =============================================
// API Request Helper
// Wraps fetch with auth headers and error handling
// =============================================
async function apiRequest(endpoint, options = {}) {
    // Get auth token from localStorage
    const token = localStorage.getItem('qs_token');

    // Default headers
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    // Add auth header if token exists
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Make the request
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });

        // Parse response
        const data = await response.json();

        // Check for auth errors
        if (response.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('qs_token');
            localStorage.removeItem('qs_user');
            window.location.href = '/login.html';
            return null;
        }

        // Return response data with status
        return {
            ok: response.ok,
            status: response.status,
            data
        };
    } catch (error) {
        console.error('API Error:', error);
        return {
            ok: false,
            status: 0,
            data: { error: 'Network error. Please check your connection.' }
        };
    }
}

// =============================================
// Auth API
// =============================================
const AuthAPI = {
    // Login
    login: async (username, password) => {
        return await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
    },

    // Register
    register: async (userData) => {
        return await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    },

    // Get current user profile
    getProfile: async () => {
        return await apiRequest('/auth/me');
    },

    // Update profile
    updateProfile: async (userData) => {
        return await apiRequest('/auth/profile', {
            method: 'PUT',
            body: JSON.stringify(userData)
        });
    },

    // Change password
    changePassword: async (passwordData) => {
        return await apiRequest('/auth/password', {
            method: 'PUT',
            body: JSON.stringify(passwordData)
        });
    },

    // Logout
    logout: () => {
        localStorage.removeItem('qs_token');
        localStorage.removeItem('qs_user');
        window.location.href = '/login.html';
    }
};

// =============================================
// Services API
// =============================================
const ServicesAPI = {
    // Get all services
    getAll: async () => {
        return await apiRequest('/services');
    },

    // Get single service with locations
    getById: async (serviceId) => {
        return await apiRequest(`/services/${serviceId}`);
    },

    // Create service (admin only)
    create: async (serviceData) => {
        return await apiRequest('/services', {
            method: 'POST',
            body: JSON.stringify(serviceData)
        });
    },

    // Update service (admin only)
    update: async (serviceId, serviceData) => {
        return await apiRequest(`/services/${serviceId}`, {
            method: 'PUT',
            body: JSON.stringify(serviceData)
        });
    },

    // Delete service (admin only)
    delete: async (serviceId) => {
        return await apiRequest(`/services/${serviceId}`, {
            method: 'DELETE'
        });
    },

    // Get locations for a service
    getLocations: async (serviceId) => {
        return await apiRequest(`/services/${serviceId}/locations`);
    },

    // Create location (admin only)
    createLocation: async (serviceId, locationData) => {
        return await apiRequest(`/services/${serviceId}/locations`, {
            method: 'POST',
            body: JSON.stringify(locationData)
        });
    },

    // Update location (admin only)
    updateLocation: async (locationId, locationData) => {
        return await apiRequest(`/services/locations/${locationId}`, {
            method: 'PUT',
            body: JSON.stringify(locationData)
        });
    },

    // Delete location (admin only)
    deleteLocation: async (locationId) => {
        return await apiRequest(`/services/locations/${locationId}`, {
            method: 'DELETE'
        });
    }
};

// =============================================
// Queue API
// =============================================
const QueueAPI = {
    // Join queue
    join: async (serviceId, locationId, appointmentId = null, isEmergency = false) => {
        return await apiRequest('/queues/join', {
            method: 'POST',
            body: JSON.stringify({
                service_id: serviceId,
                location_id: locationId,
                appointment_id: appointmentId,
                is_emergency: isEmergency
            })
        });
    },

    // Add elder to queue (staff)
    addElder: async (elderData) => {
        return await apiRequest('/queues/add-elder', {
            method: 'POST',
            body: JSON.stringify(elderData)
        });
    },

    // Get queue status
    getStatus: async (serviceId, locationId, sector = null) => {
        const sectorParam = sector ? `?sector=${sector}` : '';
        return await apiRequest(`/queues/status/${serviceId}/${locationId}${sectorParam}`);
    },

    // Get my queue position
    getMyPosition: async () => {
        return await apiRequest('/queues/my-position');
    },

    // Call next token (staff)
    callNext: async (serviceId, locationId, counterNumber, sector = null) => {
        return await apiRequest('/queues/call-next', {
            method: 'POST',
            body: JSON.stringify({
                service_id: serviceId,
                location_id: locationId,
                counter_number: counterNumber,
                sector: sector
            })
        });
    },

    // Call specific token (staff override)
    callSpecific: async (queueType, queueId, counterNumber) => {
        return await apiRequest('/queues/call-specific', {
            method: 'POST',
            body: JSON.stringify({
                queue_type: queueType,
                queue_id: queueId,
                counter_number: counterNumber
            })
        });
    },

    // Mark as served (staff)
    markServed: async (queueType, queueId) => {
        return await apiRequest(`/queues/serve/${queueType}/${queueId}`, {
            method: 'POST'
        });
    },

    // Mark as no-show (staff)
    markNoShow: async (queueType, queueId) => {
        return await apiRequest(`/queues/no-show/${queueType}/${queueId}`, {
            method: 'POST'
        });
    },

    // Add emergency case
    addEmergency: async (emergencyData) => {
        return await apiRequest('/queues/emergency', {
            method: 'POST',
            body: JSON.stringify(emergencyData)
        });
    },

    // Generate dummy data
    generateDummy: async (dummyData) => {
        return await apiRequest('/queues/generate-dummy', {
            method: 'POST',
            body: JSON.stringify(dummyData)
        });
    },

    // Cancel call / Clear serving
    cancelCall: async (queueType, queueId) => {
        return await apiRequest(`/queues/cancel-call/${queueType}/${queueId}`, {
            method: 'POST'
        });
    },

    // Cancel queue entry
    cancel: async (queueType, queueId) => {
        return await apiRequest(`/queues/cancel/${queueType}/${queueId}`, {
            method: 'DELETE'
        });
    }
};

// =============================================
// Appointments API
// =============================================
const AppointmentsAPI = {
    // Get available slots
    getSlots: async (serviceId, locationId, date) => {
        const dateParam = date ? `?date=${date}` : '';
        return await apiRequest(`/appointments/slots/${serviceId}/${locationId}${dateParam}`);
    },

    // Book appointment
    book: async (appointmentData) => {
        return await apiRequest('/appointments', {
            method: 'POST',
            body: JSON.stringify(appointmentData)
        });
    },

    // Get my appointments
    getMy: async (filters = {}) => {
        const params = new URLSearchParams(filters).toString();
        return await apiRequest(`/appointments/my${params ? '?' + params : ''}`);
    },

    // Get single appointment
    getById: async (appId) => {
        return await apiRequest(`/appointments/${appId}`);
    },

    // Update appointment
    update: async (appId, appointmentData) => {
        return await apiRequest(`/appointments/${appId}`, {
            method: 'PUT',
            body: JSON.stringify(appointmentData)
        });
    },

    // Cancel appointment
    cancel: async (appId) => {
        return await apiRequest(`/appointments/${appId}`, {
            method: 'DELETE'
        });
    },

    // Check in for appointment
    checkIn: async (appId) => {
        return await apiRequest(`/appointments/${appId}/check-in`, {
            method: 'POST'
        });
    },

    // Get all appointments (staff/admin)
    getAll: async (filters = {}) => {
        const params = new URLSearchParams(filters).toString();
        return await apiRequest(`/appointments/all${params ? '?' + params : ''}`);
    }
};

// =============================================
// Staff API
// =============================================
const StaffAPI = {
    // Get all staff (admin)
    getAll: async () => {
        return await apiRequest('/staff');
    },

    // Get staff by ID
    getById: async (staffId) => {
        return await apiRequest(`/staff/${staffId}`);
    },

    // Create staff (admin)
    create: async (staffData) => {
        return await apiRequest('/staff', {
            method: 'POST',
            body: JSON.stringify(staffData)
        });
    },

    // Update staff (admin)
    update: async (staffId, staffData) => {
        return await apiRequest(`/staff/${staffId}`, {
            method: 'PUT',
            body: JSON.stringify(staffData)
        });
    },

    // Delete staff (admin)
    delete: async (staffId) => {
        return await apiRequest(`/staff/${staffId}`, {
            method: 'DELETE'
        });
    },

    // Update my availability
    updateAvailability: async (availabilityData) => {
        return await apiRequest('/staff/availability', {
            method: 'PUT',
            body: JSON.stringify(availabilityData)
        });
    }
};

// =============================================
// Users API
// =============================================
const UsersAPI = {
    // Get all users (admin)
    getAll: async (filters = {}) => {
        const params = new URLSearchParams(filters).toString();
        return await apiRequest(`/users${params ? '?' + params : ''}`);
    },

    // Get user by ID
    getById: async (userId) => {
        return await apiRequest(`/users/${userId}`);
    },

    // Update user (admin)
    update: async (userId, userData) => {
        return await apiRequest(`/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(userData)
        });
    },

    // Delete user (admin)
    delete: async (userId) => {
        return await apiRequest(`/users/${userId}`, {
            method: 'DELETE'
        });
    }
};

// =============================================
// Analytics API
// =============================================
const AnalyticsAPI = {
    // Get dashboard stats
    getDashboard: async (filters = {}) => {
        const params = new URLSearchParams(filters).toString();
        return await apiRequest(`/analytics/dashboard${params ? '?' + params : ''}`);
    },

    // Get historical data
    getHistory: async (filters = {}) => {
        const params = new URLSearchParams(filters).toString();
        return await apiRequest(`/analytics/history${params ? '?' + params : ''}`);
    },

    // Get service-wise analytics
    getByService: async (filters = {}) => {
        const params = new URLSearchParams(filters).toString();
        return await apiRequest(`/analytics/by-service${params ? '?' + params : ''}`);
    },

    // Get hourly distribution
    getHourly: async (filters = {}) => {
        const params = new URLSearchParams(filters).toString();
        return await apiRequest(`/analytics/hourly${params ? '?' + params : ''}`);
    },

    // Get manager summary for SLA/Efficiency
    getManagerSummary: async (filters = {}) => {
        const params = new URLSearchParams(filters).toString();
        return await apiRequest(`/analytics/manager-summary${params ? '?' + params : ''}`);
    },

    // Get admin dashboard stats
    getAdminDashboard: async (filters = {}) => {
        const params = new URLSearchParams(filters).toString();
        return await apiRequest(`/analytics/admin-dashboard${params ? '?' + params : ''}`);
    },

    // Get recent activities log
    getActivities: async (filters = {}) => {
        const params = new URLSearchParams(filters).toString();
        return await apiRequest(`/analytics/activities${params ? '?' + params : ''}`);
    },

    // Get real-time data for charts
    getRealtime: async (service_id, location_id) => {
        return await apiRequest(`/analytics/realtime?service_id=${service_id}&location_id=${location_id}`);
    },

    // Get public stats for landing page
    getPublicStats: async () => {
        return await apiRequest('/analytics/public-stats');
    }
};

// =============================================
// Settings API
// =============================================
const SettingsAPI = {
    // Get all settings
    get: async () => {
        return await apiRequest('/settings');
    },

    // Update settings (bulk)
    update: async (settingsData) => {
        return await apiRequest('/settings', {
            method: 'POST',
            body: JSON.stringify(settingsData)
        });
    },

    // Update single setting
    updateSingle: async (key, value) => {
        return await apiRequest(`/settings/${key}`, {
            method: 'PUT',
            body: JSON.stringify({ value })
        });
    }
};

// Export for use in other modules
window.API = {
    Auth: AuthAPI,
    Services: ServicesAPI,
    Queue: QueueAPI,
    Appointments: AppointmentsAPI,
    Staff: StaffAPI,
    Users: UsersAPI,
    Analytics: AnalyticsAPI,
    Settings: SettingsAPI
};
