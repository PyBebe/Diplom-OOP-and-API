from urllib.parse import urlencode
import requests
import json
import logging


def get_vk_token():
    app_id = '51763415'
    oauth_base_url = 'https://oauth.vk.com/authorize'
    params = {
        'client_id':app_id,
        'redirect_url':'https://oauth.vk.com/blank.html',
        'display':'page',
        'scope':'photos',
        'response_type':'token'
        }
    oauth_url = f'{oauth_base_url}?{urlencode(params)}'
    return oauth_url


class BackupClient:
    vk_api_base_url = 'https://api.vk.com/method'
    yac_api_base_url = 'https://cloud-api.yandex.net'
    folder_name = 'VK_Backup'

    def __init__(self, vk_token, vk_user_id, yac_token):
        self.vk_token = vk_token
        self.vk_user_id = vk_user_id
        self.yac_token = yac_token

    def get_common_vk_params(self):
        return {'access_token':self.vk_token, 'v':'5.131'}

    def get_vk_profile_photos(self):
        params = self.get_common_vk_params()
        params.update({
            'owner_id':self.vk_user_id,
            'album_id':'profile',
            'rev':1,
            'extended':1,
            'photo_sizes':1
            })
        response = requests.get(f'{self.vk_api_base_url}/photos.get', params=params)
        return response.json().get('response', {}).get('items')

    def download_photos(self):
        photo_names = []
        saved_photos = []
        for i in range(5):
            photo_info = self.get_vk_profile_photos()[i]
            photo_sizes = photo_info['sizes']
            sorted_photos = sorted(photo_sizes, key=lambda x:x['height'], reverse=True)
            max_photo_url = sorted_photos[0]['url']
            photo_type = sorted_photos[0]['type']
            likes = photo_info['likes']['count']
            date = photo_info['date']
            photo_name = f'{likes}.jpg'
            if photo_name not in photo_names:
                photo_names.append(photo_name)
            else:
                photo_name = f'{likes}-{date}.jpg'
                photo_names.append(photo_name)
            saved_photos.append({'file_name':photo_name, 'size':photo_type})
            response = requests.get(max_photo_url)
            with open(photo_name, 'wb') as f:
                f.write(response.content)
        return saved_photos

    def get_common_yac_headers(self):
        return {'Authorization':self.yac_token}

    def create_yac_folder(self):
        headers = self.get_common_yac_headers()
        url_for_creating_folder = self.yac_api_base_url + '/v1/disk/resources'
        params = {'path':self.folder_name}
        response = requests.put(url_for_creating_folder, headers=headers, params=params)

    def upload_photos(self):
        saved_photos = self.download_photos()
        headers = self.get_common_yac_headers()
        url_for_link = self.yac_api_base_url + '/v1/disk/resources/upload'
        for photo in saved_photos:
            params = {'path':f'{self.folder_name}/{photo["file_name"]}'}
            response = requests.get(url_for_link, headers=headers, params=params)
            url_for_upload = response.json().get("href", "")
            with open(photo['file_name'], 'rb') as f:
                response = requests.post(url_for_upload, files={'file':f})
        with open('result.json', 'w') as f:
            json.dump(saved_photos, f, ensure_ascii=False, indent=4)
        result_link = f'https://disk.yandex.ru/client/disk/{self.folder_name}'
        result = f'Спасибо за использование нашего приложения!\nНа Ваше устройство загружен файл result.json с данными о сохраненных фотографиях.\nВаши фото Вы найдете здесь - {result_link}.\nПриятного просмотра!'
        return result


logging.basicConfig(
    level=logging.DEBUG,
    filename='mylog.log',
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
logging.info('Запуск логирования')


print('''Добро пожаловать в приложение для резервного копирования фотографий VK BackUp!

Чтобы продолжить, Вам необходимо предоставить приложению доступ к Вашим фотографиям через VK ID.

1. Перейдите по ссылке ниже и подтвердите права приложения.
2. Скопируйте токен из адреса открывшейся страницы Вашего браузера (после фразы access_token= до фразы &expires_in).
''')
print(get_vk_token())
print()
vk_token = input('Введите Ваш VK токен: ')
print()
vk_user_id = input('Введите Ваш ID пользователя VK: ')
print()
yac_token = input('Введите Ваш Яндекс OAuth-токен: ')
print()
test_client = BackupClient(vk_token, vk_user_id, yac_token)
test_client.create_yac_folder()
print(test_client.upload_photos())
