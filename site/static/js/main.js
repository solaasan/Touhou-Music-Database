/**
 * Main entry point - initializes the application
 */

import { initDatabase, getSourceTracks } from './db.js';
import { showLoading, hideLoading, showError, hideError, renderSourceTracks } from './ui.js';
import { handleSongSearch, handleIdSearch } from './search.js';

/**
 * Initialize the application
 */
async function init() {
    // Check if source tracks table is already rendered (static HTML)
    const tbody = document.getElementById('source-tracks-body');
    const hasStaticContent = tbody && tbody.children.length > 0;
    
    try {
        if (!hasStaticContent) {
            // Only show loading if we need to load source tracks
            showLoading();
        }
        
        hideError();
        
        // Only load source tracks if they're not already rendered
        if (!hasStaticContent) {
            try {
                // Initialize database
                await initDatabase();
                
                // Load source tracks
                const sourceTracks = await getSourceTracks();
                renderSourceTracks(sourceTracks);
                
                hideLoading();
            } catch (error) {
                console.error('Error loading source tracks:', error);
                showError('Failed to load source tracks. Please refresh the page.');
                hideLoading();
            }
        } else {
            // Table is already rendered, just ensure database is ready for searches
            // Don't block on this - let it load in background
            initDatabase().catch(() => {
                // Silently fail - user can still see the table and search will work once DB loads
            });
        }
    } catch (error) {
        console.error('Initialization error:', error);
        if (!hasStaticContent) {
            showError('Failed to load database. Please refresh the page.');
            hideLoading();
        }
    }
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Song search form
    const songForm = document.getElementById('song-search-form');
    if (songForm) {
        songForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const input = document.getElementById('song-input');
            if (input && input.value.trim()) {
                await handleSongSearch(input.value.trim());
            }
        });
    }
    
    // ID search form
    const idForm = document.getElementById('id-search-form');
    if (idForm) {
        idForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const input = document.getElementById('query-input');
            if (input && input.value.trim()) {
                await handleIdSearch(input.value.trim());
            }
        });
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        init();
        setupEventListeners();
    });
} else {
    init();
    setupEventListeners();
}

