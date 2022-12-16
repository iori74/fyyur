# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
from pickle import FALSE
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from forms import *
from sqlalchemy import create_engine, exc, func, and_
from markupsafe import Markup
import sys
import time


# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Show(db.Model):
    __tablename__ = "Show"

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'Artist.id',
            ondelete="CASCADE"),
        nullable=False)
    venue_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'Venue.id',
            ondelete="CASCADE"),
        nullable=False)
    start_time = db.Column(
        db.DateTime(
            timezone=True),
        onupdate=func.now(),
        nullable=True)
    artist = db.relationship("Artist", backref="show_artists", lazy=True)
    venue = db.relationship("Venue", backref="show_venues", lazy=True)
    #db.Column('start_time', db.DateTime(timezone=True), onupdate=func.now(), nullable=True)


class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, nullable=True, default=False)
    seeking_description = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    num_upcoming_shows = db.Column(db.Integer)
    show = db.relationship(
        "Show",
        backref="venue_shows",
        cascade="all, delete",
        overlaps="show_venues,venue",
        lazy='dynamic')

    def intelligence(self):
        return {
            "id": self.id,
            "name": self.name,
            "city": self.city,
            "state": self.state
        }

    # TODO: implement any missing fields, as a database migration using
    # Flask-Migrate


class Artist(db.Model):
    __tablename__ = 'Artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=True, default=False)
    seeking_description = db.Column(db.String(500))
    show = db.relationship(
        "Show",
        backref="artist_shows",
        cascade="all, delete",
        overlaps="artist,show_artists",
        lazy='dynamic')

    def identity(self):
        return {
            "id": self.id,
            "name": self.name
        }

    # TODO: implement any missing fields, as a database migration using
    # Flask-Migrate

