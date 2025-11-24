const API_BASE = window.AppConfig ? window.AppConfig.API_BASE : 'http://localhost:8000';

// DOM Elements
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
const newScanBtn = document.getElementById('newScanBtn');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
const scanHistory = document.getElementById('scanHistory');
const urlInput = document.getElementById('urlInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const inputSection = document.getElementById('inputSection');
const statusSection = document.getElementById('statusSection');
const statusText = document.getElementById('statusText');
const resultsSection = document.getElementById('resultsSection');
const emptyState = document.getElementById('emptyState');

let currentScanId = null;
let scans = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadScanHistory();
    setupEventListeners();
});

function setupEventListeners() {
    const sidebarToggleMobile = document.getElementById('sidebarToggleMobile');

    sidebarToggle?.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        // Save state to localStorage
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    });

    // Mobile toggle button
    if (sidebarToggleMobile) {
        sidebarToggleMobile.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });
    }

    // Restore sidebar state from localStorage
    const savedState = localStorage.getItem('sidebarCollapsed');
    const isMobile = window.innerWidth <= 768;

    // On mobile, always start collapsed; on desktop, restore saved state
    if (isMobile) {
        sidebar.classList.add('collapsed');
    } else if (savedState === 'true') {
        sidebar.classList.add('collapsed');
    }

    newScanBtn.addEventListener('click', showNewScanInput);
    clearHistoryBtn.addEventListener('click', clearHistory);
    analyzeBtn.addEventListener('click', createNewScan);

    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') createNewScan();
    });
}

// Load scan history from IndexedDB
async function loadScanHistory() {
    try {
        scans = await getScans();
        renderScanHistory();
    } catch (error) {
        console.error('Error loading scan history:', error);
        scanHistory.innerHTML = '<div class="loading-history">Failed to load history</div>';
    }
}

// Delete a single scan
async function deleteScan(scanId) {
    if (!confirm('Are you sure you want to delete this scan?')) {
        return;
    }

    try {
        // Delete from local DB
        await deleteScanFromDB(scanId);

        // Remove from local scans array
        scans = scans.filter(s => s.id !== scanId);

        // If deleted scan was active, show new scan input
        if (currentScanId === scanId) {
            currentScanId = null;
            showNewScanInput();
        }

        // Re-render history
        renderScanHistory();
    } catch (error) {
        console.error('Error deleting scan:', error);
        alert('Failed to delete scan. Please try again.');
    }
}

// Clear scan history
async function clearHistory() {
    if (!confirm('Are you sure you want to clear all scan history? This cannot be undone.')) {
        return;
    }

    try {
        await clearScansFromDB();
        scans = [];
        currentScanId = null;
        renderScanHistory();
        showNewScanInput();
    } catch (error) {
        console.error('Error clearing history:', error);
        alert('Failed to clear history. Please try again.');
    }
}

