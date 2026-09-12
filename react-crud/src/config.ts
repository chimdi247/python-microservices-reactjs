// Baked in at build time by Create React App (REACT_APP_* prefix required).
// See docker-compose.yml's `client` service build.args, and .env.example.
export const ADMIN_API_URL = process.env.REACT_APP_ADMIN_API_URL || 'http://localhost:8000';
export const MAIN_API_URL = process.env.REACT_APP_MAIN_API_URL || 'http://localhost:8001';
