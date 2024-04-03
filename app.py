#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys
import dateutil.parser
import babel
from flask import (
  Flask,
  render_template,
  request,
  Response,
  flash,
  redirect, url_for
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import func
from forms import *
from flask_migrate import Migrate
from models import db, Venue, Artist, Show, VenueGenre, ArtistGenre

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)
app.app_context().push()

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # Query all distinct city/state pairs
  areas = Venue.query.with_entities(Venue.city, Venue.state).distinct().all()

  data = []

  # For each city/state pair
  for area in areas:
    city, state = area

    # Query the venues in this city/state
    venues = Venue.query.filter_by(city=city, state=state).all()

    # Add the city/state and venues to the data
    data.append({
      "city": city,
      "state": state,
      "venues": [{
        "id": venue.id,
        "name": venue.name,
      } for venue in venues]
    })

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term=request.form.get('search_term', '')
  artists = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()  
  response={
    "count": len(artists),
    "data": [{
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len([show for show in artist.shows if show.start_time >= datetime.now()]),
    } for artist in artists]
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  venue = db.session.query(Venue).outerjoin(Show, Show.venue_id == Venue.id).filter(Venue.id == venue_id).first()
  past_shows = db.session.query(Show).join(Venue, Show.venue_id == Venue.id).filter(Show.start_time < datetime.now(), Venue.id == venue_id).all()
  upcoming_shows = db.session.query(Show).join(Venue, Show.venue_id == Venue.id).filter(Show.start_time >= datetime.now(), Venue.id == venue_id).all()
  venue_genres = db.session.query(VenueGenre.genre).filter(VenueGenre.venue_id == venue_id).all()

  realData = {
    "id": venue.id,
    "name": venue.name,
    "genres": [genre[0] for genre in venue_genres],
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": [{
      "artist_id": show.artist_id,
      "artist_name": show.artistForShows.name,
      "artist_image_link": show.artistForShows.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S")
    } for show in past_shows],
    "upcoming_shows": [{
      "artist_id": show.artist_id,
      "artist_name": show.artistForShows.name,
      "artist_image_link": show.artistForShows.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S")
    } for show in upcoming_shows],
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_venue.html', venue=realData)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form, meta={'csrf': False})
  if form.validate():
    
    try:
      newVenue = Venue(
        name=form.name.data,
        city=form.city.data,
        state=form.state.data,
        phone=form.phone.data,
        facebook_link=form.facebook_link.data,
        image_link=form.image_link.data,
        website_link=form.website_link.data,
        seeking_talent=bool(form.seeking_talent.data),
        seeking_description=form.seeking_description.data) 
      db.session.add(newVenue)
      db.session.commit()
          
      genres = form.genres.data
      print(genres)
      for genre_name in genres:
        genre = VenueGenre(genre=genre_name, venue_id=newVenue.id)
        db.session.add(genre)
      
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
      print(e)
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
      db.session.rollback()
    finally:
      db.session.close()
    return render_template('pages/home.html')
  else:
    for field, errors in form.errors.items():
      for error in errors:
        flash(f'{field}: {error}')
        form = VenueForm()
        return render_template('forms/new_venue.html', form=form)

