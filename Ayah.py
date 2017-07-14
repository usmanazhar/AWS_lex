"""
This is an implementation of the Lex Code Hook Interface
in order to serve the  ShaykhBot to get the ayah requested.
"""
import math
import dateutil.parser
import datetime
import time
import os
import logging

import requests

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


""" --- TODO: Remove this function --- """
def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


def validate_get_ayah(ayah_number):

    return build_validation_result(True, None, None)


""" --- Functions that control the bot's behavior --- """


def get_ayah(intent_request):
    """
    Performs dialog management and fulfillment for getting ayah.
    Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action
    in slot validation and re-prompting.
    """

    ayah_number = get_slots(intent_request)["Ayah"]
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)

        validation_result = validate_get_ayah(ayah_number)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

        # Pass the price of the flowers back through session attributes to be used in various prompts defined
        # on the bot model.
        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

    # Order the flowers, and rely on the goodbye message of the bot to define the message to the end user.
    # In a real bot, this would likely involve a call to a backend service.

    url = 'http://api.alquran.cloud/ayah/'+ayah_number+'/editions/en.sahih'
    logger.debug("request url..{}".format(url))
    response = requests.get(url)
    resp_data = response.json()
    resp_dict = dict(resp_data['data'][0])
    resp_text = resp_dict['text']
    logger.debug(resp_dict['text'])
    logger.debug("Response... {}".format(resp_data))
    #response ="this is a test response"
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': resp_text})


""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'TestOne':
        return get_ayah(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)

