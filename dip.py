import json
from math import modf
import requests
from pathlib import Path
import time
import operator


class VKpop:
    def __init__(self, token: str):
        self.token = token
        self.user_id = ''
        self.url = 'https://api.vk.com'
        self.method = 'photos.getAll'
        self.params = 'extended=1&photo_sizes=1&v=5.77'
        self.dict_photo = []

    def get_photo_info(self, offset=0, count=10):
        params = f'user_id={self.user_id}&{self.params}&access_token={self.token}&count={count}&offset={offset}'
        s_req = f'{self.url}/method/{self.method}?{params}'
        res = requests.get(s_req)
        print(res.text)
        return json.loads(res.text)

    def get_photo(self, user_id, path_to_save, number_photo=5):
        self.user_id = user_id
        i_off = 0
        i_count = 10
        list_of_photos = []
        while True:
            data = self.get_photo_info(offset=i_off, count=i_count)
            if not data['response']['items']:
                break
            for files in data['response']['items']:
                photo_params = files['sizes'][-1]
                file_size_type = photo_params['type']
                file_height = int(photo_params['height'])
                file_width = int(photo_params['width'])
                file_url = photo_params['url']
                file_path, *file_params = file_url.split('?')
                file_name = file_path.split('/')[-1]
                file_likes = files['likes']['count']
                print('Read', file_name, file_size_type, file_height, file_width, file_likes)
                time.sleep(0.1)
                if file_likes == 0:
                    time_st, ar = modf((time.time()))
                    new_name = str(int(time_st * 1000000))
                else:
                    new_name = str(file_likes)
                file_name = new_name + '.jpg'
                print(file_name)
                cur_photo = [file_name, file_size_type, file_height * file_width, file_likes, file_url]
                list_of_photos.append(cur_photo)
            i_off += i_count
        list_of_photos.sort(key=operator.itemgetter(2), reverse=True)
        print(list_of_photos[:number_photo])
        print(len(list_of_photos))
        for i in range(number_photo):
            self.dict_photo.append({'file_name': list_of_photos[i][0], 'size': list_of_photos[i][1]})
            api = requests.get(list_of_photos[i][4])
            file_spec = path_to_save / list_of_photos[i][0]
            with open(f'{file_spec}', 'wb') as file:
                file.write(api.content)
            time.sleep(0.1)
        file_spec = path_to_save / 'photo_file.json'
        with open(file_spec, "w") as write_file:
            json.dump(list_of_photos, write_file)
        return self.dict_photo


class YaUploader:
    def __init__(self, token: str):
        self.token = token
        self.url = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.headers = {'Content-Type': 'application/json', 'Accept': 'application/json',
                        'Authorization': f'OAuth {token}'}

    def upload(self, file_path, list_photo):
        """Метод загружает файлы по списку list_photo на яндекс диск"""
        replace = True
        for photo in list_photo:
            file_spec = file_path / photo['file_name']
            yd_spec = photo['file_name']
            res = requests.get(f'{self.url}/upload?path={yd_spec}&overwrite={replace}', headers=self.headers).json()
            with open(file_spec, 'rb') as f:
                try:
                    print('Write:', yd_spec)
                    requests.put(res['href'], files={'file': f})
                except KeyError:
                    print(res)


if __name__ == '__main__':
    token_vk = '...'
    downloader = VKpop(token_vk)
    vk_user = '670053379'
    path_dir = Path.cwd() / 'images'
    file_list = downloader.get_photo(vk_user, path_dir)
    token_yd = '...'
    uploader = YaUploader(token_yd)
    uploader.upload(path_dir, file_list)
