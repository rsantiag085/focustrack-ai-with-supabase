import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm'

const BACKEND_URL = 'http://localhost:8000';

let supabase;
let currentSession = null;

try {
    supabase = createClient(
        'https://unwddclrmluffxowkjrh.supabase.co',
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVud2RkY2xybWx1ZmZ4b3dranJoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ1NDM5MjYsImV4cCI6MjA5MDExOTkyNn0.L67OI6oQU-n-UAwUJGUNo98ulLzAcXt9kSC-ZebzXVE'
    );
    window.supabase = supabase;
} catch (initError) {
    console.error("CRITICAL: Failed to initialize Supabase client.", initError);
}

if (supabase) {
    supabase.auth.onAuthStateChange(async (event, session) => {
        currentSession = session;
        const authContainer = document.getElementById('auth-container');
        const mainDashboard = document.getElementById('main-dashboard');

        if (session) {
            if (authContainer) authContainer.style.display = 'none';
            if (mainDashboard) mainDashboard.style.display = 'block';
            if ((event === 'SIGNED_IN' || event === 'INITIAL_SESSION') && typeof window.refreshDashboard === 'function') {
                window.refreshDashboard();
            }
        } else {
            if (authContainer) authContainer.style.display = 'flex';
            if (mainDashboard) mainDashboard.style.display = 'none';
        }
    });
}

window.handleLogin = async (email, password) => {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
    return data;
};

window.handleSignUp = async (email, password) => {
    const { data, error } = await supabase.auth.signUp({ email, password });
    if (error) throw error;
    return data;
};

window.handleLogout = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
};

window.apiFetch = async (endpoint, options = {}) => {
    if (!currentSession) {
        throw new Error("No active Supabase session found. Please log in.");
    }

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
        'Authorization': `Bearer ${currentSession.access_token}`
    };

    const response = await fetch(`${BACKEND_URL}${endpoint}`, { ...options, headers });

    if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
};

window.loadAtividades = () => window.apiFetch('/api/atividade');

window.saveAtividade = (atividadeData) => window.apiFetch('/api/atividade', {
    method: 'POST',
    body: JSON.stringify(atividadeData)
});

window.deleteAtividade = (id) => window.apiFetch(`/api/atividade/${id}`, {
    method: 'DELETE'
});

window.analisarDia = (dataStr) => window.apiFetch(`/api/analisar?target_date=${dataStr}`, {
    method: 'POST'
});
