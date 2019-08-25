import os
from datetime import datetime
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials
from firebase_admin import firestore

from api_helper import ApiHelper
from constants import *


def init_env():
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)

    assert os.getenv(TIMELOGGY_USER) is not None
    assert os.getenv(TIMELOGGY_FIRESTORE_CONFIG_URL) is not None
    assert os.getenv(TIMELOGGY_FILE_URL) is not None
    assert os.getenv(WAKATIME_SHARE_PATH) is not None
    assert os.getenv(WAKATIME_API_URL) is not None
    assert os.getenv(WAKATIME_COOKIE) is not None
    assert os.getenv(SAVE_MODE) is not None
    assert os.getenv(SAVE_MODE) in ['cloud', 'file']


def init_firestore():
    cred = credentials.Certificate(os.getenv(TIMELOGGY_FIRESTORE_CONFIG_URL))
    firebase_admin.initialize_app(cred)


def sync(data: dict):
    if os.getenv(SAVE_MODE) == 'cloud':
        sync_cloud(data)


def sync_cloud(data: dict):
    time_logs_collection = firestore.client().collection(f'users/{os.getenv(TIMELOGGY_USER)}/timelogs')
    for key, value in data.items():
        print(key, value)
        time_logs_collection.document(key).set(value)

        for project in value['projects']:
            print(f'\t{project}')
            time_logs_collection.document(key).collection('projects').document(project['name']).set(project)


def get_current_data(start=None, end=None):
    time_logs = firestore.client().collection(u'users').document(os.getenv(TIMELOGGY_USER)).collection(u'timelogs')

    if start is not None:
        time_logs = time_logs.where(u'date', u'>=', datetime.strptime(start, '%Y-%m-%d'))

    if end is not None:
        time_logs = time_logs.where(u'date', u'<=', datetime.strptime(end, '%Y-%m-%d'))
    return time_logs


def prettify(time_logs: firestore.firestore.CollectionReference):
    print(f'\nInfo for current user {os.getenv(TIMELOGGY_USER)}')
    for log in time_logs.stream():
        print(f'Spent {log.to_dict()["text"]} on '
              f'{datetime.strftime(datetime.strptime(log.id, "%Y-%m-%d"), "%d.%m.%Y")} doing:')

        projects = sorted(time_logs.document(log.id).collection('projects').stream(),
                          key=lambda x: x.to_dict()['total_seconds'], reverse=True)

        for project in projects:
            print(f'\t{project.to_dict()["name"]} for {project.to_dict()["text"]}')


if __name__ == '__main__':
    init_env()
    init_firestore()

    api_helper = ApiHelper()

    resp_body = api_helper.get_api_data(datetime.today())
    data = api_helper.parse_api_data(resp_body)

    sync(data)
    # prettify(get_current_data())
