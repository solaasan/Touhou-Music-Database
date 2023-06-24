# Touhou Doujinshi Music Database v0.69

This database is a project to enable reverse searching through any and all Touhou doujinshi music releases found online. It contains a normalized SQLite3 database with some album metadata. The main purpose is to look up a song and find the source ZUN/Touhou tracks it originates from or vice versa. If you're searching for actual metadata on albums, visit [TouhouDB](https://touhoudb.com/). The scraping of this data was made possible thanks to GPT-4 and a number of open source projects surrounding it.

The database schema is as follows:

## Database Schema

1. `source_tracks`: Table containing information about source tracks.
    - `id`: Integer, primary key, autoincrement
    - `name`: Text, not null

2. `release_circle_index`: Table containing information about release circles (album artists).
    - `id`: Integer, primary key, autoincrement
    - `name`: Text, not null

3. `songtrack_artist_index`: Table containing information about song track artists.
    - `id`: Integer, primary key, autoincrement
    - `name`: Text, not null

4. `track_vs_source_index`: Table representing relationships between tracks and their source tracks.
    - `track_id`: Integer, primary key, foreign key references `tracks` table
    - `source_track_id`: Integer, primary key, foreign key references `source_tracks` table

5. `albums_index`: Table containing information about albums.
    - `id`: Integer, primary key, autoincrement
    - `album_name`: Text, not null
    - `url_links`: Text
    - `tlmc_path`: Text, not null
    - `genre`: Text
    - `disc_number`: Integer

6. `tracks`: Table containing information about tracks.
    - `id`: Integer, primary key, autoincrement
    - `name`: Text, not null
    - `track_number`: Integer
    - `album_id`: Integer, foreign key references `albums_index` table
    - `release_circle_id`: Integer, foreign key references `release_circle_index` table
    - `songtrack_artist_id`: Integer, foreign key references `songtrack_artist_index` table

The given database schema consists of six tables, and each table represents a distinct entity or relationship in the database.

1. `source_tracks` table holds information about source tracks, which are the original songs that other tracks are derived or influenced from.

2. `release_circle_index` table contains information about release circles, which can be considered as the album artists responsible for creating and releasing albums.

3. `songtrack_artist_index` table stores information about song track artists, who are the individual artists performing or contributing to the tracks in the album.

4. `track_vs_source_index` table represents the relationships between tracks and their source tracks. This is a one-to-many relationship, as a single source track can be associated with multiple tracks in the database. The table has two primary keys - `track_id` and `source_track_id`, both referencing other tables.

5. `albums_index` table contains information about albums, such as their names, URLs, genres, and disc numbers.

6. `tracks` table holds information about individual tracks in an album, including their names, track numbers, and associated album, release circle, and song track artist IDs.

The schema is normalized to avoid data redundancy and improve data consistency. For example, instead of repeatedly storing the name of a release circle or song track artist for each track, the schema stores this information once in respective tables (`release_circle_index` and `songtrack_artist_index`) and refers to them using foreign keys (`release_circle_id` and `songtrack_artist_id`) in the `tracks` table.

Similarly, `track_vs_source_index` table is used to maintain the one-to-many relationships between tracks and their source tracks without duplicating data. Each row in the `track_vs_source_index` table links a `track_id` to its corresponding `source_track_id`. This way, if there are multiple tracks derived from the same source track, the source track information is not duplicated, and only the relationships are stored in `track_vs_source_index` table.


If an album exists in the [TLMC v3](https://nyaa.si/view/1625916), I have attempted to indicate its location. The matching logic for this search is stored in [tlmc_searcher.py](misc_scripts/tlmc_searcher.py). Neither this GitHub repository nor myself have any relation to that collection or the wonderful folks behind it. This was collected based on personal interests.

### Disclaimer

source_track metadata has some funny values in the lowest percentile, still deciding how to manage that such as to remove outlier values. Some "source_tracks" in the low single digit occurances are non-touhou tracks, ie Kirby or Undertale.

## Example SQL Query

Below is a sample SQL query to find all Nuclear Fusion songs based on Okuu's theme:

```sql
SELECT
    tracks.name AS track_name,
    release_circle_index.name AS album_artist,
    albums_index.album_name,
    albums_index.url_links
FROM
    tracks
    INNER JOIN track_vs_source_index ON tracks.id = track_vs_source_index.track_id
    INNER JOIN source_tracks ON track_vs_source_index.source_track_id = source_tracks.id
    INNER JOIN release_circle_index ON tracks.release_circle_id = release_circle_index.id
    INNER JOIN albums_index ON tracks.album_id = albums_index.id
WHERE
    source_tracks.id = 120;
```

or a query to display all albums I was not able to succesfully match with TLMC v3:

```sql
SELECT *
FROM albums_index
WHERE tlmc_path IS NULL
OR tlmc_path = '';
```

[Sample results](sample_query/tlmc.csv) of this query are available as a CSV.

## Using the Database with SQLite Viewer

If you are not familiar with technical tools like SQL, you can still use this database using an online SQLite viewer. Follow these steps:

1. Go to https://inloop.github.io/sqlite-viewer/.
2. Drag the database file into the browser window.
3. Copy and paste the following query into the textbox:

```sql
SELECT * FROM 'source_tracks' LIMIT 0,1528
```
4. Click execute, use Ctrl + F to find the theme you want. Do note these are the Japanese Names.
5. Refer to the sample query provided just above and as well below for Nuclear Fusion, that uses `120` however update the number for the one you would wish to reverse search:

```sql
SELECT
    tracks.name AS track_name,
    release_circle_index.name AS album_artist,
    albums_index.album_name,
    albums_index.url_links
FROM
    tracks
    INNER JOIN track_vs_source_index ON tracks.id = track_vs_source_index.track_id
    INNER JOIN source_tracks ON track_vs_source_index.source_track_id = source_tracks.id
    INNER JOIN release_circle_index ON tracks.release_circle_id = release_circle_index.id
    INNER JOIN albums_index ON tracks.album_id = albums_index.id
WHERE
    source_tracks.id = 120;
```

5. Click "Execute SQL" to run the query, and the resulting table will display all the relevant songs. If you are using a macOS, you can easily copy and paste the results into a spreadsheet for further review. Other opperating systems likely the same.

