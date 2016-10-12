import apple_calendar_api
import datetime
import calendar

# Fill in your Apple ID username and password
username = ''
password = ''

# We can exclude any calendars that we don't want.
# Unfortunately the GUID needs to be given, which you probably won't have to
# hand. GUIDs are of the form 'FCB96618-39A6-4DAC-A3A5-241BAF160C2B'. It is
# possible to get these manually using the API provided - try adding your
# username & password to the apple_calendar_api file, then setting the query_day
# variable to a day that has an event in the calendar you are looking for.
# Run the file and extract the 'pGuid' variable from the event response.
calendars_to_exclude = []

def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)

def get_date(e):
    e = e['startDate']
    return datetime.datetime(e[1], e[2], e[3], e[4], e[5])

def get_date_desc(e):
    d = get_date(e)
    diff = d - datetime.datetime.today()
    if diff > datetime.timedelta(14):
        return d.strftime("%d %B")
    else:
        return calendar.day_name[d.weekday()]

def get_events(query):
    today = datetime.date.today()
    query = query.lower()
    query_day = ""
    if query == "today":
        query_day = today
    elif query == "tomorrow":
        query_day = today + datetime.timedelta(1)
    elif query == "monday":
        query_day = next_weekday(today, 0)
    elif query == "tuesday":
        query_day = next_weekday(today, 1)
    elif query == "wednesday":
        query_day = next_weekday(today, 2)
    elif query == "thursday":
        query_day = next_weekday(today, 3)
    elif query == "friday":
        query_day = next_weekday(today, 4)
    elif query == "saturday":
        query_day = next_weekday(today, 5)
    elif query == "sunday":
        query_day = next_weekday(today, 6)
    elif query == "next week":
        query_start = next_weekday(today, 0)
        query_end = query_start + datetime.timedelta(6)
    elif query == "this week":
        query_start = today
        query_end = next_weekday(today, 6)

    api = apple_calendar_api.API(username, password)
    if query_day != "":
        events = api.calendar.events(query_day, query_day)
    else:
        events = api.calendar.events(query_start, query_end)

    events = [e for e in events if not e['pGuid'] in calendars_to_exclude]
    events.sort(key=lambda x: get_date(x))
    return events

def events_to_nl(events):
    if len(events) == 0:
        return "No events"
    else:
        if events[0]['startDate'][0:3] == events[-1]['startDate'][0:3]:
            day = get_date_desc(events[0])
            if len(events) == 1:
                return "On %s you have %s" % (day,event_to_nl(events[0]))
            else:
                response = "On %s you have %d events. " % (day,len(events))
                for e in events:
                    response += event_to_nl(e)
                return response
        else:
            #multiple days
            response = "You have %d events. " % len(events)
            for e in events:
                response += event_to_nl(e, True)
            return response

def event_to_nl(e, include_day=False):
    time = e['startDate'][4]
    mins = e['startDate'][5]
    if time >= 12:
        if time > 12: time = int(time) - 12
        time = "%d" % time
        if mins > 0: time += " %d " % mins
        time = time + " pm"
    else:
        time = "%d" % time
        if mins > 0: time += " %d " % mins
        time = time + " am"

    location = e['location']
    if location is None:
        response = "%s at %s" % (e['title'], time)
    else:
        response = "%s at %s at %s" % (e['title'], location, time)

    if include_day:
        response += " on %s" % get_date_desc(e)

    response += ". "

    return response.replace("&", "and").replace("!@#$%^*()[]{};:/<>?\|`~-=_+", " ")

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    #if (event['session']['application']['applicationId'] !=
    #        "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #    raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "ac_query":
        return ask_apple_calendar(intent, session)
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here

# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Find out what's on your calendar."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = ("I didn't catch that. Name a day to find out what's on.")
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def ask_apple_calendar(intent, session):
    session_attributes = {}
    should_end_session = True
    reprompt_text = "I didn't catch that. Care to try again?"
    speech_output = "Name a day to find out what's on."

    query = intent['slots']['response'].get('value')
    if query:
        speech_output = events_to_nl(get_events(query))

    return build_response(session_attributes, build_speechlet_response(
        query, speech_output, reprompt_text, should_end_session))


# --------------- Helpers that build all of the responses ----------------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': 'Events on ' + title.title(),
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }
