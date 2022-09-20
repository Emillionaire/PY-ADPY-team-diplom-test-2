import requests
import db_application


# get user info
def get_user_info(**kwargs):
    params = {
        'fields': 'bdate, city, sex',
        'user_ids': kwargs['user_id'],
        'access_token': kwargs['VK_user_token'],
        'v': '5.89'
    }

    result = requests.get(kwargs['URL_get'], params=params).json()

    if 'city' in result['response'][0].keys():
        city = result['response'][0]['city']
    else:
        city = 1
    if 'bdate' in result['response'][0].keys():
        bdate = result['response'][0]['bdate'].split('.')[2]
    else:
        bdate = 2000

    result_dict = {
        'id_vk': result['response'][0]['id'],
        'first_name': result['response'][0]['first_name'],
        'last_name': result['response'][0]['last_name'],
        'city': city,
        'bdate': bdate,
        'sex': result['response'][0]['sex']
    }
    return result_dict


# get match person
def get_match_persons(conn, **kwargs):
    user_id = kwargs['user_id']
    result = db_application.take_user_info(conn, user_id)
    id_vk = result[1]
    first_name = result[2]
    last_name = result[3]
    city = result[4]
    bdate = result[5]
    sex = result[6]

    if sex == 1:
        target_sex = 2
    else:
        target_sex = 1

    params = {
        'sort': 0,
        'count': 1000,
        'city': city,
        'sex': target_sex,
        'birth_year': bdate,
        'has_photo': 1,
        'access_token': kwargs['VK_user_token'],
        'v': '5.89',
        'fields': 'city, bdate, sex'
    }

    result = requests.get(kwargs['URL_search'], params=params).json()

    match_list = []
    for person in result['response']['items']:
        if 'city' in person.keys() and 'bdate' in person.keys() and 'sex' in person.keys():
            if person['city']['id'] == city and int(person['bdate'].split('.')[2]) == bdate and person[
                'sex'] == target_sex:
                match_list.append(person)

    db_application.add_match_persons(conn, user_id, match_list)


# get match person info
def get_match_info(conn, person_id, VK_user_token, URL_get):
    params = {
        'fields': 'bdate, city, sex',
        'user_ids': person_id,
        'access_token': VK_user_token,
        'v': '5.89'
    }

    result = requests.get(URL_get, params=params).json()
    return result


# get favorite person info
def get_favorite_info(id_vk_user, VK_user_token, URL_get):
    params = {
        'fields': 'bdate, city, sex',
        'user_ids': id_vk_user,
        'access_token': VK_user_token,
        'v': '5.89'
    }

    result = requests.get(URL_get, params=params).json()
    return result


# get best photo of person
def get_photos(id_vk_match_person, VK_user_token, URL_get_photo):
    params = {
        'user_ids': id_vk_match_person,
        'access_token': VK_user_token,
        'v': '5.89',
        'owner_id': id_vk_match_person,
        'album_id': 'profile',
        'extended': '1',
        'count': '999',
    }
    result = requests.get(URL_get_photo, params=params)
    if 'response' in result.json():
        photo_dict = {}
        photo_list = []
        result = result.json()['response']['items']
        for photos in result:
            like = photos['likes']['count']
            for photo in photos['sizes']:
                photo['likes'] = like
                photo['id'] = photos['id']
                photo['owner_id'] = photos['owner_id']
                f_photo = {key: photo[key] for key in photo if key not in ['height', 'width']}
                photo_dict = {**photo_dict, **f_photo}
            photo_list.append([*photo_dict.values()])
            photo_list.sort(key=lambda i: i[2], reverse=True)
        return photo_list
    else:
        return None


# get id city using text name city
def get_city(city, VK_user_token, URL_get_city):
    params = {
        'q': city,
        'v': '5.89',
        'access_token': VK_user_token,
        'count': 1,
        'country_id': 1
    }
    result = requests.get(URL_get_city, params=params)
    return result
