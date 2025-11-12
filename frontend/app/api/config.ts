/**
 * API Configuration
 * Automatically detects backend URL based on current hostname
 */

export function getBackendUrl(): string {
  // If we're in the browser
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    
    // If accessing via localhost, use localhost for backend
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:5001';
    }
    
    // If accessing via network IP, use the same IP for backend
    // This allows the frontend to work when accessed from other devices on the network
    return `http://${hostname}:5001`;
  }
  
  // Server-side (SSR) fallback - use localhost
  return 'http://localhost:5001';
}

export const API_BASE_URL = getBackendUrl();


