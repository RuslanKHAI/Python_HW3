import asyncpg
import logging
from tablesql import CREATE_TABLES_SQL
from fastapi.encoders import jsonable_encoder

logging.basicConfig(level=logging.INFO)
# Шаблон Singleton
class interact_postgreSQL_database:
    _instance = None

    def __new__(cls, database_fastapi_url: str):
        if cls._instance is None:
            cls._instance = super(interact_postgreSQL_database, cls).__new__(cls)
            cls._instance.database_fastapi_url = database_fastapi_url
            cls._instance.pool = None
        return cls._instance

#Подключение к базе
    async def connection_database(self):
        self.pool = await asyncpg.create_pool(self.database_fastapi_url)
#interact_postgres.py вызывает tablesql import CREATE_TABLES_SQL ее при необходимости
    async def create_database(self):
        async with self.pool.acquire() as conn:
            for query in CREATE_TABLES_SQL:
                await conn.execute


#Поиск пользователя: 
    async def get_user_by_credentials(self, client_id: int, auth_token: str):
        async with self.pool.acquire() as conn:
            code_result = await conn.fetchrow("""
                SELECT * FROM users WHERE id = $1 AND auth_token = $2
            """, client_id, auth_token)
            if code_result:
                return dict(code_result)
            else:
                return None

#Работа с ссылками:Вставка данных о ссылке, Учет срока действия (expires_at) и пр.
    async def store_link(self, long_link: str, short_link: str, client_id: int, is_authorized: bool, expires_at):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO links (long_link, short_link, client_id, is_authorized, expires_at)
                VALUES ($1, $2, $3, $4, $5)
            """, long_link, short_link, client_id, is_authorized, expires_at)

#Работа с ссылками:
# Быстрый поиск по индексируемому полю short_link
    async def search_at_the_source_url_short_link(self, short_url: str):
        async with self.pool.acquire() as conn:
            code_result = await conn.fetchrow("""
                SELECT long_link FROM links WHERE short_link = $1
            """, short_url)
            if code_result:
                return code_result['long_link']
            else:
                return None
#Этот метод возвращает идентификатор клиента (client_id), 
# который создал короткую ссылку.

         
    async def client_created_shortcut(self, short_url: str):
        async with self.pool.acquire() as conn:
            code_result = await conn.fetchrow("""
                SELECT client_id FROM links WHERE short_link = $1
            """, short_url)
            if code_result:
                return code_result['client_id']
            else:
                return None
# метод удаляет короткую ссылку из базы данных    
    async def removes_short_reference_database(self, short_url: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM links WHERE short_link = $1
            """, short_url)

 #Этот метод обновляет исходную ссылку (long_link) для заданной короткой ссылки   
    async def method_updates_source_link(self, short_link: str, long_link: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE links SET long_link = $1 WHERE short_link = $2
            """, long_link, short_link)

 #Этот метод возвращает дату создания короткой ссылки   
    async def return_date_created_short_link(self, short_link: str):
        async with self.pool.acquire() as conn:
            code_result = await conn.fetchrow("""
                SELECT created_at FROM links WHERE short_link = $1
            """, short_link)
            
            if code_result:
                return code_result['created_at']
            else:
                return None
            
#Этот метод сохраняет информацию о доступе к короткой ссылке в таблицу statistics
    async def saves_short_link_access_statistics_table(self, short_url: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO statistics (short_link)
                VALUES ($1)
            """, short_url)

 # метод возвращает статистику по короткой ссылке.
    async def return_statistics_short_link(self, short_url: str):
        async with self.pool.acquire() as conn:
            return_full_link_date = await conn.fetchrow("""
                SELECT long_link, created_at FROM links WHERE short_link = $1
            """, short_url)
            
            if return_full_link_date:
                long_link = return_full_link_date['long_link']
                date_short_link = return_full_link_date['created_at']
            else:
                return None
            #Получение количества переходов/выбирает количество строк в таблице statistics, 
            # где короткая ссылка соответствует переданной
            selects_number_rows_passed_link = await conn.fetchrow("""
                SELECT COUNT(*) FROM statistics WHERE short_link = $1
            """, short_url)
            #Если результат запроса существует, то извлекает количество переходов.
            if selects_number_rows_passed_link:
                selects_number_rows = selects_number_rows_passed_link['count']
            else:
                selects_number_rows = 0
            #Выбирает максимальную дату доступа (access_date) из таблицы statistics для данной короткой ссылки
            max_date_result = await conn.fetchrow("""
                SELECT MAX(access_date) FROM statistics WHERE short_link = $1
            """, short_url)
            
            if max_date_result and max_date_result['max'] is not None:
                max_date = max_date_result['max']
            else:
                max_date = None
            
            stats = {
                "short_url": short_url,
                "full_url": long_link,
                "date_short_link": date_short_link,
                "selects_number_rows": selects_number_rows,
                "max_date": max_date
            }
            
            return jsonable_encoder(stats)
        
#метод проверяет доступность алиаса для короткой ссылки
    async def alias_availability_check(self, alias: str) -> bool:
        return await self.search_at_the_source_url_short_link(alias) is None


    async def search_short_link_at_the_source_url(self, original_url: str):
        async with self.pool.acquire() as conn:
            logging.info("Запрос на поиск ссылки")
            code_result = await conn.fetchrow("""
                SELECT short_link FROM links WHERE long_link = $1
            """, original_url)
            logging.info(f"Результат запроса: {code_result}")
            if code_result:
                return {"short_link": code_result['short_link']}
            else:
                return None
            
    
    async def purge_old_links(self):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    INSERT INTO expired_links (long_link, short_link, created_at, expires_at, client_id, is_authorized)
                    SELECT long_link, short_link, created_at, expires_at, client_id, is_authorized
                    FROM links
                    WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP
                """)
                
                await conn.execute("""
                    DELETE FROM links WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP
                """)


    async def return_all_links_users(self, client_id: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():    
                active_links_count = await conn.fetchval("""
                        SELECT COUNT(*) 
                        FROM links 
                        WHERE client_id = $1 AND expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP;
                    """, int(client_id))
                    
                if active_links_count is None:
                        active_links_count = 0
                    
                expired_links_count = await conn.fetchval("""
                        SELECT COUNT(*) 
                        FROM expired_links 
                        WHERE client_id = $1;
                    """, int(client_id))
                    
                if expired_links_count is None:
                        expired_links_count = 0
                    
                return {
                        "active_links": active_links_count,
                        "expired_links": expired_links_count
                    }

    async def pool_database_connection_close(self):
        if self.pool:
            await self.pool.pool_database_connection_close()