# TODO Implement Show and Artist models, and complete all model
# relationships and properties, as a database migration.

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    # num_upcoming_shows should be aggregated based on number of upcoming
    # shows per venue.
    venue = Venue.query.all()
    data = [ven.intelligence() for ven in venue]
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live
    # Music & Coffee"

    search_term = request.form.get('search_term', '')
    search_word = Venue.query.filter(
        Venue.name.ilike(
            '%{}%'.format(search_term)))
    list_id = [venue.id for venue in search_word]

    response = {
        "count": len(list_id),
        "data": search_word
    }
    return render_template(
        'pages/search_venues.html',
        results=response,
        search_term=request.form.get(
            'search_term',
            ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    found_venue = Venue.query.get(venue_id)

    shows = Show.query.filter(
        and_(
            Show.start_time < datetime.now(),
            Show.venue_id == venue_id))
    past_shows = []
    for show in shows:
        artist = Artist.query.get(show.artist_id)
        show_data = {
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": str(show.start_time),
        }
        past_shows.append(show_data)
    shows = Show.query.filter(
        and_(
            Show.start_time >= datetime.now(),
            Show.venue_id == venue_id))
    upcoming_shows = []
    for show in shows:
        artist = Artist.query.get(show.artist_id)
        show_data = {
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": str(show.start_time),
        }
        upcoming_shows.append(show_data)

    data = {
        "id": found_venue.id,
        "name": found_venue.name,
        "genres": found_venue.genres.split(','),
        "address": found_venue.address,
        "city": found_venue.city,
        "state": found_venue.state,
        "phone": found_venue.phone,
        "website": found_venue.website,
        "facebook_link": found_venue.facebook_link,
        "seeking_talent": found_venue.seeking_talent,
        "seeking_description": found_venue.seeking_description,
        "image_link": found_venue.image_link,
        "past_shows": past_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows": upcoming_shows,
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    try:
        name = request.form.get("name")
        city = request.form.get("city")
        state = request.form.get("state")
        address = request.form.get("address")
        phone = request.form.get("phone")
        genres = request.form.getlist("genres")
        facebook_link = request.form.get("facebook_link")
        image_link = request.form.get("image_link")
        website_link = request.form.get("website_link")
        seeking_talent = request.form.get('seeking_talent', type=bool)
        seeking_description = request.form.get('seeking_description')

        new_venue = Venue(
            name=name,
            city=city,
            state=state,
            address=address,
            phone=phone,
            genres=','.join(genres),
            facebook_link=facebook_link,
            image_link=image_link,
            website=website_link,
            seeking_talent=seeking_talent,
            seeking_description=seeking_description
        )
        db.session.add(new_venue)
        db.session.commit()

        db.session.refresh(new_venue)
        flash("Venue " + new_venue.name + " was successfully listed!")

    except BaseException:
        db.session.rollback()
        print(sys.exc_info())
        flash(
            "An error occurred. Venue "
            + new_venue.name
            + " could not be listed."
        )

    finally:
        db.session.close()

    # on successful db insert, flash success
   #flash('Venue ' + request.form['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit
    # could fail.
    try:
        venue_deleted = Venue.query.get(venue_id)
        db.session.delete(venue_deleted)
        db.session.commit()
    except BaseException:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the
    # homepage
    return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    artist = Artist.query.all()
    data = [ar.identity() for ar in artist]

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".

    search_term = request.form.get('search_term', '')
    search_word = Artist.query.filter(
        Artist.name.ilike(
            '%{}%'.format(search_term)))
    list_id = [artist.id for artist in search_word]

    response = {
        "count": len(list_id),
        "data": search_word
    }
    return render_template(
        'pages/search_artists.html',
        results=response,
        search_term=request.form.get(
            'search_term',
            ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using
    # artist_id
    artist = Artist.query.get(artist_id)
    shows = Show.query.filter(
        and_(
            Show.start_time < datetime.now(),
            Show.artist_id == artist_id))
    past_shows = []
    for show in shows:
        venue = Venue.query.get(show.venue_id)
        show_data = {
            "venue_id": venue.id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": str(show.start_time),
        }
        past_shows.append(show_data)
    shows = Show.query.filter(
        and_(
            Show.start_time >= datetime.now(),
            Show.artist_id == artist_id))
    upcoming_shows = []
    for show in shows:
        venue = Venue.query.get(show.venue_id)
        show_data = {
            "venue_id": venue.id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": str(show.start_time),
        }
        upcoming_shows.append(show_data)

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres.split(','),
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows": upcoming_shows,
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    searched_artist = Artist.query.get(artist_id)
    data = {
        "id": searched_artist.id,
        "name": searched_artist.name,
        "genres": searched_artist.genres.split(','),
        "city": searched_artist.city,
        "state": searched_artist.state,
        "phone": searched_artist.phone,
        "website": searched_artist.website,
        "facebook_link": searched_artist.facebook_link,
        "seeking_venue": searched_artist.seeking_venue,
        "seeking_description": searched_artist.seeking_description,
        "image_link": searched_artist.image_link,
    }

    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=data)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    artist_updated = Artist.query.get(artist_id)

    name = request.form.get("name")
    city = request.form.get("city")
    state = request.form.get("state")
    phone = request.form.get("phone")
    genres = request.form.getlist("genres")
    facebook_link = request.form.get("facebook_link")
    website = request.form.get("website_link")
    image_link = request.form.get("image_link")
    seeking_venue = request.form.get("seeking_venue", type=bool)
    seeking_description = request.form.get("seeking_description")

    try:
        artist_updated.name = name
        artist_updated.city = city
        artist_updated.state = state
        artist_updated.phone = phone
        artist_updated.genres = ','.join(genres)
        artist_updated.facebook_link = facebook_link
        artist_updated.website = website
        artist_updated.image_link = image_link
        artist_updated.seeking_venue = seeking_venue
        artist_updated.seeking_description = seeking_description
        db.session.commit()

        flash(request.form.get("name")
              + " artist"
              + " was successfully updated!")
    except BaseException:
        db.session.rollback()
        print(sys.exc_info())
        flash(
            "An error occurred."
            + request.form.get("name")
            + " Artist could not be updated."
        )
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    found_venue = Venue.query.get(venue_id)

    data = {
        "id": found_venue.id,
        "name": found_venue.name,
        "genres": found_venue.genres.split(','),
        "address": found_venue.address,
        "city": found_venue.city,
        "state": found_venue.state,
        "phone": found_venue.phone,
        "website": found_venue.website,
        "facebook_link": found_venue.facebook_link,
        "seeking_talent": found_venue.seeking_talent,
        "seeking_description": found_venue.seeking_description,
        "image_link": found_venue.image_link,
    }

    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=data)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.get(venue_id)

    name = request.form.get("name")
    city = request.form.get("city")
    state = request.form.get("state")
    address = request.form.get("address")
    phone = request.form.get("phone")
    genres = request.form.getlist("genres")
    facebook_link = request.form.get("facebook_link")
    image_link = request.form.get("image_link")
    website_link = request.form.get("website_link")
    seeking_talent = request.form.get('seeking_talent', type=bool)
    seeking_description = request.form.get('seeking_description')

    try:
        venue.name = name
        venue.city = city
        venue.state = state
        venue.address = address
        venue.phone = phone
        venue.genres = ','.join(genres)
        venue.facebook_link = facebook_link
        venue.image_link = image_link
        venue.website_link = website_link
        venue.seeking_talent = seeking_talent
        venue.seeking_description = seeking_description
        db.session.commit()

        flash(request.form.get("name")
              + " venue"
              + " was successfully updated!")

    except BaseException:
        db.session.rollback()
        print(sys.exc_info())
        flash(
            "An error occurred."
            + request.form.get("name")
            + " venue could not be updated."
        )
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    name = request.form.get("name")
    city = request.form.get("city")
    state = request.form.get("state")
    phone = request.form.get("phone")
    genres = request.form.getlist("genres")
    facebook_link = request.form.get("facebook_link")
    website = request.form.get("website_link")
    image_link = request.form.get("image_link")
    seeking_venue = request.form.get("seeking_venue", type=bool)
    seeking_description = request.form.get("seeking_description")

    try:
        new_artist = Artist(
            name=name,
            city=city,
            state=state,
            phone=phone,
            genres=','.join(genres),
            facebook_link=facebook_link,
            website=website,
            image_link=image_link,
            seeking_venue=seeking_venue,
            seeking_description=seeking_description
        )
        db.session.add(new_artist)
        db.session.commit()
        flash(request.form['name'] + ' artist' + ' was successfully listed!')
    except BaseException:
        db.session.rollback()
        print(sys.exc_info())
        flash(
            "An error occurred."
            + request.form.get("name")
            + " artist could not be listed."
        )
    finally:
        db.session.close()

    # on successful db insert, flash success

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be
    # listed.')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    showing_data = Show.query.all()
    all_data = []

    for shows in showing_data:
        venue_id = shows.venue_id
        artist_id = shows.artist_id
        venue = Venue.query.get(venue_id)
        artist = Artist.query.get(artist_id)

        shows_data = {
            "venue_id": venue_id,
            "venue_name": venue.name,
            "artist_id": artist_id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": str(shows.start_time)
        }

        all_data.append(shows_data)

    return render_template('pages/shows.html', shows=all_data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    venue_id = request.form.get('venue_id')
    artist_id = request.form.get('artist_id')
    start_time = request.form.get('start_time')

    try:
        ven = Venue(id=venue_id)
        s = Show(start_time=start_time)
        s.artist = Artist(id=artist_id)
        ven.show.append(s)

        db.session.add(ven)
        db.session.commit()
        flash('Show was successfully listed!')

    except BaseException:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()

    # on successful db insert, flash success

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.debug = True
    app.run(host='127.0.0.1', port=5000)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT',3000))
    app.run(host='0.0.0.0', port=port)
'''
