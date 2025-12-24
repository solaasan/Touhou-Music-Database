/**
 * Database module - handles SQLite database loading and queries
 */

let db = null;
let initPromise = null;

/**
 * Initialize the database
 * @returns {Promise} Promise that resolves when database is loaded
 */
export async function initDatabase() {
    if (db) {
        return db;
    }
    
    if (initPromise) {
        return initPromise;
    }
    
    initPromise = (async () => {
        try {
            // Wait for sql.js to be available (loaded via script tag)
            // sql.js makes initSqlJs available globally when loaded
            const getInitSqlJs = () => {
                if (typeof initSqlJs !== 'undefined') {
                    return initSqlJs;
                }
                if (typeof window !== 'undefined' && window.initSqlJs) {
                    return window.initSqlJs;
                }
                return null;
            };
            
            let sqlInit = getInitSqlJs();
            if (!sqlInit) {
                // Wait for script to load
                await new Promise((resolve, reject) => {
                    let attempts = 0;
                    const maxAttempts = 100; // 10 seconds
                    const checkInterval = setInterval(() => {
                        sqlInit = getInitSqlJs();
                        if (sqlInit) {
                            clearInterval(checkInterval);
                            resolve();
                        } else if (attempts++ >= maxAttempts) {
                            clearInterval(checkInterval);
                            reject(new Error('sql.js failed to load after 10 seconds'));
                        }
                    }, 100);
                });
            }
            
            // Initialize sql.js
            const SQL = await sqlInit({
                locateFile: file => `static/${file}`
            });
            
            // Load the database file
            const response = await fetch('touhou-music.db');
            if (!response.ok) {
                throw new Error(`Failed to load database: ${response.statusText}`);
            }
            
            const buffer = await response.arrayBuffer();
            const uint8Array = new Uint8Array(buffer);
            
            // Open the database
            db = new SQL.Database(uint8Array);
            
            return db;
        } catch (error) {
            console.error('Database initialization error:', error);
            throw error;
        }
    })();
    
    return initPromise;
}

/**
 * Get source tracks with counts
 * @returns {Promise<Array>} Array of [id, name, count] tuples
 */
export async function getSourceTracks() {
    await initDatabase();
    
    const query = `
        SELECT 
            st.id,
            st.name,
            COUNT(tvs.track_id) as count
        FROM source_tracks st
        LEFT JOIN track_vs_source_index tvs ON st.id = tvs.source_track_id
        WHERE st.id != 35
        GROUP BY st.id, st.name
        ORDER BY count DESC
    `;
    
    const result = db.exec(query);
    if (result.length === 0) {
        return [];
    }
    
    const rows = result[0].values;
    return rows.map(row => [row[0], row[1], row[2]]);
}

/**
 * Search by source track ID
 * @param {number} sourceTrackId - Source track ID (1-4 digits)
 * @returns {Promise<Array>} Array of result rows
 */
export async function searchBySourceTrackId(sourceTrackId) {
    await initDatabase();
    
    if (sourceTrackId > 9999) {
        throw new Error("Invalid input. Please enter upto 4 numbers.");
    }
    
    const query = `
        SELECT 
            t.name AS track_name,
            sta.name AS track_artist,
            rci.name AS album_artist,
            ai.album_name,
            ai.url_links,
            ai.genre
        FROM tracks t
        JOIN track_vs_source_index tvs ON t.id = tvs.track_id
        JOIN source_tracks st ON tvs.source_track_id = st.id
        JOIN songtrack_artist_index sta ON t.songtrack_artist_id = sta.id
        JOIN release_circle_index rci ON t.release_circle_id = rci.id
        JOIN albums_index ai ON t.album_id = ai.id
        WHERE st.id = ?
        ORDER BY rci.name
    `;
    
    const stmt = db.prepare(query);
    stmt.bind([sourceTrackId]);
    
    const results = [];
    while (stmt.step()) {
        // Use get() to get values by index (more reliable than getAsObject)
        const row = stmt.get();
        results.push([
            row[0] || '',  // track_name
            row[1] || '',  // track_artist
            row[2] || '',  // album_artist
            row[3] || '',  // album_name
            row[4] || null, // url_links
            row[5] || null  // genre
        ]);
    }
    
    stmt.free();
    return results;
}

/**
 * Search by song name (searches across tracks, albums, artists, circles)
 * @param {string} songName - Song name to search for
 * @returns {Promise<Array>} Array of result rows
 */
export async function searchBySongName(songName) {
    await initDatabase();
    
    if (!songName || songName.trim() === '') {
        return [];
    }
    
    const query = `
        SELECT 
            t.name AS track_name,
            sta.name AS track_artist,
            rci.name AS album_artist,
            ai.album_name,
            ai.url_links,
            ai.genre
        FROM tracks t
        JOIN track_vs_source_index tvs ON t.id = tvs.track_id
        JOIN source_tracks st ON tvs.source_track_id = st.id
        JOIN songtrack_artist_index sta ON t.songtrack_artist_id = sta.id
        JOIN release_circle_index rci ON t.release_circle_id = rci.id
        JOIN albums_index ai ON t.album_id = ai.id
        WHERE t.name LIKE ? 
           OR ai.album_name LIKE ?
           OR rci.name LIKE ?
           OR sta.name LIKE ?
        ORDER BY rci.name
    `;
    
    const searchPattern = `%${songName}%`;
    const stmt = db.prepare(query);
    stmt.bind([searchPattern, searchPattern, searchPattern, searchPattern]);
    
    const results = [];
    while (stmt.step()) {
        // Use get() to get values by index (more reliable than getAsObject)
        const row = stmt.get();
        results.push([
            row[0] || '',  // track_name
            row[1] || '',  // track_artist
            row[2] || '',  // album_artist
            row[3] || '',  // album_name
            row[4] || null, // url_links
            row[5] || null  // genre
        ]);
    }
    
    stmt.free();
    return results;
}

