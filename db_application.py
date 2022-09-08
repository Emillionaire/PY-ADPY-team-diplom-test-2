# START FUNCTION
# clear db
import psycopg2
from psycopg2.extras import DictCursor

import vk_application


def reset_db(conn):
    delete_tables = """
        DROP SCHEMA public CASCADE;
        CREATE SCHEMA public;
    """

    with conn.cursor() as cursor:
        cursor.execute(delete_tables)
        conn.commit()


# create db
def create_db(conn):
    main_users = '''
        CREATE TABLE IF NOT EXISTS main_users (
        ID SERIAL PRIMARY KEY,
        ID_VK INT NOT NULL UNIQUE,
        first_name VARCHAR NOT NULL,
        last_name VARCHAR NOT NULL,
        city INT NOT NULL,
        bdate INT NOT NULL,
        sex INT NOT NULL
        );
    '''

    match_person = '''
        CREATE TABLE IF NOT EXISTS match_persons (
        ID SERIAL PRIMARY KEY,
        ID_VK_user INT NOT NULL,
        ID_VK_match_person INT NOT NULL
        );
    '''

    reviewed_persons = '''
        CREATE TABLE IF NOT EXISTS reviewed_persons (
        ID SERIAL PRIMARY KEY,
        ID_VK_user INT NOT NULL,
        ID_VK_rev_person INT NOT NULL
        );
    '''

    favorite_persons = '''
        CREATE TABLE IF NOT EXISTS favorite_persons (
        ID SERIAL PRIMARY KEY,
        ID_VK_user INT NOT NULL,
        ID_VK_fav_person INT NOT NULL
        );
    '''

    black_list = '''
        CREATE TABLE IF NOT EXISTS black_list (
        ID SERIAL PRIMARY KEY,
        ID_VK_user INT NOT NULL,
        ID_VK_black_person INT NOT NULL
        );
    '''

    with conn.cursor() as cursor:
        cursor.execute(main_users)
        cursor.execute(match_person)
        cursor.execute(reviewed_persons)
        cursor.execute(favorite_persons)
        cursor.execute(black_list)
        conn.commit()


# ADD FUNCTION
# add new user to db
def add_new_user(conn, user_info):
    id_vk = user_info['id_vk']
    first_name = user_info['first_name']
    last_name = user_info['last_name']
    city = user_info['city']
    bdate = user_info['bdate']
    sex = user_info['sex']
    try:
        with conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO main_users (id_vk, first_name, last_name, city, bdate, sex)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (id_vk, first_name, last_name, city, bdate, sex))
            conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.commit()


# add match users to db
def add_match_persons(conn, id_vk, match_list):
    for match_person in match_list:
        with conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO match_persons (id_vk_user, id_vk_match_person)
                VALUES (%s, %s)
            ''', (id_vk, match_person['id']))
            conn.commit()


# add reviewed persons to db
def add_reviewed_persons(conn, id_vk_user, id_vk_rev_person):
    with conn.cursor() as cursor:
        cursor.execute('''
            INSERT INTO reviewed_persons (id_vk_user, id_vk_rev_person)
            VALUES (%s, %s)
        ''', (id_vk_user, id_vk_rev_person))
        conn.commit()


# add favorite persons to db
def add_fav_persons(conn, id_vk_user, id_vk_fav_person):
    with conn.cursor() as cursor:
        cursor.execute('''
            INSERT INTO favorite_persons (id_vk_user, id_vk_fav_person)
            VALUES (%s, %s)
        ''', (id_vk_user, id_vk_fav_person))
        conn.commit()


# CHANGE FUNCTION
# change user city
def change_user_city(conn, vk_id, city, VK_user_token, URL_get_city):
    city_id = vk_application.get_city(city, VK_user_token, URL_get_city).json()
    with conn.cursor() as cursor:
        cursor.execute('''
            UPDATE main_users
            SET city = %s
            WHERE id_vk = %s
        ''', (city_id['response']['items'][0]['id'], vk_id))
        conn.commit()


# change user bdate
def change_user_bdate(conn, id_vk, year):
    with conn.cursor() as cursor:
        cursor.execute('''
            UPDATE main_users
            SET bdate = %s
            WHERE id_vk = %s
        ''', (year, id_vk))
        conn.commit()


# SEARCH FUNCTION
# search user info
def take_user_info(conn, user_id):
    with conn.cursor() as cursor:
        cursor.execute('''
            SELECT *
            FROM main_users
            WHERE id_vk = %s
        ''', (user_id,))
        conn.commit()
        result = list(cursor.fetchone())
        return result


# check user in db
def check_user_in_db(conn, id_vk):
    try:
        with conn.corsor() as cursor:
            cursor.execute('''
                SELECT id_vk
                FROM main_users
                WHERE id_vk = %s
            ''', id_vk)
            conn.commit()
            result = cursor.fetchone()
            return result
    except:
        return None


# search user match
def take_user_match(conn, user_id):
    with conn.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute('''
            SELECT id_vk_match_person
            FROM match_persons
            WHERE id_vk_user = %s
        ''', (user_id,))
        conn.commit()
        result = cursor.fetchall()
        match_list = []
        for id in result:
            match_list.append(id[0])
        return match_list


# search user reviewed
def take_user_reviewed(conn, user_id):
    with conn.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute('''
            SELECT id_vk_rev_person
            FROM reviewed_persons
            WHERE id_vk_user = %s
        ''', (user_id,))
        conn.commit()
        result = cursor.fetchall()
        rev_list = []
        for id in result:
            rev_list.append(id[0])
        return rev_list


# search user favorite
def take_user_favorite(conn, id_vk_user):
    with conn.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute('''
            SELECT id_vk_fav_person
            FROM favorite_persons
            WHERE id_vk_user = %s
        ''', (id_vk_user,))
        conn.commit()
        result = cursor.fetchall()
        fav_list = []
        for id in result:
            fav_list.append(id[0])
        return fav_list