// Poll scan status
async function pollScanStatus(scanId) {
    let attempts = 0;
    const maxAttempts = 120;

    const poll = async () => {
        if (attempts >= maxAttempts) {
            statusText.textContent = 'Scan timed out';
            setTimeout(() => loadScan(scanId), 2000);
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/scan/${scanId}`);
            if (!response.ok) throw new Error('Failed to fetch scan status');

            const scanData = await response.json();
            statusText.textContent = `Status: ${scanData.status}...`;

            if (scanData.status === 'completed') {
                // Save completed scan to IndexedDB
                await saveScan(scanData);

                // Refresh sidebar to show updated status
                await loadScanHistory();

                // Display results
                displayResults(scanData);
            } else if (scanData.status === 'failed') {
                // Save failed scan to IndexedDB
                await saveScan(scanData);
                await loadScanHistory();

                statusText.textContent = `Scan failed: ${scanData.error_message || 'Unknown error'}`;
                setTimeout(() => loadScan(scanId), 3000);
            } else {
                attempts++;
                setTimeout(poll, 1000);
            }
        } catch (error) {
            console.error('Error polling scan:', error);
            statusText.textContent = `Error: ${error.message}`;
        }
    };

    poll();
}

// Load existing scan (from DB first, then API if needed)
async function loadScan(scanId) {
    currentScanId = scanId;

    // Update active state in sidebar
    document.querySelectorAll('.scan-item').forEach(item => {
        item.classList.toggle('active', item.dataset.scanId === scanId);
    });

    // Show loading
    inputSection.classList.add('hidden');
    statusSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    emptyState.classList.add('hidden');
    statusText.textContent = 'Loading scan...';

    try {
        // Try loading from IndexedDB first
        let scanData = await getScan(scanId);

        if (!scanData) {
            // Fallback to API if not in DB (e.g. shared link or fresh load)
            const response = await fetch(`${API_BASE}/scan/${scanId}`);
            if (!response.ok) throw new Error('Failed to load scan');
            scanData = await response.json();

            // If completed, save to DB for next time
            if (scanData.status === 'completed') {
                await saveScan(scanData);
            }
        }

        if (scanData.status === 'completed') {
            displayResults(scanData);
        } else if (scanData.status === 'queued') {
            statusText.textContent = 'Scan is queued...';
            pollScanStatus(scanId);
        } else if (scanData.status === 'failed') {
            statusText.textContent = `Scan failed: ${scanData.error_message || 'Unknown error'}`;
        }
    } catch (error) {
        console.error('Error loading scan:', error);
        statusText.textContent = `Error: ${error.message}`;
    }
}

// Chat Logic
async function sendChatMessage() {
    const userMsg = chatInput.value.trim();
    if (!userMsg) return;

    displayChatMessage(userMsg, 'user');
    chatHistory.push({ user: userMsg });
    chatInput.value = '';
    showTypingIndicator();

    try {
        const apiKey = await getStoredApiKey();

        // Get current scan context from DB
        const scanData = await getScan(currentScanId);

        // Construct context object
        let scanContext = {};
        if (scanData) {
            scanContext = {
                url: scanData.url,
                module_results: scanData.module_results
            };
        }

        const response = await fetch(`${API_BASE}/chat/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: userMsg,
                history: chatHistory,
                api_key: apiKey,
                scan_context: scanContext
            })
        });

        hideTypingIndicator();
        if (!response.ok) throw new Error('Chat request failed');

        const data = await response.json();
        const aiMsg = data.response;
        displayChatMessage(aiMsg, 'assistant');
        chatHistory.push({ assistant: aiMsg });
    } catch (err) {
        hideTypingIndicator();
        console.error('Chat error:', err);
        displayChatMessage('Error: unable to get response.', 'assistant');
    }
}


// Render scan history in sidebar
function renderScanHistory() {
    if (scans.length === 0) {
        scanHistory.innerHTML = '<div class="loading-history">No scans yet</div>';
        return;
    }

    scanHistory.innerHTML = scans.map(scan => `
        <div class="scan-item ${scan.id === currentScanId ? 'active' : ''}" data-scan-id="${scan.id}">
            <div class="scan-item-content">
                <div class="scan-item-url" title="${scan.url}">${formatUrl(scan.url)}</div>
                <div class="scan-item-meta">
                    <span>${formatDate(scan.created_at)}</span>
                    <span class="scan-status ${scan.status}">${scan.status}</span>
                </div>
            </div>
            <button class="scan-delete-btn" data-scan-id="${scan.id}" title="Delete scan">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        </div>
    `).join('');

    // Add click listeners for scan items
    document.querySelectorAll('.scan-item').forEach(item => {
        const content = item.querySelector('.scan-item-content');
        content.addEventListener('click', () => {
            const scanId = item.dataset.scanId;
            loadScan(scanId);
        });
    });

    // Add click listeners for delete buttons
    document.querySelectorAll('.scan-delete-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation(); // Prevent triggering scan load
            const scanId = btn.dataset.scanId;
            await deleteScan(scanId);
        });
    });
}

// ---------- IndexedDB Storage ----------

const DB_NAME = 'siteSenseDB';
const DB_VERSION = 2; // Increment for new stores

function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onupgradeneeded = (e) => {
            const db = e.target.result;
            if (!db.objectStoreNames.contains('keys')) {
                db.createObjectStore('keys');
            }
            if (!db.objectStoreNames.contains('scans')) {
                const scanStore = db.createObjectStore('scans', { keyPath: 'id' });
                scanStore.createIndex('created_at', 'created_at', { unique: false });
            }
        };

        request.onsuccess = (e) => resolve(e.target.result);
        request.onerror = (e) => reject(e.target.error);
    });
}

// API Key Helpers
async function getStoredApiKey() {
    const db = await openDB();
    return new Promise((resolve) => {
        const tx = db.transaction('keys', 'readonly');
        const store = tx.objectStore('keys');
        const getReq = store.get('gemini');
        getReq.onsuccess = () => resolve(getReq.result || null);
        getReq.onerror = () => resolve(null);
    });
}

