from server import app, sqldb
import datetime
from .base import cached_route, create_user
from .penndata import din, dinV2
from flask import jsonify, request
from .models import User, DiningPreference
from sqlalchemy import func


@app.route('/dining/v2/venues', methods=['GET'])
def retrieve_venues_v2():
    def get_data():
        return dinV2.venues()['result_data']

    now = datetime.datetime.today()
    daysTillWeek = 6 - now.weekday()
    td = datetime.timedelta(days=daysTillWeek)
    return cached_route('dining:v2:venues', td, get_data)


@app.route('/dining/v2/menu/<venue_id>/<date>', methods=['GET'])
def retrieve_menu_v2(venue_id, date):
    def get_data():
        return dinV2.menu(venue_id, date)['result_data']

    now = datetime.datetime.today()
    daysTillWeek = 6 - now.weekday()
    td = datetime.timedelta(days=daysTillWeek)
    return cached_route('dining:v2:menu:%s:%s' % (venue_id, date), td,
                        get_data)


@app.route('/dining/v2/item/<item_id>', methods=['GET'])
def retrieve_item_v2(item_id):
    def get_data():
        return dinV2.item(item_id)['result_data']

    now = datetime.datetime.today()
    daysTillWeek = 6 - now.weekday()
    td = datetime.timedelta(days=daysTillWeek)
    return cached_route('dining:v2:item:%s' % item_id, td, get_data)


@app.route('/dining/venues', methods=['GET'])
def retrieve_venues():
    def get_data():
        return din.venues()['result_data']

    now = datetime.datetime.today()
    daysTillWeek = 6 - now.weekday()
    td = datetime.timedelta(days=daysTillWeek)
    return cached_route('dining:venues', td, get_data)


@app.route('/dining/hours/<venue_id>', methods=['GET'])
def retrieve_hours(venue_id):
    def get_data():
        return dinV2.hours(venue_id)['result_data']

    now = datetime.datetime.today()
    daysTillWeek = 6 - now.weekday()
    td = datetime.timedelta(days=daysTillWeek)
    return cached_route('dining:v2:hours:%s' % venue_id, td, get_data)


@app.route('/dining/weekly_menu/<venue_id>', methods=['GET'])
def retrieve_weekly_menu(venue_id):
    now = datetime.datetime.today()
    daysTillWeek = 6 - now.weekday()
    td = datetime.timedelta(days=daysTillWeek)

    def get_data():
        menu = din.menu_weekly(venue_id)
        return menu["result_data"]

    return cached_route('dining:venues:weekly:%s' % venue_id, td, get_data)


@app.route('/dining/daily_menu/<venue_id>', methods=['GET'])
def retrieve_daily_menu(venue_id):
    now = datetime.datetime.today()
    end_time = datetime.datetime(now.year, now.month,
                                 now.day) + datetime.timedelta(hours=4)

    def get_data():
        return din.menu_daily(venue_id)["result_data"]

    return cached_route('dining:venues:daily:%s' % venue_id, end_time - now,
                        get_data)


@app.route('/dining/preferences', methods=['POST'])
def save_dining_preferences():
    device_id = request.headers.get('X-Device-ID')

    if not device_id:
        return jsonify({'success': False, 'error': 'No device id passed to server.'})

    user = User.query.filter_by(device_id=device_id).first()

    # check if user exists, create user in db if not
    if not user:
        platform = request.form.get('platform')

        if not platform:
            return jsonify({'success': False, 'error': 'No platform specified.'})

        create_user(platform, device_id, None)

    venue_id = request.form.get('venue_id')

    if not venue_id:
        return jsonify({'success': False, 'error': 'No rooms specified.'})

    dining_preference = DiningPreference(user_id=user.id, venue_id=venue_id)
    sqldb.session.add(dining_preference)
    sqldb.session.commit()

    return jsonify({'success': True, 'error': None})


@app.route('/dining/preferences', methods=['GET'])
def get_dining_preferences():
    device_id = request.headers.get('X-Device-ID')

    if not device_id:
        return jsonify({'error': 'No device id passed to server.'})

    user = User.query.filter_by(device_id=device_id).first()

    if not user:
        return jsonify({'preferences': []})

    preferences = sqldb.session.query(DiningPreference.venue_id, func.count(DiningPreference.venue_id)) \
                               .filter_by(user_id=user.id).group_by(DiningPreference.venue_id).all()
    preference_arr = [{'venue_id': x[0], 'count': x[1]} for x in preferences]
    return jsonify({'preferences': preference_arr})
