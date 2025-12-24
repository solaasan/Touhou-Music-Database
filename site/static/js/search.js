/**
 * Search module - handles search functionality
 */

import { searchBySongName, searchBySourceTrackId } from './db.js';
import { navigateToResults, showError, hideError } from './ui.js';

/**
 * Handle song name search
 * @param {string} songName - Song name to search for
 */
export async function handleSongSearch(songName) {
    try {
        hideError();
        
        if (!songName || songName.trim() === '') {
            return;
        }
        
        const results = await searchBySongName(songName.trim());
        navigateToResults(results, songName.trim(), 'song');
    } catch (error) {
        console.error('Search error:', error);
        showError(error.message || 'An error occurred during search');
    }
}

/**
 * Handle source track ID search
 * @param {string} query - Source track ID (1-4 digits)
 */
export async function handleIdSearch(query) {
    try {
        hideError();
        
        if (!query || query.trim() === '') {
            return;
        }
        
        const sourceTrackId = parseInt(query.trim(), 10);
        
        if (isNaN(sourceTrackId) || sourceTrackId > 9999) {
            showError("Invalid input. Please enter upto 4 numbers.");
            return;
        }
        
        const results = await searchBySourceTrackId(sourceTrackId);
        navigateToResults(results, query.trim(), 'id');
    } catch (error) {
        console.error('Search error:', error);
        showError(error.message || 'An error occurred during search');
    }
}