async function storeApiKey(key) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction('keys', 'readwrite');
        const store = tx.objectStore('keys');
        const putReq = store.put(key, 'gemini');
        putReq.onsuccess = () => resolve();
        putReq.onerror = (e) => reject(e.target.error);
    });
}

// Scan Storage Helpers
async function saveScan(scanData) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction('scans', 'readwrite');
        const store = tx.objectStore('scans');
        const putReq = store.put(scanData);
        putReq.onsuccess = () => resolve();
        putReq.onerror = (e) => reject(e.target.error);
    });
}

async function getScans() {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction('scans', 'readonly');
        const store = tx.objectStore('scans');
        const index = store.index('created_at');
        const request = index.openCursor(null, 'prev'); // Newest first
        const results = [];

        request.onsuccess = (e) => {
            const cursor = e.target.result;
            if (cursor) {
                results.push(cursor.value);
                cursor.continue();
            } else {
                resolve(results);
            }
        };
        request.onerror = (e) => reject(e.target.error);
    });
}

async function getScan(id) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction('scans', 'readonly');
        const store = tx.objectStore('scans');
        const request = store.get(id);
        request.onsuccess = () => resolve(request.result);
        request.onerror = (e) => reject(e.target.error);
    });
}

async function deleteScanFromDB(id) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction('scans', 'readwrite');
        const store = tx.objectStore('scans');
        const request = store.delete(id);
        request.onsuccess = () => resolve();
        request.onerror = (e) => reject(e.target.error);
    });
}

async function clearScansFromDB() {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction('scans', 'readwrite');
        const store = tx.objectStore('scans');
        const request = store.clear();
        request.onsuccess = () => resolve();
        request.onerror = (e) => reject(e.target.error);
    });
}

// Delete a single scan
async function deleteScan(scanId) {
    if (!confirm('Are you sure you want to delete this scan?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/scan/${scanId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to delete scan');

        // Remove from local scans array
        scans = scans.filter(s => s.id !== scanId);

        // If deleted scan was active, show new scan input
        if (currentScanId === scanId) {
            currentScanId = null;
            showNewScanInput();
        }

        // Re-render history
        renderScanHistory();
    } catch (error) {
        console.error('Error deleting scan:', error);
        alert('Failed to delete scan. Please try again.');
    }
}

// Format URL for display
function formatUrl(url) {
    try {
        const urlObj = new URL(url);
        return urlObj.hostname;
    } catch {
        return url;
    }
}

// Format date for display
function formatDate(dateString) {
    // Treat the timestamp as UTC by appending 'Z' if not present
    const utcDateString = dateString.endsWith('Z') ? dateString : dateString + 'Z';
    const date = new Date(utcDateString);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
}

// Clear scan history
async function clearHistory() {
    if (!confirm('Are you sure you want to clear all scan history? This cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/scan/clear`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to clear history');

        scans = [];
        currentScanId = null;
        renderScanHistory();
        showNewScanInput();
    } catch (error) {
        console.error('Error clearing history:', error);
        alert('Failed to clear history. Please try again.');
    }
}

// Show new scan input
function showNewScanInput() {
    currentScanId = null;
    inputSection.classList.remove('hidden');
    statusSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    emptyState.classList.add('hidden');
    urlInput.value = '';
    urlInput.focus();

    // Remove active state from all scan items
    document.querySelectorAll('.scan-item').forEach(item => {
        item.classList.remove('active');
    });
}

// Create new scan
async function createNewScan() {
    const url = urlInput.value.trim();

    if (!url) {
        alert('Please enter a URL');
        return;
    }

    // Validate URL
    try {
        new URL(url);
    } catch (e) {
        alert('Please enter a valid URL');
        return;
    }

    // Show status
    inputSection.classList.add('hidden');
    statusSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    emptyState.classList.add('hidden');
    statusText.textContent = 'Creating scan...';

    try {
        // Create scan
        const response = await fetch(`${API_BASE}/scan/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        if (!response.ok) throw new Error('Failed to create scan');

        const scanData = await response.json();
        currentScanId = scanData.id;

        // Save initial "queued" scan to IndexedDB so it appears in history
        await saveScan(scanData);

        // Reload history to show new scan
        await loadScanHistory();

        // Poll for results
        pollScanStatus(currentScanId);

    } catch (error) {
        console.error('Error creating scan:', error);
        statusText.textContent = `Error: ${error.message}`;
        setTimeout(() => showNewScanInput(), 3000);
    }
}

// Poll scan status
async function pollScanStatus(scanId) {
    let attempts = 0;
    const maxAttempts = 120;

    const poll = async () => {
        if (attempts >= maxAttempts) {
            statusText.textContent = 'Scan timed out';
            setTimeout(() => loadScan(scanId), 2000);
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/scan/${scanId}`);
            if (!response.ok) throw new Error('Failed to fetch scan status');

            const scanData = await response.json();
            statusText.textContent = `Status: ${scanData.status}...`;

            if (scanData.status === 'completed') {
                await loadScanHistory(); // Refresh history
                displayResults(scanData);
            } else if (scanData.status === 'failed') {
                statusText.textContent = `Scan failed: ${scanData.error_message || 'Unknown error'}`;
                setTimeout(() => loadScan(scanId), 3000);
            } else {
                attempts++;
                setTimeout(poll, 1000);
            }
        } catch (error) {
            console.error('Error polling scan:', error);
            statusText.textContent = `Error: ${error.message}`;
        }
    };

    poll();
}

