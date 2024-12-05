import random
import time
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import msal
import json, requests
import logging
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

from colorlog import ColoredFormatter
import colorlog
import logging

def initialize_logging(level):
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    handler = colorlog.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger('demo')
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger

class APIClient:
    def __init__(self, dotenv_path=None, log_level=logging.ERROR):
        self.logger = initialize_logging(log_level)
        self._load_env_vars(dotenv_path)
        self.access_token_cache = None
        self.token_expiry_time = 0
        self.client = AzureOpenAI(
            azure_endpoint=self.apim_resource_gateway_url, 
            api_key=self.apim_subscription_key, 
            api_version=self.openai_api_version
        )

    def _load_env_vars(self, dotenv_path):

        load_dotenv(dotenv_path=dotenv_path or os.path.join(os.path.dirname(__file__), '.env'))
        
        self.apim_base_url = os.getenv('APIM_BASE_URL')
        self.apim_api = os.getenv('APIM_API')
        self.apim_subscription_key = os.getenv('APIM_SUBSCRIPTION_KEY')
        self.openai_api_version = os.getenv('OPENAI_API_VERSION')
        self.openai_model_name = os.getenv('OPENAI_MODEL_NAME')
        self.openai_deployment_name = os.getenv('OPENAI_DEPLOYMENT_NAME')
        self.frontend_client_id = os.getenv('CLIENT_ID')
        self.tenant_id = os.getenv('TENANT_ID')
        
        missing_vars = []
        required_vars = {
            'APIM_BASE_URL': self.apim_base_url,
            'APIM_API': self.apim_api,
            'APIM_SUBSCRIPTION_KEY': self.apim_subscription_key,
            'OPENAI_API_VERSION': self.openai_api_version,
            'OPENAI_MODEL_NAME': self.openai_model_name,
            'OPENAI_DEPLOYMENT_NAME': self.openai_deployment_name,
            'CLIENT_ID': self.frontend_client_id,
            'TENANT_ID': self.tenant_id
        }

        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")
        
        self.apim_resource_gateway_url = f"{self.apim_base_url}/{self.apim_api}"

    def get_access_token(self):
        
        if self.access_token_cache and time.time() < self.token_expiry_time:
            return self.access_token_cache

        app = msal.PublicClientApplication(self.frontend_client_id, authority=f"https://login.microsoftonline.com/{self.tenant_id}")
        flow = app.initiate_device_flow(scopes=["User.Read"])
        if "user_code" not in flow:
            raise ValueError("Failed to create device flow. Error: %s" % json.dumps(flow, indent=2))

        print(flow["message"])
        result = app.acquire_token_by_device_flow(flow)
        if "access_token" in result:
            self.access_token_cache = result['access_token']
            self.token_expiry_time = time.time() + result['expires_in'] - 60  # Subtract 60 seconds for buffer
            graph_data = requests.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={'Authorization': 'Bearer ' + self.access_token_cache},
            ).json()
            self.logger.info("Graph API call result: %s" % json.dumps(graph_data, indent=2))
        else:
            return None

        return self.access_token_cache

    def run_queries(self, questions, runs=5, randomize=True):
        self.logger.info(f"Running {runs} queries")
        access_token = self.get_access_token()
        api_runs = []

        for i in range(runs):
            if randomize:
                random_question = random.choice(questions)
            else:
                random_question = questions[i % len(questions)]
            messages = [
                {"role": "system", "content": "You are a sarcastic unhelpful assistant."},
                {"role": "user", "content": random_question}
            ]
            region = ""
            start_time = time.time()
            try:
                raw_response = self.client.chat.completions.with_raw_response.create(
                    model=self.openai_model_name, 
                    messages=messages, 
                    extra_headers={"Authorization": "Bearer " + access_token}
                )
                response = raw_response.parse()
                headers = raw_response.headers
                response_time = time.time() - start_time

                remaining_tokens = headers.get('x-ratelimit-remaining-tokens')
                remaining_requests = headers.get('x-ratelimit-remaining-requests')
                region = headers.get('x-ms-region')

                logging.debug(f"Response: {response}")
                logging.debug(f"\n\tRemaining Tokens: {remaining_tokens} \n\tRemaining Requests: {remaining_requests}\n\tRegion: {region}")
                logging.debug(f"\tResponse Time: {response_time:.2f} seconds")

            except Exception as e:
                if 'Azure AI Content Safety service' in str(e):
                    print(f"\n❌ Content Filtered: {e}\n\tInitial Question: {random_question}\n")
                else:
                    print(f"Error during API call: {e}")
                continue

            response_time = time.time() - start_time
            print("\n\n▶️ Run: ", i+1, f"duration: {response_time:.2f} seconds")
            if remaining_tokens:
                print("\t[AOAI Model] x-ratelimit-remaining-tokens:", '\x1b[1;31m'+remaining_tokens+'\x1b[0m')
            if remaining_requests:
                print("\t[AOAI Model] x-ratelimit-remaining-requests:", '\x1b[1;31m'+remaining_requests+'\x1b[0m')
            if region:
                print("\t[AOAI Model] x-ms-region:", '\x1b[1;31m'+region+'\x1b[0m')
            if headers.get('remaining-tokens'):
                print("\t[API Policy] remaining-tokens:", '\x1b[1;31m'+headers.get('remaining-tokens')+'\x1b[0m')
            if headers.get('consumed-tokens'):
                print("\t[API Policy] consumed-tokens:", '\x1b[1;31m'+headers.get('consumed-tokens')+'\x1b[0m')
            print("💬 ", random_question, response.choices[0].message.content)

            api_runs.append((response_time, region))

        return api_runs

    def plot_results(self, api_runs, title='Semantic Caching Performance'):
        mpl.rcParams['figure.figsize'] = [15, 5]
        df = pd.DataFrame(api_runs, columns=['Response Time'])
        df['Run'] = range(1, len(df) + 1)
        df.plot(kind='bar', x='Run', y='Response Time', legend=False)
        plt.title(title)
        plt.xlabel('Runs')
        plt.ylabel('Response Time (s)')
        plt.xticks(df['Run'], rotation=0)

        average = df['Response Time'].mean()
        plt.axhline(y=average, color='r', linestyle='--', label=f'Average: {average:.2f}')
        plt.legend()

        plt.show()

    def plot_load_balancing_results(self, api_runs, color_map=None, title='Load Balancing results'):
        if color_map is None:
            color_map = {
                'East US': 'blue',
                'North Central US': 'green',
                'West US': 'red',
            }
        mpl.rcParams['figure.figsize'] = [15, 7]
        df = pd.DataFrame(api_runs, columns=['Response Time', 'Region'])
        df['Run'] = range(1, len(df) + 1)

        ax = df.plot(kind='bar', x='Run', y='Response Time', color=[color_map.get(region, 'gray') for region in df['Region']], legend=False)

        legend_labels = [plt.Rectangle((0, 0), 1, 1, color=color_map.get(region, 'gray')) for region in df['Region'].unique()]
        ax.legend(legend_labels, df['Region'].unique())

        plt.title(title)
        plt.xlabel('Runs')
        plt.ylabel('Response Time')
        plt.xticks(df['Run'], rotation=0)

        average = df['Response Time'].mean()
        plt.axhline(y=average, color='r', linestyle='--', label=f'Average: {average:.2f}')

        plt.show()
