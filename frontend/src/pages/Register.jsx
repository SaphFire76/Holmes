import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { registerUser } from '../services/authService';

function Register() {
    const [email, setEmail] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    const navigate = useNavigate();

    const handleRegister = async () => {
        setError(null);
        setIsLoading(true); 

        try {
            // 1. Call the service function
            const data = await registerUser(email, username, password);

            // 2. Success! Save the token
            localStorage.setItem('access_token', data.access_token);
            
            // 3. Redirect
            navigate('/');

        } catch (err) {
            // 4. If the service threw an error, display it in the UI
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="register">
            <h2>Register</h2>
            
            {/* Display error messages if they exist */}
            {error && <div style={{ color: 'red', marginBottom: '1rem' }}>{error}</div>}

            <form className="register-form" onSubmit={(e) => {
                e.preventDefault();
                handleRegister();
            }}>
                <div>
                    <label>Email:</label>
                    <input 
                        type="email" 
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />
                </div>
                <div>
                    <label>Username:</label>
                    <input 
                        type="text" 
                        required
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                    />
                </div>
                <div>
                    <label>Password:</label>
                    <input 
                        type="password" 
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </div>
                
                {/* Disable the button while the request is running so they don't double-click */}
                <button type="submit" disabled={isLoading}>
                    {isLoading ? 'Registering...' : 'Register'}
                </button>
            </form>
        </div>
    );
}

export default Register;