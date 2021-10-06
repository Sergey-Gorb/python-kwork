import json
from math import modf
import requests
from pathlib import Path
import time
import operator


def getintinput(msg, min_int, max_int, def_int=5):
    while True:
        inp = input(msg)
        if inp:
            try:
                int_inp = int(inp)
                if int_inp < min_int or int_inp > max_int:
                    print(f'Value {int_inp} out margin!')
                else:
                    return int_inp
            except ValueError:
                print('Bad value', inp)
        else:
            return def_int
        print('Try again!')


class VKpop:
    def __init__(self, token: str):
        self.token = token
        self.owner_id = ''
        self.url = 'https://api.vk.com'
        self.method = 'photos.get'
        self.album_id = 'profile'
        self.method_album = 'photos.getAlbums'
        self.method_users = 'users.get'
        self.params_users = 'user_ids'
        self.method_utils = 'utils.resolveScreenName'
        self.params_utils = 'screen_name'
        self.params = 'extended=1&photo_sizes=1&v=5.130'
        self.dict_photo = []

    def set_owner_id(self, user_input):
        if user_input.isdigit():
            params = f'user_ids={user_input}&fields=name'
            s_req = f'{self.url}/method/{self.method_users}?{params}&access_token={self.token}&v=5.130'
            res = requests.get(s_req)
            data_user = json.loads(res.text)
            # print(res)
            # print(data_user)
            if str(data_user['response'][0]['id']) == user_input:
                self.owner_id = data_user['response'][0]['id']
                return True
            else:
                return
        else:
            params = f'screen_name={user_input}'
            s_req = f'{self.url}/method/{self.method_utils}?{params}&access_token={self.token}&v=5.130'
            res = requests.get(s_req)
            data_user = json.loads(res.text)
            if data_user['response']['type'] == 'user':
                self.owner_id = data_user['response']['object_id']
                return True
            else:
                return

    def get_photo_info(self, offset=0, count=10):
        params = f'owner_id={self.owner_id}&album_id={self.album_id}&{self.params}&access_token={self.token}' \
                 f'&count={count}&offset={offset}'
        s_req = f'{self.url}/method/{self.method}?{params}'
        res = requests.get(s_req)
        return json.loads(res.text)

    def get_photo(self, path_to_save):
        i_off = 0
        i_count = 10
        list_of_photos = []
        while True:
            data = self.get_photo_info(offset=i_off, count=i_count)
            if 'error' in data.keys():
                print(f"Error: {data['error']['error_msg']} [owner_id] = {self.owner_id}")
                return None
            elif 'response' in data.keys():
                j_count = 0
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
                    j_count += 1
                if j_count == 0:
                    break
            i_off += j_count
        if len(list_of_photos):
            list_of_photos.sort(key=operator.itemgetter(2), reverse=True)
            print(f'Collect information about {len(list_of_photos)} photos')
            que = f'How many biggest photos wish you save in YD [5]?: '
            number_photo = getintinput(que, 0, len(list_of_photos))
            if number_photo:
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
            else:
                return None
        else:
            return None


class YaUploader:
    def __init__(self, token: str):
        self.token = token
        self.url = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.headers = {'Content-Type': 'application/json', 'Accept': 'application/json',
                        'Authorization': f'OAuth {token}'}

    def set_dest_path(self, save_path):
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
    token_vk = '2ed4994139addec3f51843643fe25f35b8251b197bef321c715a18ce998c5b61f6e1c859cc10ec2f9c7dd'
    downloader = VKpop(token_vk)
    vk_user = input('Enter <owner_id> or <screen_name> for VK member: ')
    if downloader.set_owner_id(vk_user):
        path_dir = Path.cwd() / 'images'
        file_list = downloader.get_photo(path_dir)
        if file_list:
            token_yd = '...'
            uploader = YaUploader(token_yd)
            yd_save_folder = input('Enter YD folder name for saved photo: ')
            if uploader.set_dest_path(yd_save_folder):
                uploader.upload(path_dir, yd_save_folder, file_list)
                print('Done')
            else:
                print(f'Problem with folder for saved photo <{yd_save_folder}>')
        else:
            print('User canceled operation or list of photos is empty')
    else:
        print(f'Problem with VK member <{vk_user}>')
