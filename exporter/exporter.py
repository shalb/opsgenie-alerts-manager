#!/usr/bin/env python3

import http.server
import traceback
import sys
import time
import json
import urllib.request
import os
import logging
import datetime
import opsgenie_sdk
import schedule
import prometheus_client
import prometheus_client.core


def get_config():
    '''Get configuration from ENV variables'''
   #conf['opsgenie_api_key'] = ''
   #conf['opsgenie_query'] = ''
    conf['scheduler_time'] = '17:00'
    conf['log_level'] = 'INFO'
    env_text_options = ['scheduler_time', 'opsgenie_api_key', 'opsgenie_query', 'log_level']
    for opt in env_text_options:
        opt_val = os.environ.get(opt.upper())
        if opt_val:
            conf[opt] = opt_val
    conf['opsgenie_query_limit'] = 100
    conf['main_loop_sleep_interval'] = 10
    conf['listen_port'] = 9647
    env_int_options = ['opsgenie_query_limit', 'main_loop_sleep_interval', 'listen_port']
    for opt in env_int_options:
        opt_val = os.environ.get(opt.upper())
        if opt_val:
            conf[opt] = int(opt_val)

def configure_logging():
    '''Configure logging module'''
    log = logging.getLogger(__name__)
    log.setLevel(conf['log_level'])
    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(format=FORMAT)
    return log

class Opsgenie:
    '''Object to work with opsgenie'''
    def __init__(self, opsgenie_api_key):
        self.conf = self.conf = opsgenie_sdk.configuration.Configuration()
        self.conf.api_key['Authorization'] = opsgenie_api_key
        self.api_client = opsgenie_sdk.api_client.ApiClient(configuration=self.conf)
        self.alert_api = opsgenie_sdk.AlertApi(api_client=self.api_client)

    def list_alerts(self):
      '''Get alerts with filter'''
      query = conf['opsgenie_query']
      list_response = self.alert_api.list_alerts(limit=conf['opsgenie_query_limit'], query=query)
      return list_response.to_dict()

    def close_alert(self, alert_id):
      '''Close alert by ID'''
      body = opsgenie_sdk.CloseAlertPayload(user='ghastly', note='ghastly was here', source='python sdk')
      close_response = self.alert_api.close_alert(identifier=alert_id, close_alert_payload=body)
      return close_response

def run():
    '''Run whole code'''
    try:
        opsgenie = Opsgenie(conf['opsgenie_api_key'])
        alerts = opsgenie.list_alerts()
        for alert in alerts['data']:
            alert_id = alert['id']
            log.debug('Closing alert with id: "{}"'.format(alert_id))
            opsgenie.close_alert(alert_id)
        opsgenie_alerts_manager_scheduler_last_run_timestamp.set(datetime.datetime.now().timestamp())
        opsgenie_alerts_manager_alerts_count.set(len(alerts['data']))
        opsgenie_alerts_manager_up.set(1)
    except:
        trace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
        for line in trace:
            log.error(line[:-1])
        opsgenie_alerts_manager_up.set(0)
        opsgenie_alerts_manager_errors_total.inc()


conf = dict()
get_config()
log = configure_logging()

opsgenie_alerts_manager_up = prometheus_client.Gauge('opsgenie_alerts_manager_up', 'opsgenie alerts manager scrape status')
opsgenie_alerts_manager_up.set(1)
opsgenie_alerts_manager_errors_total = prometheus_client.Counter('opsgenie_alerts_manager_errors_total', 'opsgenie alerts manager scrape errors total counter')
opsgenie_alerts_manager_scheduler_last_run_timestamp = prometheus_client.Gauge('opsgenie_alerts_manager_scheduler_last_run_timestamp', 'opsgenie alerts manager scheduler job last run timestamp')
opsgenie_alerts_manager_scheduler_last_run_timestamp.set(datetime.datetime.now().timestamp())
opsgenie_alerts_manager_alerts_count = prometheus_client.Gauge('opsgenie_alerts_manager_alerts_count', 'opsgenie alerts manager alerts count')
opsgenie_alerts_manager_alerts_count.set(0)

prometheus_client.start_http_server(conf['listen_port'])

if __name__ != 'main':
    log.debug('Config: "{}"'.format(conf))
    schedule.every().day.at(conf['scheduler_time']).do(run)
    while True:
        try:
            schedule.run_pending()
        except KeyboardInterrupt:
            break
        except:
            trace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
            print(trace)
        time.sleep(conf['main_loop_sleep_interval'])
