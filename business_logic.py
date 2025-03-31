import asyncio
import logging
import random
import string
from pydantic import BaseModel
from interact_postgres import interact_postgreSQL_database
from typing import Optional
from fastapi import HTTPException
from datetime import datetime

logging.basicConfig(level=logging.INFO)

#Этот код использует библиотеку Pydantic 
# для определения двух моделей данных: LinkRequest и CustomLinkRequest
#структурирование и проверки данных, 
# связанных с запросами на сокращение ссылок
class LinkRequest(BaseModel):
    link: str
    expires_at: Optional[datetime] = None

class CustomLinkRequest(BaseModel):
    link: str
    custom_alias: str
    expires_at: Optional[datetime] = None


class business_logic_shortlink:
    _instance = None

    def __new__(cls, interact_postgres: interact_postgreSQL_database):
        if cls._instance is None:
            cls._instance = super(business_logic_shortlink, cls).__new__(cls)
            cls._instance.interact_postgres = interact_postgres
        return cls._instance

        
    async def get_original_url(self, short_code: str):
        await self.interact_postgres.saves_short_link_access_statistics_table(short_code)
        return await self.interact_postgres.search_at_the_source_url_short_link(short_code)
    

    async def removes_short_reference_database(self, short_code: str, client_id: int, auth_token: str) -> bool:
        user = await self.interact_postgres.get_user_by_credentials(client_id, auth_token)
        if user:
            author_id = await self.interact_postgres.client_created_shortcut(short_code)
            if user['id'] == author_id:
                await self.interact_postgres.removes_short_reference_database(short_code)
                return True
            else:
                return False
        else:
            return False
        

    async def update_url(self, short_code: str, long_url: str, client_id: int, auth_token: str) -> bool:
        user = await self.interact_postgres.get_user_by_credentials(client_id, auth_token)
        if user:
            author_id = await self.interact_postgres.client_created_shortcut(short_code)
            if user['id'] == author_id:
                await self.interact_postgres.method_updates_source_link(short_code, long_url)
                return True
            else:
                return False
        else:
            return False
        

    async def return_statistics_short_link_for_authorized_users(self, short_code: str, client_id: int, auth_token: str):
        user = await self.interact_postgres.get_user_by_credentials(client_id, auth_token)
        if not user:
            return None

        author_id = await self.interact_postgres.client_created_shortcut(short_code)

        if author_id is None:
            return None

        if user['id'] != author_id:
            return None

        stats = await self.interact_postgres.return_statistics_short_link(short_code)
        if stats:
            return stats
        else:
            return None
        

    async def short_link_building(self, long_link: str, client_id: int = None, sign_up_create_account: bool = False, expires_at: Optional[datetime] = None) -> Optional[dict]:
        symbols = string.ascii_letters + string.digits
        max_attempts = 50
        attempts = 0
        
        while attempts < max_attempts:
            short_link = ''.join(random.choice(symbols) for _ in range(6))
            
            if await self.interact_postgres.search_at_the_source_url_short_link(short_link) is None:
                break
            attempts += 1
        
        if attempts == max_attempts:
            return None
        
        await self.interact_postgres.store_link(long_link, short_link, client_id, sign_up_create_account, expires_at)
        
        return {
            "status_code": 201,
            "short_link": short_link
        }
    
    
    async def generate_short_link_custom_alias(self, long_link: str, custom_alias: str, client_id: int = None, sign_up_create_account: bool = False, expires_at: Optional[datetime] = None) -> Optional[dict]:
        if await self.interact_postgres.search_at_the_source_url_short_link(custom_alias):
            raise HTTPException(status_code=400, detail="Alias already exists")
        
        await self.interact_postgres.store_link(long_link, custom_alias, client_id, sign_up_create_account, expires_at)
        
        return {
            "status_code": 201,
            "short_link": custom_alias
        }
    

    async def return_all_links_users(self, client_id: int):
        return await self.interact_postgres.return_all_links_users(client_id)
    
    
    async def short_link_search_at_the_source_url(self, original_url: str) -> Optional[dict]:
        logging.info("Попали в сервисный класс")
        return await self.interact_postgres.short_link_search_at_the_source_url(original_url)
    
