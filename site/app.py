from flask import Flask, render_template, request, make_response, session as flask_session, redirect, url_for
from flask_session import Session
from io import StringIO
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func, desc
from sqlalchemy import literal, or_
import re

Base = declarative_base()

class SourceTracks(Base):
    __tablename__ = 'source_tracks'
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)

class ReleaseCircleIndex(Base):
    __tablename__ = 'release_circle_index'
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)

class SongTrackArtistIndex(Base):
    __tablename__ = 'songtrack_artist_index'
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)

class TrackVsSourceIndex(Base):
    __tablename__ = 'track_vs_source_index'
    track_id = Column(Integer, ForeignKey('tracks.id'), primary_key=True)
    source_track_id = Column(Integer, ForeignKey('source_tracks.id'), primary_key=True)

class AlbumsIndex(Base):
    __tablename__ = 'albums_index'
    id = Column(Integer, primary_key=True)
    album_name = Column(Text, nullable=False)
    url_links = Column(Text)
    tlmc_path = Column(Text)
    genre = Column(Text)
    disc_number = Column(Integer)

class Tracks(Base):
    __tablename__ = 'tracks'
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    track_number = Column(Integer)
    album_id = Column(Integer, ForeignKey('albums_index.id'))
    release_circle_id = Column(Integer, ForeignKey('release_circle_index.id'))
    songtrack_artist_id = Column(Integer, ForeignKey('songtrack_artist_index.id'))

app = Flask(__name__)
app.config['CSV_FILENAME'] = "results.csv"
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

@app.route('/search-song', methods=['GET', 'POST'])
def search_song():
    engine = create_engine("sqlite:///touhou-music.db")
    Session = sessionmaker(bind=engine)
    song_name = request.args.get('song', '')
    
    if song_name != '':
        query = "%{}%".format(song_name)
        with Session() as session:
            results = session.execute(
                session.query(
                    Tracks.name,
                    SongTrackArtistIndex.name,
                    ReleaseCircleIndex.name,
                    AlbumsIndex.album_name,
                    AlbumsIndex.url_links,
                    AlbumsIndex.genre
                ).join(
                    TrackVsSourceIndex, Tracks.id == TrackVsSourceIndex.track_id
                ).join(
                    SourceTracks, TrackVsSourceIndex.source_track_id == SourceTracks.id
                ).join(
                    SongTrackArtistIndex, Tracks.songtrack_artist_id == SongTrackArtistIndex.id
                ).join(
                    ReleaseCircleIndex, Tracks.release_circle_id == ReleaseCircleIndex.id
                ).join(
                    AlbumsIndex, Tracks.album_id == AlbumsIndex.id
                ).filter(or_(Tracks.name.like(query),
                             AlbumsIndex.album_name.like(query),
                             ReleaseCircleIndex.name.like(query),
                             SongTrackArtistIndex.name.like(query),
                             SourceTracks.name.like(query)))       # Filtered by like
                .order_by(
                    ReleaseCircleIndex.name
                )
            )
            fetched_results = results.fetchall()
            flask_session['fetched_results'] = [[r if i!=5 else 'Not Available' for i, r in enumerate(row)]  for row in fetched_results] 
        return render_template('results-songs.html', results=fetched_results, query=song_name)

    else:
        with Session() as session:
            source_tracks = session.execute(
                session.query(
                    SourceTracks.id,
                    SourceTracks.name,
                    func.count(TrackVsSourceIndex.track_id).label('count')
                ).join(
                    TrackVsSourceIndex, SourceTracks.id == TrackVsSourceIndex.source_track_id 
                ).group_by(
                    SourceTracks.id
                ).order_by(
                    desc('count')
                )
            ).fetchall()

        return render_template('search.html', source_tracks=source_tracks)

@app.route('/download_song_csv', methods=['GET'])
def download_song_csv():
    song_name = request.args.get('song_name', '')
    if song_name != '':
        query = "%{}%".format(song_name)
        engine = create_engine("sqlite:///touhou-music.db")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        results = session.query(
            Tracks.name,
            SongTrackArtistIndex.name,
            ReleaseCircleIndex.name,
            AlbumsIndex.album_name,
            AlbumsIndex.url_links,
            AlbumsIndex.genre
        ).join(
            TrackVsSourceIndex, Tracks.id == TrackVsSourceIndex.track_id
        ).join(
            SourceTracks, TrackVsSourceIndex.source_track_id == SourceTracks.id
        ).join(
            SongTrackArtistIndex, Tracks.songtrack_artist_id == SongTrackArtistIndex.id
        ).join(
            ReleaseCircleIndex, Tracks.release_circle_id == ReleaseCircleIndex.id
        ).join(
            AlbumsIndex, Tracks.album_id == AlbumsIndex.id
        ).filter(
            Tracks.name.like(query)
        ).order_by(
            ReleaseCircleIndex.name
        ).all()   # Fetch all results

        session.close()

        csv_file = StringIO()
        writer = csv.writer(csv_file)
        writer.writerow(["Track Name", "Track Artist", "Album Artist", "Album Name", "URL", "Album Genre"])
        writer.writerows(results)
        csv_file.seek(0)
        response = make_response(csv_file.getvalue())
        filename = f"{song_name}_results.csv"
        response.headers.set('Content-Disposition', 'attachment', filename=filename)
        response.mimetype='text/csv'
        return response
    else:
        return redirect(url_for('search_song'))