@app.route('/venues/delete/<venue_id>', methods=['GET'])
def delete_venue(venue_id):
  venue = Venue.query.get(venue_id)
  try:
    db.session.delete(venue)
    db.session.commit()
    flash('Venue was successfully deleted!')
  except Exception as e:
    print(e)
    flash('An error occurred. Venue could not be deleted.')
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  return render_template('pages/artists.html', artists=Artist.query.with_entities(Artist.id, Artist.name).all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term=request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()  
  response={
    "count": len(artists),
    "data": [{
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len([show for show in artist.shows if show.start_time >= datetime.now()]),
    } for artist in artists]
  }
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  artist = db.session.query(Artist).outerjoin(Show, Show.artist_id == Artist.id).filter(Artist.id == artist_id).first()
  past_shows = db.session.query(Show).join(Artist, Show.artist_id == Artist.id).filter(Show.start_time < datetime.now(), Artist.id == artist_id).all()
  upcoming_shows = db.session.query(Show).join(Artist, Show.artist_id == Artist.id).filter(Show.start_time >= datetime.now(), Artist.id == artist_id).all()
  artist_genres = db.session.query(ArtistGenre.genre).filter(ArtistGenre.artist_id == artist_id).all()
  realData = {
    "id": artist.id,
    "name": artist.name,
    "genres": [genre[0] for genre in artist_genres],
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": [{
      "artist_id": show.artist_id,
      "artist_name": show.artistForShows.name,
      "artist_image_link": show.venueForShows.image_link,
    "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S")
    } for show in past_shows],
    "upcoming_shows": [{
      "artist_id": show.artist_id,
      "artist_name": show.artistForShows.name,
      "artist_image_link": show.venueForShows.image_link,
    "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S")
    } for show in upcoming_shows],
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=realData)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  return render_template('forms/edit_artist.html', form=form, artist=Artist.query.get(artist_id))

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # take values from the form submitted, and update existing artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      updateArtist = Artist.query.get(artist_id)
      updateArtist.name = form.name.data
      updateArtist.city = form.city.data
      updateArtist.state = form.state.data
      updateArtist.phone = form.phone.data
      updateArtist.facebook_link = form.facebook_link.data
      updateArtist.image_link = form.image_link.data
      updateArtist.website_link = form.website_link.data
      updateArtist.seeking_venue = bool(form.seeking_venue.data)
      updateArtist.seeking_description = form.seeking_description.data
      db.session.commit()
      
      genres = form.genres.data
      updateGenres = ArtistGenre.query.filter(ArtistGenre.artist_id == artist_id).all()
      
      for genre in updateGenres:
        db.session.delete(genre)
        
      for genre in genres:
        newGenre = ArtistGenre(genre=genre, artist_id=artist_id)
        db.session.add(newGenre)
        
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully updated!')
    except Exception as e:
      print(e)
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
      db.session.rollback()
    finally:
      db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))
  else:
    for field, errors in form.errors.items():
      for error in errors:
        flash(f'{field}: {error}')
        form = ArtistForm()
        return render_template('forms/edit_artist.html', form=form, artist=Artist.query.get(artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  return render_template('forms/edit_venue.html', form=form, venue=Venue.query.get(venue_id))

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # take values from the form submitted, and update existing venue record with ID <venue_id> using the new attributes 
  form = VenueForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      updateVenue = Venue.query.get(venue_id)
      updateVenue.name = form.name.data
      updateVenue.city = form.city.data
      updateVenue.state = form.state.data
      updateVenue.phone = form.phone.data
      updateVenue.facebook_link = form.facebook_link.data
      updateVenue.image_link = form.image_link.data
      updateVenue.website_link = form.website_link.data
      updateVenue.seeking_talent = bool(form.seeking_talent.data)
      updateVenue.seeking_description = form.seeking_description.data
      db.session.commit()
      
      genres = form.genres.data
      updateGenres = VenueGenre.query.filter(VenueGenre.venue_id == venue_id).all()
      
      for genre in updateGenres:
        db.session.delete(genre)
        
      for genre in genres:
        newGenre = VenueGenre(genre=genre, venue_id=venue_id)
        db.session.add(newGenre)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully updated!')
    except Exception as e:
      print(e)
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
      db.session.rollback()
    finally:
      db.session.close()
      
    return redirect(url_for('show_venue', venue_id=venue_id))
  else:
    for field, errors in form.errors.items():
      for error in errors:
        flash(f'{field}: {error}')
        form = VenueForm()
        return render_template('forms/edit_venue.html', form=form, venue=Venue.query.get(venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  form = ArtistForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      newArtist = Artist(
        name=form.name.data,
        city=form.city.data,
        state=form.state.data,
        phone=form.phone.data,
        facebook_link=form.facebook_link.data,
        image_link=form.image_link.data,
        website_link=form.website_link.data,
        seeking_venue=bool(form.seeking_venue.data),
        seeking_description=form.seeking_description.data) 
      db.session.add(newArtist)
      db.session.commit()
          
      genres = form.genres.data
      
      for genre_name in genres:
        genre = ArtistGenre(genre=genre_name, artist_id=newArtist.id)
        db.session.add(genre)
      
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
      print(e)
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
      db.session.rollback()
    finally:
      db.session.close()

    return render_template('pages/home.html')
  else:
    for field, errors in form.errors.items():
      for error in errors:
        flash(f'{field}: {error}')
        form = ArtistForm()
        return render_template('forms/new_artist.html', form=form)

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  realData = db.session.query(
    Show.venue_id,
    Venue.name.label('venue_name'),
    Show.artist_id,
    Artist.name.label('artist_name'),
    Artist.image_link.label('artist_image_link'),
    func.to_char(Show.start_time, 'YYYY-MM-DD"T"HH12:MI:SS').label('start_time')
  ).join(Venue, Show.venue_id == Venue.id).join(Artist, Show.artist_id == Artist.id).all()
  return render_template('pages/shows.html', shows=realData)

@app.route('/shows/create')
def create_shows():
  artists = Artist.query.with_entities(Artist.id, Artist.name).all()
  venues = Venue.query.with_entities(Venue.id, Venue.name).all()
  return render_template('forms/new_show.html', artists=artists, venues=venues)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  try:
    newShow = Show(start_time=request.form.get('start_time'),
                    artist_id=request.form.get('artist_id'),
                    venue_id=request.form.get('venue_id')) 
    db.session.add(newShow)
    db.session.commit()
    flash('Show was successfully listed!')
  except Exception as e:
    print(e)
    flash('An error occurred. Show could not be listed.')
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
