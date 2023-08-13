import os
import re
import sqlite3
from fuzzywuzzy import fuzz
from pathlib import Path

NEW_DATABASE_PATH = "./lossless_touhou_music.db"
OLD_DATABASE_PATH = "./touhou-music.db"
LOCAL_MUSIC_PATH = "/media/Music/Touhou/"
IGNORE_DIRS = ['opus', '@eaDir', '.DS_Store']  # Ignore these directories
DIFF_NUMBER_CHECK = r'\b\d+\b'

#########

def create_new_database():
    conn_old = sqlite3.connect(OLD_DATABASE_PATH)
    conn_new = sqlite3.connect(NEW_DATABASE_PATH)

    with conn_old as old_db, conn_new as new_db:
        for line in old_db.iterdump():
            if line.startswith("COMMIT"):
                continue
            elif line.startswith("BEGIN"):
                new_db.execute("BEGIN")
            else:
                new_db.execute(line)
        new_db.commit()

def check_number_difference(album1, album2, DIFF_NUMBER_CHECK):
    album1_numbers = re.findall(DIFF_NUMBER_CHECK, album1)
    album2_numbers = re.findall(DIFF_NUMBER_CHECK, album2)

    if len(album1_numbers) == len(album2_numbers) == 0:
        return False

    if len(album1_numbers) != len(album2_numbers):
        return True

    return any(int(a) != int(b) for a, b in zip(album1_numbers, album2_numbers))


def update_album_tlmc_path():
    conn = sqlite3.connect(NEW_DATABASE_PATH)
    cursor = conn.cursor()

    sql_query = '''
        SELECT
            a.id, 
            a.album_name, 
            a.tlmc_path, 
            c.name as artist 
        FROM
            albums_index a 
        JOIN
            tracks t ON a.id = t.album_id 
        JOIN
            release_circle_index c ON t.release_circle_id = c.id;
        '''
    albums = cursor.execute(sql_query).fetchall()

    print("Before clearing:")
    for album_id, album_name, tlmc_path, artist in albums:
        print(album_id, album_name, tlmc_path, artist)

    cursor.execute("UPDATE albums_index SET tlmc_path = ''")
    conn.commit()

    print("After clearing:")
    cleared_albums = cursor.execute(sql_query).fetchall()
    for album_id, album_name, tlmc_path, artist in cleared_albums:
        print(album_id, album_name, tlmc_path, artist)

    date_re = re.compile(r"\d{4}\.\d{2}.\d{2}")
    event_re = re.compile(r"\[.*\]")

    for album_id, album_name, tlmc_path, artist_name in albums:
        found_path = ""

        for artist_dir in os.listdir(LOCAL_MUSIC_PATH):
            if artist_dir in IGNORE_DIRS:
                continue
            artist_path = os.path.join(LOCAL_MUSIC_PATH, artist_dir)

            artist_dir_only_list = re.findall(r'\[(.*?)\]', artist_dir)
    
            if not artist_dir_only_list: # if artist_dir_only_list is empty
                continue

            artist_dir_only = artist_dir_only_list[0]

            if fuzz.ratio(artist_dir_only.lower(), artist_name.lower()) < 95:
                continue

            for album_dir in os.listdir(artist_path):
                if album_dir in IGNORE_DIRS:
                    continue

                full_path = os.path.join(artist_path, album_dir)

                album_parts = album_dir.split(' ')

                album_name_only = ""
                for part in album_parts:
                    if date_re.match(part) or event_re.match(part):
                        continue
                    else:
                        album_name_only += " " + part
                album_name_only = album_name_only.strip()

                if fuzz.token_set_ratio(album_name_only.lower(), album_name.lower()) >= 85:
                    if check_number_difference(album_name_only, album_name, DIFF_NUMBER_CHECK):
                        continue
                    found_path = full_path.replace(LOCAL_MUSIC_PATH, '')
                    break

            if found_path:
                break

        if found_path:
            print(f"Updating album_id {album_id} with found_path {found_path}")
            cursor.execute(
                "UPDATE albums_index SET tlmc_path = ? WHERE id = ?",
                (found_path, album_id)
            )
            conn.commit()

if __name__ == "__main__":
    create_new_database()
    update_album_tlmc_path()