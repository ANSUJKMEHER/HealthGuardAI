/**
 * HealthGuard AI — Frontend Configuration
 * Reads API URL from environment variable for deployment flexibility.
 */
export const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
export const SSE_URL = `${API_URL}/api/v1/stream`;