// Load existing scan
async function loadScan(scanId) {
    currentScanId = scanId;

    // Update active state in sidebar
    document.querySelectorAll('.scan-item').forEach(item => {
        item.classList.toggle('active', item.dataset.scanId === scanId);
    });

    // Show loading
    inputSection.classList.add('hidden');
    statusSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    emptyState.classList.add('hidden');
    statusText.textContent = 'Loading scan...';

    try {
        const response = await fetch(`${API_BASE}/scan/${scanId}`);
        if (!response.ok) throw new Error('Failed to load scan');

        const scanData = await response.json();

        if (scanData.status === 'completed') {
            displayResults(scanData);
        } else if (scanData.status === 'queued') {
            statusText.textContent = 'Scan is queued...';
            pollScanStatus(scanId);
        } else if (scanData.status === 'failed') {
            statusText.textContent = `Scan failed: ${scanData.error_message || 'Unknown error'}`;
        }
    } catch (error) {
        console.error('Error loading scan:', error);
        statusText.textContent = `Error: ${error.message}`;
    }
}

// Display results
function displayResults(scanData) {
    statusSection.classList.add('hidden');
    resultsSection.classList.remove('hidden');
    emptyState.classList.add('hidden');

    // Display scanned URL
    const scannedUrlElement = document.getElementById('scannedUrl');
    scannedUrlElement.textContent = scanData.url;
    scannedUrlElement.href = scanData.url;

    // Find aggregated report
    const aggregatedReport = scanData.module_results.find(r => r.module_name === 'aggregated_report');

    if (!aggregatedReport) {
        statusSection.classList.remove('hidden');
        statusText.textContent = 'No results available';
        return;
    }

    const report = aggregatedReport.result_json;

    // Overall score with animation
    const overallScore = report.overall_score || 0;
    document.getElementById('overallScore').textContent = overallScore;

    const scoreRing = document.getElementById('scoreRing');
    const circumference = 2 * Math.PI * 54;
    const offset = circumference - (overallScore / 100) * circumference;
    scoreRing.style.strokeDashoffset = offset;

    // Set ring color based on score
    if (overallScore >= 80) scoreRing.style.stroke = '#10b981';
    else if (overallScore >= 60) scoreRing.style.stroke = '#3b82f6';
    else if (overallScore >= 40) scoreRing.style.stroke = '#f59e0b';
    else scoreRing.style.stroke = '#ef4444';

    // Module scores
    document.getElementById('securityScore').textContent = Math.round(report.module_scores?.security || 0);
    document.getElementById('seoScore').textContent = Math.round(report.module_scores?.seo || 0);
    document.getElementById('performanceScore').textContent = Math.round(report.module_scores?.performance || 0);
    document.getElementById('accessibilityScore').textContent = Math.round(report.module_scores?.accessibility || 0);

    // Recommendations
    const recommendationsList = document.getElementById('recommendationsList');
    recommendationsList.innerHTML = '';

    if (report.recommendations && report.recommendations.length > 0) {
        report.recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.innerHTML = `<strong>${rec.category}:</strong> ${rec.text}`;
            recommendationsList.appendChild(li);
        });
    } else {
        recommendationsList.innerHTML = '<li>No recommendations available</li>';
    }

    // Heatmaps - now served from database
    document.getElementById('attentionHeatmap').src = `${API_BASE}/files/${scanData.id}/attention_heatmap`;
    document.getElementById('clickHeatmap').src = `${API_BASE}/files/${scanData.id}/click_heatmap`;
}
