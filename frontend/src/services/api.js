// src/services/api.js
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
});

// ── AUTH ──────────────────────────────────────────────────────────────────
export async function loginUser(email, password) {
  try {
    const response = await api.post('/auth/login', { email, password });
    return { success: true, data: response.data };
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Erreur de connexion';
    return { success: false, error: msg };
  }
}

// ── CHATBOT ───────────────────────────────────────────────────────────────
export async function sendQuestion(question, tenantDb, responseMode = 'data') {
  try {
    const response = await api.post('/chat/question', {
      question,
      tenant_db: tenantDb,
      response_mode: responseMode,
    });
    return { success: true, data: response.data };
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Erreur lors de la requête';
    return { success: false, error: msg };
  }
}

// ── EXPORT EXCEL ──────────────────────────────────────────────────────────
export async function exportExcel(rows, columns, question) {
  try {
    const XLSX = await import('xlsx');
    const { saveAs } = await import('file-saver');

    const ws = XLSX.utils.json_to_sheet(rows);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Données');

    const excelBuffer = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
    const blob = new Blob([excelBuffer], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    const filename = `ichat_export_${new Date().toISOString().slice(0, 10)}.xlsx`;
    saveAs(blob, filename);
    return true;
  } catch (err) {
    console.error('Export Excel error:', err);
    return false;
  }
}

export default api;
