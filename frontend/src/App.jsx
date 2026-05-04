// import { useState, useRef, useEffect } from 'react'; // Added useRef and useEffect
// import api from './api';
import './App.css';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Register from './pages/Register';
import ProtectedRoute from './components/ProtectedRoute';
import { Routes, Route } from 'react-router-dom';

function App() {
  return (
    <main className='main-content'>
      <Routes>
        <Route 
            path="/" 
            element={
                <ProtectedRoute>
                    <Dashboard />
                </ProtectedRoute>
            } 
        />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Routes>
    </main>
  );
}

export default App;