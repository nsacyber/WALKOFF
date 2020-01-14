import conf
import log
import sys
import os
import yaml
import datetime
import time
import signal
import docker


def shutdown(_signo, _stack_frame):
    logger.info('Recieved {}, shutting down'.format(_signo))
    sys.exit(0)


def sendAlert(event, timestamp):
    ''' Check which integrations are enabled and send alerts '''
    logger.info('Alert triggered: {},{},{}'.format(event['Type'], event['Action'], event['Actor']['ID']))
    if 'slack' in config['integrations']:
        if config['integrations']['slack']['enabled']:
            import slack
            slack.alert(event, config, thisHost, timestamp)
    if 'sparkpost' in config['integrations']:
        if config['integrations']['sparkpost']['enabled']:
            import sparkpost
            sparkpost.alert(event, config, thisHost, timestamp)
    if 'discord' in config['integrations']:
        if config['integrations']['discord']['enabled']:
            import discord
            discord.alert(event, config, thisHost, timestamp)
    if 'apirequest' in config['integrations']:
        if config['integrations']['apirequest']['enabled']:
            import apirequest
            apirequest.alert(event, config, thisHost, timestamp)


def main():
    ''' Look for any event on the event stream that matches the defined event types  '''
    for event in stream:
        logger.debug('Event: {}'.format(event))
        eventType = event['Type']
        eventAction = event['Action']
        timestamp = datetime.datetime.fromtimestamp(event['time']).strftime('%c')

        if eventType in config['events']:
            if eventAction in config['events'][eventType]:
                try:

                    if 'name' in event['Actor']['Attributes']:
                        eventActorName = event['Actor']['Attributes']['name']
                    else:
                        # No name available, use ID instead
                        eventActorName = event['Actor']['ID']

                    if 'exclusions' in config['settings'] and eventActorName in config['settings']['exclusions']:
                        logger.info('Excluded Event: {}'.format(event))
                    else:
                        if 'inclusions' not in config['settings']:
                            sendAlert(event, timestamp)
                        elif eventActorName in config['settings']['inclusions']:
                            sendAlert(event, timestamp)
                        else:
                            logger.info(
                                'Excluded Event: {}, actor {} not in inclusion list'.format(event, eventActorName))
                except:
                    sendAlert(event, timestamp)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    logger = log.load()
    config = conf.load()
    try:
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        stream = client.events(decode=True)
        thisHost = client.info()['Name']
    except:
        logger.info('Failed to connect to Docker event stream')
        shutdown()

    logger.info('Starting up')
    main()