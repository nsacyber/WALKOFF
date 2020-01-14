import requests
import time
import json
import logging


def alert(event, config, thisHost, timestamp):
    logger = logging.getLogger('main')
    key = config['integrations']['apirequest']['key']

    logger.info(f"I'm executing something in here, also this is my message: {key}")
    # key = config['integrations']['sparkpost']['key']
    # msgFrom = config['integrations']['sparkpost']['from']
    # msgSubject = config['integrations']['sparkpost']['subject']
    # msgRecipients = []
    # for recipient in config['integrations']['sparkpost']['recipients']:
    #   recipientObj = {'address': recipient}
    #   msgRecipients.append(recipientObj)

    # msgBody = "Host: {}\nType: {}\nTime: {}\nAction: {}\nID: {}".format(thisHost,event['Type'],timestamp,event['Action'],event['Actor']['ID'])

    # ## Append name to payload if exists
    # if 'name' in event['Actor']['Attributes']:
    #   msgBody += "\nName: {}".format(event['Actor']['Attributes']['name'])

    # ## Append tags to payload if exists
    # if 'tags' in config['settings']:
    #   tags = ", ".join([str(x) for x in config['settings']['tags']])
    #   msgBody += "\nTags: {}".format(tags)

    # ## Define payload
    # payload = {
    #   "options": {
    #     "sandbox": False
    #   },
    #   "content": {
    #     "from": msgFrom,
    #     "subject": msgSubject,
    #     "text": msgBody
    #   },
    #   "recipients": msgRecipients
    # }

    # ## Perform request
    # try:
    #   requests.post(
    #     config['integrations']['sparkpost']['url'],
    #     data = json.dumps(payload),
    #     headers = {
    #       'Content-Type': 'application/json',
    #       'Authorization': key
    #       }
    #     )

    # except requests.exceptions.RequestException as e:
    #   logger.error('{}: {}'.format(__name__,e))