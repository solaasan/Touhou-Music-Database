import sqlite3
import csv

# Connect to the database.
conn = sqlite3.connect('../touhou-music.db')
cur = conn.cursor()

# Execute the SQL query.
query = '''
SELECT DISTINCT
    albums_index.album_name,
    release_circle_index.name AS album_artist,
    url_links,
    genre,
    tlmc_path,
    albums_index.id AS album_id
FROM
    albums_index
    INNER JOIN tracks ON albums_index.id = tracks.album_id
    INNER JOIN release_circle_index ON tracks.release_circle_id = release_circle_index.id
WHERE
    albums_index.tlmc_path IS NOT NULL AND albums_index.tlmc_path != '';
'''
cur.execute(query)

# Fetch the result of the query.
result = cur.fetchall()

# Write the result to a CSV file.
with open('../sample_query/tlmc.csv', 'w', newline='', encoding='utf-8') as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(['album_name', 'album_artist', 'url_links', 'genre', 'tlmc_path', 'internal album_id'])
    csv_writer.writerows(result)

# Close the database connection.
cur.close()
conn.close()
