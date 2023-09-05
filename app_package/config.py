import os
import json
from dotenv import load_dotenv

load_dotenv()


with open(os.path.join(os.environ.get('CONFIG_PATH'), os.environ.get('CONFIG_FILE_NAME'))) as config_file:
    config_dict = json.load(config_file)


class ConfigBase:

    def __init__(self):

        self.SECRET_KEY = config_dict.get('SECRET_KEY')
        self.PROJECT_ROOT = os.environ.get('PROJECT_ROOT')
        self.DB_ROOT = os.environ.get('DB_ROOT')
        self.DB_NAME = os.environ.get('DB_NAME')
        self.SQL_URI = f"sqlite:///{self.DB_ROOT}{os.environ.get('DB_NAME')}"
        self.SOCIAL_DF_FILE_NAME = 'df_social_activity.pkl'
        self.API_PASSWORD = config_dict.get('API_PASSWORD')
        self.PERSONAL_EMAIL = config_dict.get('PERSONAL_EMAIL')
        self.DOSSIER_FILENAME = config_dict.get('DOSSIER_FILENAME')


class ConfigLocal(ConfigBase):

    def __init__(self):
        super().__init__()

    DEBUG = True
            

class ConfigDev(ConfigBase):

    def __init__(self):
        super().__init__()

    DEBUG = True
            

class ConfigProd(ConfigBase):

    def __init__(self):
        super().__init__()

    DEBUG = False


if os.environ.get('CONFIG_TYPE')=='local':
    config = ConfigLocal()
    print('- whatSticks09web/app_pacakge/config: Local')
elif os.environ.get('CONFIG_TYPE')=='dev':
    config = ConfigDev()
    print('- whatSticks09web/app_pacakge/config: Development')
elif os.environ.get('CONFIG_TYPE')=='prod':
    config = ConfigProd()
    print('- whatSticks09web/app_pacakge/config: Production')

print(f"webpackage location: {os.environ.get('PROJECT_ROOT')}")
print(f"config location: {os.path.join(os.environ.get('CONFIG_PATH'),os.environ.get('CONFIG_FILE_NAME')) }")