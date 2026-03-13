import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000', // Change this to your backend URL
});

export default api;