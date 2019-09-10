import os
from datetime import datetime, timedelta
import requests
from constants import *


class ApiHelper:

    def __init__(self):
        self.api_url = os.getenv(WAKATIME_API_URL)
        self.share_url = os.getenv(WAKATIME_SHARE_PATH)
        self.cookie = os.getenv(WAKATIME_COOKIE)
        pass

    def get_api_data(self, end_date, days=14):
        start_date = end_date - timedelta(days=days)

        url = f"{self.api_url}/users/current/summaries?" \
            f"start={start_date.strftime('%Y-%m-%d')}&" \
            f"end={end_date.strftime('%Y-%m-%d')}"

        print(f'## sending request to {url}')
        response = requests.get(url, headers={'cookie': self.cookie})
        return ApiHelper.handle_response(response, url)

    def get_share_data(self):
        print(f'## sending request to {self.share_url}')
        response = requests.get(self.share_url)
        return ApiHelper.handle_response(response, self.share_url)

    @staticmethod
    def handle_response(response, url):
        if response.status_code != 200:
            raise Exception(f'Response from {url} is {response.status_code}\nCause {response.content}')
        return response.json()

    @staticmethod
    def parse_api_data(response: dict):
        print('## parsing API data')
        data = ApiHelper.get_data(response)
        data = filter(lambda x: len(x['categories']) > 0, data)
        time_logs = {datum['range']['date']: {
            'date': ApiHelper.to_date(datum['range']['date']),  # date
            'text': datum['categories'][0]['text'],  # string
            'total_seconds': datum['categories'][0]['total_seconds'],  # number
            'projects': [{
                'name': project['name'],
                'text': project['text'],
                'total_seconds': project['total_seconds']
            } for project in datum['projects']]
        } for datum in data}

        return time_logs

    @staticmethod
    def parse_share_data(response: dict):
        print('Parsing share data')
        data = ApiHelper.get_data(response)

        return {datum['range']['date']: {
            'date': ApiHelper.to_date(datum['range']['date'], '%Y-%m-%d'),  # date
            'text': datum['grand_total']['text'],  # string
            'total_seconds': datum['grand_total']['total_seconds']  # number
        } for datum in data}

    @staticmethod
    def get_data(response):
        data = response['data']
        if not data:
            raise Exception('No data is present in the response')
        return data

    @staticmethod
    def to_date(date: str, format='%Y-%m-%dT%H:%M:%SZ'):
        if len(date) <= 10:
            format = '%Y-%m-%d'
        return datetime.strptime(date, format)
