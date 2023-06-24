import os
import re
import sqlite3
from fuzzywuzzy import fuzz


##Uncomment and change these default values
#OLD_DATABASE_PATH = "reference_2hu.db"
#NEW_DATABASE_PATH = "touhou_music.db"
#LOCAL_MUSIC_PATH = "/mnt2/Touhou/"


#########

def create_new_database():
    conn_old = sqlite3.connect(OLD_DATABASE_PATH)
    conn_new = sqlite3.connect(NEW_DATABASE_PATH)

    # Copy the schema from the old database to the new database
    with conn_old as old_db, conn_new as new_db:
        for line in old_db.iterdump():
            if line.startswith("COMMIT"):
                continue
            elif line.startswith("BEGIN"):
                new_db.execute("BEGIN")
            else:
                new_db.execute(line)
        new_db.commit()
def update_album_tlmc_path():
    conn = sqlite3.connect(NEW_DATABASE_PATH)
    cursor = conn.cursor()

    sql_query = '''
        SELECT
            id,
            album_name,
            tlmc_path
        FROM
            albums_index;
        '''
    albums = cursor.execute(sql_query).fetchall()

    # Print tlmc_path values before clearing them
    print("Before clearing:")
    for album_id, album_name, tlmc_path in albums:
        print(album_id, album_name, tlmc_path)

    # Clear old tlmc_path values
    cursor.execute("UPDATE albums_index SET tlmc_path = ''")
    conn.commit()

    # Print tlmc_path values after clearing them
    print("After clearing:")
    cleared_albums = cursor.execute(sql_query).fetchall()
    for album_id, album_name, tlmc_path in cleared_albums:
        print(album_id, album_name, tlmc_path)

    for album_id, album_name, tlmc_path in albums:
        found_path = ""

        for artist_dir in os.listdir(LOCAL_MUSIC_PATH):
            artist_path = os.path.join(LOCAL_MUSIC_PATH, artist_dir)

            for album_dir in os.listdir(artist_path):
                # Remove date code if present before the album name
                album_name_only = re.sub(r'\d{4}\.\d{2}\.\d{2}\s?', '', album_dir.split('] ')[-1])

                if fuzz.token_set_ratio(album_name_only.lower(), album_name.lower()) >= 70:
                    album_path = os.path.join(artist_dir, album_dir)
                    found_path = album_path
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