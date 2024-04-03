from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    facebook_link = db.Column(db.String(120), nullable=True)
    image_link = db.Column(db.String(500), nullable=True)
    website_link = db.Column(db.String(500), nullable=True)
    seeking_talent = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String(500), nullable=True)
    genres = db.relationship('VenueGenre', backref='venue', cascade='all, delete-orphan')
    shows = db.relationship('Show', backref='venueForShows', cascade='all, delete-orphan')

class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    facebook_link = db.Column(db.String(120), nullable=True)
    image_link = db.Column(db.String(500), nullable=True)
    website_link = db.Column(db.String(500), nullable=True)
    seeking_venue = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String(500), nullable=True)
    genres = db.relationship('ArtistGenre', backref='artist', cascade='all, delete-orphan')
    shows = db.relationship('Show', backref='artistForShows', cascade='all, delete-orphan')
    
    def __repr__(self) -> str:
      return f'<artist {self.id} {self.name}>'
      
class ArtistGenre(db.Model):
    __tablename__ = 'artist_genre'
    id = db.Column(db.Integer, primary_key=True)
    genre = db.Column(db.String(35))
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
      
class VenueGenre(db.Model):
    __tablename__ = 'venue_genre'
    id = db.Column(db.Integer, primary_key=True)
    genre = db.Column(db.String(35))
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    
class Show(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    
    def __repr__(self) -> str:
      return f'<show {self.id} {self.start_time}>'
