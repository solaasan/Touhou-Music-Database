/**
 * UI module - handles rendering and display
 */

/**
 * Show loading indicator
 */
export function showLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'block';
    }
}

/**
 * Hide loading indicator
 */
export function hideLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'none';
    }
}

/**
 * Show error message
 * @param {string} message - Error message to display
 */
export function showError(message) {
    const error = document.getElementById('error');
    if (error) {
        error.textContent = message;
        error.style.display = 'block';
    }
}

/**
 * Hide error message
 */
export function hideError() {
    const error = document.getElementById('error');
    if (error) {
        error.style.display = 'none';
    }
}

/**
 * Render source tracks table
 * @param {Array} sourceTracks - Array of [id, name, count] tuples
 */
export function renderSourceTracks(sourceTracks) {
    const table = document.getElementById('source-tracks-table');
    const tbody = document.getElementById('source-tracks-body');
    
    if (!table || !tbody) {
        return;
    }
    
    // Clear existing rows
    tbody.innerHTML = '';
    
    // Add rows
    sourceTracks.forEach(([id, name, count]) => {
        const row = document.createElement('tr');
        
        const idCell = document.createElement('td');
        const idLink = document.createElement('a');
        idLink.href = '#';
        idLink.textContent = id;
        idLink.onclick = (e) => {
            e.preventDefault();
            const input = document.getElementById('query-input');
            if (input) {
                input.value = id;
            }
        };
        idCell.appendChild(idLink);
        
        const nameCell = document.createElement('td');
        nameCell.textContent = name;
        
        const countCell = document.createElement('td');
        countCell.textContent = count;
        
        row.appendChild(idCell);
        row.appendChild(nameCell);
        row.appendChild(countCell);
        
        tbody.appendChild(row);
    });
    
    table.style.display = 'table';
}


/**
 * Navigate to results page with data in sessionStorage and URL parameters
 * @param {Array} results - Array of result rows
 * @param {string} query - Search query
 * @param {string} searchType - 'song' or 'id'
 */
export function navigateToResults(results, query, searchType) {
    // Store results in sessionStorage for fast navigation
    sessionStorage.setItem('searchResults', JSON.stringify(results));
    sessionStorage.setItem('searchQuery', query);
    sessionStorage.setItem('searchType', searchType);
    
    // Build URL with query parameters for sharing
    const params = new URLSearchParams();
    params.set('type', searchType);
    params.set('q', encodeURIComponent(query));
    
    // Navigate to results page with URL parameters
    window.location.href = `results.html?${params.toString()}`;
}

