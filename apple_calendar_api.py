import uuid
import json
import requests
import cookielib
import sys
import os
import tempfile
import six
from re import match
from datetime import datetime, timedelta, date
from calendar import monthrange
import time
from tzlocal import get_localzone

"""
This is a stripped down version of the PyiCloud API from https://github.com/picklepete/pyicloud
All credit to the original authors.
"""

class Session(requests.Session):
    def __init__(self, service):
        self.service = service
        super(Session, self).__init__()

    def request(self, *args, **kwargs):
        response = super(Session, self).request(*args, **kwargs)

        content_type = response.headers.get('Content-Type', '').split(';')[0]
        json_mimetypes = ['application/json', 'text/json']
        if content_type not in json_mimetypes:
            return response

        try:
            json = response.json()
        except:
            return response

        reason = json.get('errorMessage') or json.get('reason')
        if not reason and isinstance(json.get('error'), six.string_types):
            reason = json.get('error')
        if not reason and not response.ok:
            reason = response.reason
        if not reason and json.get('error'):
            reason = "Unknown reason"

        code = json.get('errorCode')

        if reason:
            raise Exception

        return response

class API(object):
    """
    A base authentication class for the iCloud service. Handles the
    authentication required to access iCloud services.

    Usage:
        from pyicloud import API
        api = API('username@apple.com', 'password')
        api.calendar.events(start_date, end_date)
    """
    def __init__(
        self, apple_id, password, cookie_directory=None, verify=True
    ):
        self.data = {}
        self.client_id = str(uuid.uuid1()).upper()
        self.user = {'apple_id': apple_id, 'password': password}

        self._home_endpoint = 'https://www.icloud.com'
        self._setup_endpoint = 'https://setup.icloud.com/setup/ws/1'

        self._base_login_url = '%s/login' % self._setup_endpoint

        self._cookie_directory = os.path.join(
            tempfile.gettempdir(),
            'pyicloud',
        )

        self.session = Session(self)
        self.session.verify = verify
        self.session.headers.update({
            'Origin': self._home_endpoint,
            'Referer': '%s/' % self._home_endpoint,
            'User-Agent': 'Opera/9.52 (X11; Linux i686; U; en)'
        })

        cookiejar_path = self._get_cookiejar_path()
        self.session.cookies = cookielib.LWPCookieJar(filename=cookiejar_path)
        if os.path.exists(cookiejar_path):
            self.session.cookies.load()

        self.params = {
            'clientBuildNumber': '14E45',
            'clientId': self.client_id,
        }

        self.authenticate()

    def authenticate(self):
        """
        Handles authentication, and persists the X-APPLE-WEB-KB cookie so that
        subsequent logins will not cause additional e-mails from Apple.
        """
        data = dict(self.user)

        # We authenticate every time, so "remember me" is not needed
        data.update({'extended_login': False})

        req = self.session.post(
            self._base_login_url,
            params=self.params,
            data=json.dumps(data)
        )

        resp = req.json()
        self.params.update({'dsid': resp['dsInfo']['dsid']})

        if not os.path.exists(self._cookie_directory):
            os.mkdir(self._cookie_directory)
        self.session.cookies.save()
        self.data = resp
        self.webservices = self.data['webservices']

    def _get_cookiejar_path(self):
        # Get path for cookiejar file
        return os.path.join(
            self._cookie_directory,
            ''.join([c for c in self.user.get('apple_id') if match(r'\w', c)])
        )

    @property
    def calendar(self):
        service_root = self.webservices['calendar']['url']
        return CalendarService(service_root, self.session, self.params)

    def __unicode__(self):
        return 'iCloud API: %s' % self.user.get('apple_id')

    def __str__(self):
        as_unicode = self.__unicode__()
        if sys.version_info[0] >= 3:
            return as_unicode
        else:
            return as_unicode.encode('ascii', 'ignore')

    def __repr__(self):
        return '<%s>' % str(self)

class CalendarService(object):
    """
    The 'Calendar' iCloud service, connects to iCloud and returns events.
    """
    def __init__(self, service_root, session, params):
        self.session = session
        self.params = params
        self._service_root = service_root
        self._calendar_endpoint = '%s/ca' % self._service_root
        self._calendar_refresh_url = '%s/events' % self._calendar_endpoint
        self._calendar_event_detail_url = '%s/eventdetail' % (
            self._calendar_endpoint,
        )

    def get_event_detail(self, pguid, guid):
        """
        Fetches a single event's details by specifying a pguid
        (a calendar) and a guid (an event's ID).
        """
        params = dict(self.params)
        params.update({'lang': 'en-us', 'usertz': get_localzone().zone})
        url = '%s/%s/%s' % (self._calendar_event_detail_url, pguid, guid)
        req = self.session.get(url, params=params)
        self.response = req.json()
        return self.response['Event'][0]

    def refresh_client(self, from_dt=None, to_dt=None):
        """
        Refreshes the CalendarService endpoint, ensuring that the
        event data is up-to-date. If no 'from_dt' or 'to_dt' datetimes
        have been given, the range becomes this month.
        """
        today = datetime.today()
        first_day, last_day = monthrange(today.year, today.month)
        if not from_dt:
            from_dt = datetime(today.year, today.month, first_day)
        if not to_dt:
            to_dt = datetime(today.year, today.month, last_day)
        params = dict(self.params)
        params.update({
            'lang': 'en-us',
            'usertz': get_localzone().zone,
            'startDate': from_dt.strftime('%Y-%m-%d'),
            'endDate': to_dt.strftime('%Y-%m-%d')
        })
        req = self.session.get(self._calendar_refresh_url, params=params)
        self.response = req.json()

    def events(self, from_dt=None, to_dt=None):
        """
        Retrieves events for a given date range, by default, this month.
        """
        self.refresh_client(from_dt, to_dt)
        return self.response['Event']

if __name__ == "__main__":
    username = ''
    password = ''
    api = API(username, password)
    query_day = date.today()+timedelta(1)
    events = api.calendar.events(query_day, query_day)
    for e in events:
        print e['startDate'][1:5], e['title'], e['location']
        print e['pGuid']
