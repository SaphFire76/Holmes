const BASE_URL = `http://${window.location.hostname}:8000`;

// ==========================================
// THE FETCH WRAPPER (Centralized Logic)
// ==========================================
const apiFetch = async (endpoint, options = {}) => {
    const token = localStorage.getItem('access_token');

    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers 
    };

    const response = await fetch(`${BASE_URL}${endpoint}`, {
        ...options,
        headers
    });

    // Centralized 401 Handling
    if (response.status === 401) {
        console.warn("Token expired! Auto-logging out...");
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        throw new Error("Session expired");
    }

    // Parse the JSON once
    const data = await response.json().catch(() => ({}));

    // Centralized Error Handling
    if (!response.ok) {
        throw new Error(data.detail || `API request failed with status ${response.status}`);
    }

    return data;
};

// ==========================================
// API FUNCTIONS
// ==========================================

// Fetch the logged-in user's profile info
export const fetchUserDetails = async () => {
    const data = await apiFetch('/users/me');
    return data.user; 
};

// Fetch the history of scans for the logged-in user
export const fetchHistory = async () => {
    const data = await apiFetch('/history');
    return data.history; 
};

// Send a request for details of scan
export const fetchFullScanVerdict = async (scanId) => {
    const data = await apiFetch(`/scans/${scanId}`);
    return data.scan; 
};

// Send a new email to be scanned
export const scanNewEmail = async (emailText) => {
    const data = await apiFetch('/analyse', {
        method: 'POST',
        body: JSON.stringify({ email: emailText }) 
    });
    return data.scan; 
};

// Search for scans matching a query
export const searchScanHistory = async (searchTerm) => {
    const safeSearchTerm = encodeURIComponent(searchTerm);
    const data = await apiFetch(`/search?q=${safeSearchTerm}`);
    return data.results; 
};

// Rename a scan
export const renameScanApi = async (scanId, newTitle) => {
    return await apiFetch(`/scans/${scanId}/rename`, {
        method: 'PATCH',
        body: JSON.stringify({ new_title: newTitle })
    });
};

// Delete a scan
export const deleteScanApi = async (scanId) => {
    return await apiFetch(`/scans/${scanId}`, {
        method: 'DELETE'
    });
};