@app.route('/download_csv/<int:source_track_id>', methods=['GET'])
def download_csv(source_track_id):
    if source_track_id > 9999:
        return render_template('error.html', message="Invalid input. Please enter upto 4 numbers.")
    engine = create_engine("sqlite:///touhou-music.db")
    Session = sessionmaker(bind=engine)
    with Session() as session:
        results = session.execute(
            session.query(
                Tracks.name,
                SongTrackArtistIndex.name,
                ReleaseCircleIndex.name,
                AlbumsIndex.album_name,
                AlbumsIndex.url_links,
                AlbumsIndex.genre
            ).join(
                TrackVsSourceIndex, Tracks.id == TrackVsSourceIndex.track_id
            ).join(
                SourceTracks, TrackVsSourceIndex.source_track_id == SourceTracks.id
            ).join(
                SongTrackArtistIndex, Tracks.songtrack_artist_id == SongTrackArtistIndex.id
            ).join(
                ReleaseCircleIndex, Tracks.release_circle_id == ReleaseCircleIndex.id
            ).join(
                AlbumsIndex, Tracks.album_id == AlbumsIndex.id
            ).filter(
                SourceTracks.id == source_track_id
            ).order_by(
                ReleaseCircleIndex.name
            )   
        )
        fetched_results = results.fetchall()
    csv_file = StringIO()
    writer = csv.writer(csv_file)
    writer.writerow(['Track Name', 'Track Artist', 'Album Artist', 'Album Name', 'URL', 'Album Genre'])  # This line is edited
    writer.writerows(fetched_results)
    csv_file.seek(0)
    response = make_response(csv_file.getvalue())
    cd = 'attachment; filename=' + app.config['CSV_FILENAME']
    response.headers.set('Content-Disposition', 'attachment', filename=app.config['CSV_FILENAME'])
    response.mimetype='text/csv'
    return response
    

@app.route('/', methods=['GET', 'POST'])
def search2():
    engine = create_engine("sqlite:///touhou-music.db")
    Session = sessionmaker(bind=engine)
    query = request.args.get('query', '')
    if query.isdigit() and len(query) <= 4:
        source_track_id = query
        with Session() as session:
            results = session.execute(
                session.query(
                    Tracks.name,
                    SongTrackArtistIndex.name,
                    ReleaseCircleIndex.name,
                    AlbumsIndex.album_name,
                    AlbumsIndex.url_links,
                    AlbumsIndex.genre
                ).join(
                    TrackVsSourceIndex, Tracks.id == TrackVsSourceIndex.track_id
                ).join(
                    SourceTracks, TrackVsSourceIndex.source_track_id == SourceTracks.id
                ).join(
                    SongTrackArtistIndex, Tracks.songtrack_artist_id == SongTrackArtistIndex.id
                ).join(
                    ReleaseCircleIndex, Tracks.release_circle_id == ReleaseCircleIndex.id
                ).join(
                    AlbumsIndex, Tracks.album_id == AlbumsIndex.id
                ).filter(
                    SourceTracks.id == source_track_id
                ).order_by(
                    ReleaseCircleIndex.name
                )   
            )
            fetched_results = results.fetchall()
            flask_session['fetched_results'] = [[r if i!=5 else 'Not Available' for i, r in enumerate(row)]  for row in fetched_results]  # This line is edited
        return render_template('results.html', results=fetched_results, query=source_track_id)
    else:
        with Session() as session:
            source_tracks = session.execute(
                session.query(
                    SourceTracks.id,
                    SourceTracks.name,
                    func.count(TrackVsSourceIndex.track_id).label('count')
                ).join(
                    TrackVsSourceIndex, SourceTracks.id == TrackVsSourceIndex.source_track_id 
                ).filter(SourceTracks.id != 35)
                .group_by(
                    SourceTracks.id
                ).order_by(
                    desc('count')
                )
            ).fetchall()

        return render_template('search.html', source_tracks=source_tracks)

if __name__ == '__main__':
    app.run(host='localhost', port=8050)