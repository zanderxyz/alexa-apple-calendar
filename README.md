# alexa-apple-calendar

An example Alexa Skill to read upcoming events from Apple Calendar, written in Python.

## Dependencies

- An [AWS account](https://console.aws.amazon.com/console/home)
- A pre-existing Apple ID with events in the calendar.

## Quick Start

1. Open `lambda_function.py`, fill in your Apple ID username and password at the top and save. If you use 2 factor authentication then you will need to turn it off, as the Apple web service doesn't seem to work with app specific passwords.
1. Zip up the three folders (pytz, requests & tzlocal) and the two .py files (apple_calendar_api.py and lambda_function.py) into a single zip file.
1. Create an [AWS Lambda](https://console.aws.amazon.com/console/home) function
   using your zip file as the code
   - You can follow the [official Amazon
     instructions](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/developing-an-alexa-skill-as-a-lambda-function)
     to give you a hand
   - You *should* uncomment the block in the `lambda_handler` function and
     insert your `applicationId` to only allow requests coming from your
     `applicationId`
   - You can use `test_event.json` as your test template.
   - Consider extending the timeout beyond the default of 3 seconds (I raised mine to 10, which is likely excessive, but may eliminate some sporadic errors)
1. Create a new [Alexa
   Skill](https://developer.amazon.com/edw/home.html#/skill/create) using
   `intent_schema.json` and `sample_utterances.txt`. You can choose your own word for invocation (I use `calendar`).
1. **Don't publish** the skill (because it includes your Apple ID username and password), leave it in development mode
1. Test that it's working from the web interface during the creation of the
   skill
1. Test that it's working with your Echo

## Examples

So far the following commands work:

1. `Alexa ask calendar today` - lists events happening today
1. `Alexa ask calendar tomorrow` - lists events happening tomorrow
1. `Alexa ask calendar Monday` (or any other day) - lists events happening on the next day given
1. `Alexa ask calendar next week` - lists a full week of events starting from next Monday

Note that if you used something other than `calendar` for the invocation word, you must substitute that in the above examples.

## Known Issues

1. Currently you can't add new events as the Apple web service doesn't allow this.
1. Doesn't work if you use 2 Factor Authentication to protect your Apple account.
1. As a consequence of the point above, I receive an email from Apple every single time it runs telling me I have logged into a new computer so I've set my email host to delete all these.

## Acknowledgements

- <https://github.com/n8henrie/alexa-wolfram-alpha> -- A simple skill to query Wolfram Alpha, from which I have cribbed the instructions in this README and some of the boilerplate code.
- <https://github.com/picklepete/pyicloud> -- A Python library for connecting to iCloud, which I stripped down to the basics for our purposes here.
