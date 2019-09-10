import os
from pathlib import Path
from datetime import date, datetime, timedelta

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials
from firebase_admin import firestore

from api_helper import ApiHelper
from constants import *


def init_env():
    print('Setting up environment...')
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
    print('Initializing firestore...')
    cred = credentials.Certificate(os.getenv(TIMELOGGY_FIRESTORE_CONFIG_URL))
    firebase_admin.initialize_app(cred)


def sync(data: dict):
    if os.getenv(SAVE_MODE) == 'cloud':
        sync_cloud(data)


def sync_cloud(data: dict):
    print('## syncing to firestore')
    db = firestore.client()
    batch = db.batch()

    time_logs_collection = db.collection(f'users/{os.getenv(TIMELOGGY_USER)}/timelogs')
    for key, value in data.items():
        print(key, value)
        batch.set(time_logs_collection.document(key), value)

        for project in value['projects']:
            print(f'\t{project}')
            batch.set(time_logs_collection.document(key).collection('projects').document(project['name']), project)

    batch.commit()


def get_current_data(start=None, end=None):
    time_logs = firestore.client().collection(u'users').document(os.getenv(TIMELOGGY_USER)).collection(u'timelogs')

    if start is not None:
        time_logs = time_logs.where(u'date', u'>=', datetime.strptime(start, '%Y-%m-%d'))

    if end is not None:
        time_logs = time_logs.where(u'date', u'<=', datetime.strptime(end, '%Y-%m-%d'))
    return time_logs


def prettify(time_logs: firestore.firestore.CollectionReference):
    print(f'Info for current user {os.getenv(TIMELOGGY_USER)}')
    for log in time_logs.stream():
        day = log.to_dict()

        print(f'\nSpent {day["text"]} on '
              f'{datetime.strftime(datetime.strptime(log.id, "%Y-%m-%d"), "%d.%m.%Y")} doing:')

        projects = day['projects'] if 'projects' in day else []
        sorted_projects = sorted(projects, key=lambda x: x['total_seconds'], reverse=True)

        for project in sorted_projects:
            print(f'\t- {project["name"]} for {project["text"]}')


if __name__ == '__main__':
    init_env()
    init_firestore()

    print()
    api_helper = ApiHelper()
    resp_body = api_helper.get_api_data(datetime.today())
    data = api_helper.parse_api_data(resp_body)

    print()
    sync(data)

    print()
    start = date.today() - timedelta(days=7)
    prettify(get_current_data(start.isoformat()))
