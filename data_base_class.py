import psycopg2
import urllib.parse as urlparse
from psycopg2 import Error
import os


class DataBase:

    def __init__(self, *args):

        url = urlparse.urlparse(os.environ['DATABASE_URL'])
        dbname = url.path[1:]
        user = url.username
        password = url.password
        host = url.hostname
        port = url.port
        self.connection = psycopg2.connect(user=user,
                                           # пароль, который указали при установке PostgreSQL
                                           password=password,
                                           host=host,
                                           port=port,
                                           database=dbname)
        self.cursor = self.connection.cursor()
        self.err = ''


    def read_all(self, table_name: str):
        sql_query = f"SELECT * FROM {table_name}"
        try:
            self.cursor.execute(sql_query)
            record = self.cursor.fetchall()
            return record

        except (Exception, Error) as error:
            self.err = "Ошибка при работе с PostgreSQL: \n" + error
            return self.err
        finally:
            self.close()

    def read_one(self, table_name, target):
        sql_query = f"SELECT * FROM {table_name} WHERE userid={target}"
        try:
            self.cursor.execute(sql_query)
            record = self.cursor.fetchone()
            return record

        except (Exception, Error) as error:
            self.err = "Ошибка при работе с PostgreSQL: \n" + error
            return self.err
        finally:
            self.close()

    def insert(self, sql_query, *args):
        try:
            self.cursor.execute(sql_query, args)
            self.connection.commit()
            return 'Данные добавлены в базу'

        except (Exception, Error) as error:
            self.err = "Ошибка при работе с PostgreSQL: \n" + str(error)
            print(self.err)
            return self.err
        finally:
            self.close()

    def update(self, table, field, new_value, target):
        try:
            sql_query = f"UPDATE {table} SET {field} = '{new_value}' WHERE userid={target}"
            self.cursor.execute(sql_query)
            self.connection.commit()
            return 'Успешно обновлено'

        except (Exception, Error) as error:
            self.err = "Ошибка при работе с PostgreSQL: \n" + str(error)
            return self.err
        finally:
            self.close()

    def delete(self, table, target):
        try:
            sql_query = f"DELETE FROM {table} WHERE userid={target}"
            self.cursor.execute(sql_query)
            self.connection.commit()
        except (Exception, Error) as error:
            self.err = "Ошибка при работе с PostgreSQL: \n" + str(error)
            return self.err
        finally:
            self.close()

    def close(self):
        self.cursor.close()
        self.connection.close()
        if self.err:
            print(self.err)


if __name__ == '__main__':
    url = urlparse.urlparse(os.environ['DATABASE_URL'])
    dbname = url.path[1:]
    user = url.username
    password = url.password
    host = url.hostname
    port = url.port

    cheeses = DataBase().read_all('cheese')
    btns = []
    for i in cheeses:
        btns.append([i[1], i[2]])

    start = 0


    while True:
        end = start + 3
        print('start= ', start)
        print('end= ', end)
        print(btns[start:end])
        cnt = input('next/prev: ')
        if cnt == '1':
            start += 3
        if cnt == '2':
            start -= 3
