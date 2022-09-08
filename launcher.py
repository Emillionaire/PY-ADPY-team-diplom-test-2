import configparser
import random
from random import randrange

import psycopg2
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType

import db_application
import vk_application

if __name__ == '__main__':
    # SETTINGS
    # read settings file
    path_to_settings = 'settings.ini'
    settings = configparser.ConfigParser()
    settings.read(path_to_settings)

    # db block
    database = settings.get('DB', 'database')
    user = settings.get('DB', 'user')
    password = settings.get('DB', 'password')
    port = settings.get('DB', 'port')
    host = settings.get('DB', 'host')
    reset_db = settings.get('DB', 'reset_db')

    # VK token block
    VK_user_token = settings.get('VK_tokens', 'VK_user_token')
    VK_group_token = settings.get('VK_tokens', 'VK_group_token')

    # VK API block
    URL_get = settings.get('VK_API', 'URL_get')
    URL_search = settings.get('VK_API', 'URL_search')
    URL_get_photo = settings.get('VK_API', 'URL_get_photo')
    URL_get_city = settings.get('VK_API', 'URL_get_city')

    # DB
    # connection parameters
    conn = psycopg2.connect(database=database, user=user, password=password, port=port, host=host)

    # db cleaner
    if reset_db == '1':
        db_application.reset_db(conn)

    # db creator
    db_application.create_db(conn)

    # VK BOT
    # start bot
    vk = vk_api.VkApi(token=VK_group_token)
    longpoll = VkLongPoll(vk)
    count = 0
    want_change_year = 0
    want_change_city = 0


    def write_msg(user_id, message):
        vk.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7), })


    def write_msg_att(user_id, message, att):
        vk.method('messages.send',
                  {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7), 'attachment': att})


    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                request = event.text
                if request == 'привет':
                    write_msg(event.user_id,
                              'Привет, пользователь! Если хочешь начать поиск знакомств - напиши "начать".')
                elif request == 'начать':
                    check = db_application.check_user_in_db(conn, event.user_id)
                    if check is not None:
                        write_msg(event.user_id, 'Сейчас я внесу тебя в свою базу данных!')
                        user_info = vk_application.get_user_info(user_id=event.user_id, VK_user_token=VK_user_token,
                                                                 URL_get=URL_get)
                        if user_info['city'] == 1:
                            write_msg(event.user_id,
                                      'Я не смог определить твой город, извини. Буду искать, будто ты живешь в Москве. Если ты хочешь изменить свой город - напиши "изменить город"!')
                        if user_info['bdate'] == 0:
                            write_msg(event.user_id,
                                      'Я не смог определить твой год рождения, извини. Буду считать, будто ты родился в 2000 году. Если ты хочешь изменить год рождения - напиши "изменить год"!')
                        db_application.add_new_user(conn, user_info)
                        write_msg(event.user_id,
                                  'Чтобы запустить поиск подходящих для знакомтсва людей - напиши "искать"')
                    else:
                        write_msg(event.user_id, 'Я помню тебя. Давай продолжим работу. Напиши "смотреть"!')
                elif request == 'искать':
                    write_msg(event.user_id, 'Начинаю подбор...')
                    vk_application.get_match_persons(conn, user_id=event.user_id, VK_user_token=VK_user_token,
                                                     URL_search=URL_search)
                    write_msg(event.user_id, '...подбор окончен! Напиши "смотреть", чтобы увидеть результаты')
                elif request == 'смотреть':
                    count = 0
                    clear_match_list = vk_application.get_persons_for_show(conn, event.user_id)
                    if not clear_match_list:
                        write_msg(event.user_id, 'У тебя закончились варианты или ты ещё не подбирал кандидатов. Напиши "искать", чтобы я составил новый список!')
                        print(clear_match_list)
                    else:
                        result = vk_application.get_match_info(conn, clear_match_list[count], VK_user_token, URL_get)
                        watch_id = result["response"][0]["id"]
                        try:
                            take_photos = vk_application.get_photos(result["response"][0]["id"], VK_user_token,
                                                                    URL_get_photo)
                            photos = []
                            for foto in take_photos[0:3]:
                                photos.append(f'photo{foto[4]}_{foto[3]}_{VK_user_token}')
                            write_msg_att(event.user_id,
                                          f'Имя: {result["response"][0]["first_name"]}'
                                          f'\nФамилия: {result["response"][0]["last_name"]}'
                                          f'\nСсылка: https://vk.com/id{result["response"][0]["id"]}'
                                          f'\nНапиши "далее" чтобы посмотреть другие варианты или "добавь" чтобы добавить человека в избранное',
                                          photos)
                        except KeyError:
                            write_msg(event.user_id,
                                      f'Имя: {result["response"][0]["first_name"]}'
                                      f'\nФамилия: {result["response"][0]["last_name"]}'
                                      f'\nСсылка: https://vk.com/id{result["response"][0]["id"]}'
                                      f'\nНапиши "далее" чтобы посмотреть другие варианты или "добавь" чтобы добавить человека в избранное'
                                      f'\nЯ не смог загрузить фото...')
                        count += 1
                        db_application.add_reviewed_persons(conn, event.user_id, result['response'][0]['id'])
                elif request == 'далее':
                    result = vk_application.get_match_info(conn, clear_match_list[count], VK_user_token, URL_get)
                    watch_id = result["response"][0]["id"]
                    try:
                        take_photos = vk_application.get_photos(result["response"][0]["id"], VK_user_token,
                                                                URL_get_photo)
                        photos = []
                        for foto in take_photos[0:3]:
                            photos.append(f'photo{foto[4]}_{foto[3]}_{VK_user_token}')
                        write_msg_att(event.user_id,
                                      f'Имя: {result["response"][0]["first_name"]}'
                                      f'\nФамилия: {result["response"][0]["last_name"]}'
                                      f'\nСсылка: https://vk.com/id{result["response"][0]["id"]}'
                                      f'\nНапиши "далее" чтобы посмотреть другие варианты или "добавь" чтобы добавить человека в избранное',
                                      photos)
                    except KeyError:
                        write_msg(event.user_id, f'Имя: {result["response"][0]["first_name"]}'
                                                 f'\nФамилия: {result["response"][0]["last_name"]}'
                                                 f'\nСсылка: https://vk.com/id{result["response"][0]["id"]}'
                                                 f'\nНапиши "далее" чтобы посмотреть другие варианты или "добавь" чтобы добавить человека в избранное'
                                                 f'\nЯ не смог загрузить фото...')

                    count += 1
                    db_application.add_reviewed_persons(conn, event.user_id, result['response'][0]['id'])
                elif request == 'добавь':
                    db_application.add_fav_persons(conn, event.user_id, watch_id)
                    write_msg(event.user_id,
                              f'Добавил пользователя с ID {watch_id} в твой список избранных! Чтобы продолжить просмотр напиши "далее".')
                elif request == 'избранное':
                    fav_list = db_application.take_user_favorite(conn, event.user_id)
                    for id in fav_list:
                        id_info = vk_application.get_favorite_info(id, VK_user_token, URL_get)
                        try:
                            take_photos = vk_application.get_photos(id_info["response"][0]["id"], VK_user_token,
                                                                    URL_get_photo)
                            photos = []
                            for foto in take_photos[0:3]:
                                photos.append(f'photo{foto[4]}_{foto[3]}_{VK_user_token}')
                            write_msg_att(event.user_id,
                                          f'Имя: {id_info["response"][0]["first_name"]}'
                                          f'\nФамилия: {id_info["response"][0]["last_name"]}'
                                          f'\nСсылка: https://vk.com/id{id_info["response"][0]["id"]}'
                                          f'\nНапиши "далее" чтобы посмотреть другие варианты или "добавь" чтобы добавить человека в избранное',
                                          photos)
                        except KeyError:
                            write_msg(event.user_id, f'Имя: {id_info["response"][0]["first_name"]}'
                                                     f'\nФамилия: {id_info["response"][0]["last_name"]}'
                                                     f'\nСсылка: https://vk.com/id{id_info["response"][0]["id"]}'
                                                     f'\nНапиши "далее" чтобы посмотреть другие варианты или "добавь" чтобы добавить человека в избранное'
                                                     f'\nЯ не смог загрузить его фото...')
                elif request == 'изменить город':
                    write_msg(event.user_id, 'Хорошо, в каком городе ты живешь? Напиши без ошибок и я попробую понять!')
                    want_change_city = 1

                elif request == 'изменить год':
                    write_msg(event.user_id,
                              'Хорошо, какой твой год рождения? Напиши числом из четырех цифр (например: 1991)!')
                    want_change_year = 1

                elif want_change_city == 1:
                    db_application.change_user_city(conn, event.user_id, request, VK_user_token, URL_get_city)
                    write_msg(event.user_id, f'Отлично, я записал {request} как твой город!')
                    want_change_city = 0

                else:
                    try:
                        request = int(request)
                        if request in range(1900, 2100) and want_change_year == 1:
                            db_application.change_user_bdate(conn, event.user_id, request)
                            write_msg(event.user_id, f'Отлично, я записал {request} как твой год рождения!')
                            want_change_year = 0
                    except:
                        write_msg(event.user_id,
                                  'Не понял команду! Повтори предидущую команду или давай попробуем сначала - напиши "привет"!')
