
// Registration API call
export const registerUser = async (email, username, password) => {
    const response = await fetch('http://localhost:8000/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, username, password }),
    });

    const data = await response.json();

    // If FastAPI throws an error (like email already exists), throw it so React can catch it
    if (!response.ok) {
        throw new Error(data.detail || 'Registration failed');
    }

    // Return the successful data (which includes the access_token)
    return data;
};

// Login API call
export const loginUser = async (email, password) => {
    const response = await fetch('http://localhost:8000/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    // Throw the specific backend error (e.g., "Invalid email or password") back to React
    if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
    }

    // Return the successful data payload (access_token)
    return data;
};