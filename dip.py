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
        self.method = 'photos.get'
        self.method_album = 'photos.getAlbums'
        self.method_users = 'users.get'
        self.params_users = 'user_ids'
        self.method_utils = 'utils.resolveScreenName'
        self.params_utils = 'screen_name'
        self.params = 'extended=1&photo_sizes=1&v=5.77'
        self.dict_photo = []

    def set_user_id(self, user_input):
        if user_input.isdigit():
            params = f'user_ids={user_input}&fields=name'
            s_req = f'{self.url}/method/{self.method_users}?{params}&access_token={self.token}&v=5.77'
            res = requests.get(s_req)
            data_user = json.loads(res.text)
            if str(data_user['response'][0]['id']) == user_input:
                self.user_id = data_user['response'][0]['id']
                return True
            else:
                return
        else:
            params = f'screen_name={user_input}'
            s_req = f'{self.url}/method/{self.method_utils}?{params}&access_token={self.token}&v=5.77'
            res = requests.get(s_req)
            data_user = json.loads(res.text)
            if data_user['response']['type'] == 'user':
                self.user_id = data_user['response']['object_id']
                return True
            else:
                return

    def get_photo_info(self, album_id, offset=0, count=10):
        params = f'user_id={self.user_id}&album_id={album_id}&{self.params}&access_token={self.token}' \
                 f'&count={count}&offset={offset}'
        s_req = f'{self.url}/method/{self.method}?{params}'
        res = requests.get(s_req)
        return json.loads(res.text)

    def get_album_info(self):
        params = f'user_id={self.user_id}&{self.params}&access_token={self.token}'
        s_req = f'{self.url}/method/{self.method_album}?{params}'
        res = requests.get(s_req)
        return json.loads(res.text)

    def get_photo(self,  path_to_save, number_photo=5):
        i_off = 0
        i_count = 10
        list_of_photos = []
        data_album = self.get_album_info()
        for album in data_album['response']['items']:
            i_off = 0
            i_count = 10
            album_id = album['id']
            data = self.get_photo_info(album_id, offset=i_off, count=i_count)
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

    def set_dest_path(self,save_path):
        """Метод проверяет наличие папки save_path и, при необходимости создает ее"""
        res = requests.get(f'{self.url}?path=%2F{save_path}&preview_crop=true', headers=self.headers)
        if res.status_code == 404:
            resp = requests.put(f'{self.url}?path=%2F{save_path}', headers=self.headers)
            if resp.status_code == 201:
                return True
            else:
                return False
        elif res.status_code == 200:
            return True

    def upload(self, source_path, save_path, list_photo):
        """Метод загружает файлы по списку list_photo на яндекс диск"""
        replace = True
        for photo in list_photo:
            file_spec = source_path / photo['file_name']
            yd_spec = save_path + '/' + photo['file_name']
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
    vk_user = input('Enter <user_id> or <screen_name> for VK member: ')
    if downloader.set_user_id(vk_user):
        path_dir = Path.cwd() / 'images'
        vk_count_photo = int(input('Enter count of photo saved from VK member albums: '))
        file_list = downloader.get_photo( path_dir, vk_count_photo)
        token_yd = '...'
        uploader = YaUploader(token_yd)
        yd_save_folder = input('Enter YD folder name for saved photo: ')
        if uploader.set_dest_path(yd_save_folder):
            uploader.upload(path_dir, yd_save_folder,file_list)
            print('Done')
        else:
            print(f'Problem with folder for saved photo <{yd_save_folder}>')
    else:
        print(f'Problem with VK member <{vk_user}>')
