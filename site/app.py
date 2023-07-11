from flask import Flask, render_template, request, make_response, session as flask_session
from flask_session import Session
from io import StringIO
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func, desc

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

@app.route('/download_csv', methods=['GET'])
def download_csv():
    csv_file = StringIO()
    writer = csv.writer(csv_file)
    writer.writerow(['Track Name', 'Track Artist', 'Album Artist', 'Album Name', 'URL'])
    if 'fetched_results' in flask_session:
       writer.writerows(flask_session['fetched_results'])
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
    if request.method == 'POST':
        with Session() as session:
            source_track_id = request.form['source_track_id']
            results = session.execute(
                session.query(
                    Tracks.name,
                    SongTrackArtistIndex.name,
                    ReleaseCircleIndex.name,
                    AlbumsIndex.album_name,
                    AlbumsIndex.url_links,
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
            flask_session['fetched_results'] = [list(r) for r in fetched_results]
        return render_template('results.html', results=fetched_results)
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

if __name__ == '__main__':
    app.run(host='localhost', port=8050) 
