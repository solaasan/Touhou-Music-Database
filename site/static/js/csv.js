/**
 * CSV export module
 */

/**
 * Export results to CSV
 * @param {Array} results - Array of result rows
 * @param {string} query - Search query
 * @param {string} searchType - 'song' or 'id'
 */
export function exportToCSV(results, query, searchType) {
    const headers = ['Track Name', 'Track Artist', 'Album Artist', 'Album Name', 'URL', 'Album Genre'];
    
    // Create CSV content
    let csvContent = headers.join(',') + '\n';
    
    results.forEach(row => {
        const escapedRow = row.map(cell => {
            if (cell === null || cell === undefined) {
                return '';
            }
            // Escape quotes and wrap in quotes if contains comma or quote
            const str = String(cell);
            if (str.includes(',') || str.includes('"') || str.includes('\n')) {
                return '"' + str.replace(/"/g, '""') + '"';
            }
            return str;
        });
        csvContent += escapedRow.join(',') + '\n';
    });
    
    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    const filename = searchType === 'song' 
        ? `${query}_results.csv`
        : 'results.csv';
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up
    URL.revokeObjectURL(url);
}

