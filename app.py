import os
import logging
import aioredis
import asyncio
import redis.asyncio as redis
import asyncpg
import BackgroundScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from business_logic import LinkRequest, CustomLinkRequest
from business_logic import business_logic_shortlink
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from interact_postgres import interact_postgreSQL_database

#Настройка логирования/
#базовый уровень логирования для приложения на уровне INFO. 
#Это означает, что все сообщения с уровнем INFO и выше (например, WARNING, ERROR, CRITICAL) будут отображаться в логах
logging.basicConfig(level=logging.INFO)

#Рассматриваем два варианта через (так как в разных версиях по разному работает события и конфликтуют):
#1.on_event
#2.lifespan
fastapi_application = FastAPI()           #создаем API-сервер
task_planner = AsyncIOScheduler() #создаем планировщик

database_fastapi_url = os.environ.get('DATABASE_URL')
ipd = interact_postgreSQL_database(database_fastapi_url)   # подключаем БД.
business_logic = business_logic_shortlink(ipd)
# создаем соединение с Redis.
cache_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
redis = aioredis.from_url(cache_url, decode_responses=True)

#1.on_event____________________________________________
#Обработка событий при запуске и остановке приложения
@fastapi_application.on_event("startup")
async def launching_app():
    await ipd.connection_database()   #Подключаемся к базе данных
    await ipd.create_database() #Создаем таблицы в базе данных, если они еще не существую
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache") #Инициализирует кэш FastAPI с использованием Redis в качестве бэкенда
    
    task_planner.add_job(purge_old_links, 'interval', minutes=1) #Добавляет задачу purge_old_links в планировщик для запуска каждую минуту.
    task_planner.start()

#Событие остановки (stopping_app)
@fastapi_application.on_event("shutdown")
async def stopping_app():
    task_planner.shutdown()
    await ipd.pool_database_connection_close()

#2.lifespan
'''
______________________________________________________
@asynccontextmanager
async def lifespan(app: FastAPI):
    task_planner = AsyncIOScheduler() # создаем планировщик фона.
    
    # Startup tasks
    await ipd.connection_database()
    await ipd.create_database()
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    
    task_planner.add_job(purge_old_links, 'interval', minutes=1) 
    task_planner.start()
    
    yield
    
    # Shutdown tasks
    task_planner.shutdown()
    await ipd.pool_database_connection_close()

# Создайте приложение с функцией lifespan
fastapi_application = FastAPI(lifespan=lifespan)
'''
_____________________________________________________
#код обрабатывает POST-запросы на создание коротких ссылок. 
#беспечивает создание коротких ссылок как для авторизованных, 
#так и для неавторизованных пользователей, с возможностью привязки 
# ссылок к аккаунтам
@fastapi_application.post('/links/shorten')
@cache(expire=60)
async def short_link_building(request: Request, link_request: LinkRequest):
    client_id = request.headers.get('username')
    auth_token = request.headers.get('sign_up').split()[1] if request.headers.get('sign_up') else None
    
    logging.info(f"Request from user: {client_id} to create a short link")

    if client_id and auth_token:
        user = await ipd.get_user_by_credentials(int(client_id), auth_token)
        if user:
            code_result = await business_logic.short_link_building(link_request.link, int(client_id), True, link_request.expires_at)
            if code_result:
                return JSONResponse(content={"short_link": code_result['short_link']}, status_code=201)
            else:
                raise HTTPException(status_code=500, detail="Error!")
        else:
            raise HTTPException(status_code=401, detail="Error. User is not def user")
    else:
        code_result = await business_logic.short_link_building(link_request.link, None, False, link_request.expires_at)
        if code_result:
            return JSONResponse(content={"short_link": code_result['short_link']}, status_code=201)
        else:
            raise HTTPException(status_code=500, detail="Error!")

#эндпоинт принимает GET-запрос с кодом короткой ссылки 
# и перенаправляет пользователя на исходный URL
@fastapi_application.get('/links/{short_code}')
@cache(expire=60)
async def redirect_user_short_link(short_code: str):
    logging.info(f"Request to access short link: {short_code}")
    original_url = await business_logic.get_source_url(short_code)
    if original_url:
        return RedirectResponse(url=original_url, status_code=302)
    else:
        raise HTTPException(status_code=404, detail="Error! No original link")
    

#эндпоинт принимает DELETE-запрос для удаления короткой ссылки (removes_short_reference_database). 
@fastapi_application.delete('/links/{short_code}')
@cache(expire=0)
async def removes_short_reference_database(short_code: str, request: Request):
    client_id = request.headers.get('username')
    auth_token = request.headers.get('sign_up').split()[1] if request.headers.get('sign_up') else None

    logging.info(f"Request from user: {client_id} to delete short link: {short_code}")

    if client_id and auth_token:
        if await business_logic.removes_short_reference_database(short_code, int(client_id), auth_token):
            await redis.delete(f"fastapi-cache:{short_code}")
            return {"message": "deleted short link"}
        else:
            raise HTTPException(status_code=403, detail="Error")
    else:
        raise HTTPException(status_code=401, detail="Error. you're not logged in")

#эндпоинт обновляет существующую короткую ссылку. 
# Доступно только для авторизованных пользователей.
@fastapi_application.put('/links/{short_code}')
@cache(expire=0)
async def short_link_update_for_authorized_users(short_code: str, request: Request, link_request: LinkRequest):
    client_id = request.headers.get('username')
    auth_token = request.headers.get('sign_up').split()[1] if request.headers.get('sign_up') else None

    logging.info(f"Request from user: {client_id} to delete short link: {short_code}")
    
    if client_id and auth_token:
        if await business_logic.update_url(short_code, link_request.link, int(client_id), auth_token):
            await redis.delete(f"fastapi-cache:{short_code}")
            return {"message": "short link update (обновили существующую короткую ссылку)"}
        else:
            raise HTTPException(status_code=403, detail="Error")
    else:
        raise HTTPException(status_code=401, detail="Error. you're not logged in")

#эндпоинт возвращает статистику по короткой ссылке.
#  Доступно только для авторизованных пользователей.
@fastapi_application.get('/links/{short_code}/stats')
@cache(expire=60)
async def return_statistics_short_link_for_authorized_users(short_code: str, request: Request):
    client_id = request.headers.get('username')
    auth_token = request.headers.get('sign_up').split()[1] if request.headers.get('sign_up') else None

    logging.info(f"Request from user: {client_id} to retrieve stats for short link: {short_code}")
    
    if not client_id or not auth_token:
        raise HTTPException(status_code=401, detail="Error. you're not logged in")

    try:
        client_id_integer = int(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Error. User is not def")

    stats = await business_logic.return_statistics_short_link_for_authorized_users(short_code, client_id_integer, auth_token)
    
    if stats is None:
        raise HTTPException(status_code=403, detail="Stats not found")
    
    return JSONResponse(content=stats, media_type="application/json")


# эндпоинт создает короткую ссылку с пользовательским алиасом.
@fastapi_application.post('/links/custom_shorten')
@cache(expire=60)
async def generate_short_link_custom_request(request: Request, link_request: CustomLinkRequest):
    client_id = request.headers.get('username')
    auth_token = request.headers.get('sign_up').split()[1] if request.headers.get('sign_up') else None
    
    logging.info(f"Request from user: {client_id} short link custom_alias")

    if client_id and auth_token:
        user = await ipd.get_user_by_credentials(int(client_id), auth_token)
        if user:
            code_result = await business_logic.generate_short_link_custom_alias(link_request.link, link_request.custom_alias, int(client_id), True, link_request.expires_at)
            if code_result:
                return JSONResponse(content={"short_link": code_result['short_link']}, status_code=201)
            else:
                raise HTTPException(status_code=500, detail="Error!")
        else:
            raise HTTPException(status_code=401, detail="Error. you're not logged in")
    else:
        code_result = await business_logic.generate_short_link_custom_alias(link_request.link, link_request.custom_alias, None, False, link_request.expires_at)
        if code_result:
            return JSONResponse(content={"short_link": code_result['short_link']}, status_code=201)
        else:
            raise HTTPException(status_code=500, detail="Error!")

#эндпоинт ищет короткую ссылку по исходному URL.
@fastapi_application.get('/search')
@cache(expire=60)
async def search_at_the_source_url(original_url: str):

    logging.info(f"Request from user:{original_url}")

    if not original_url:
        raise HTTPException(status_code=400, detail="Original URL is required")
    
    code_result = await business_logic.short_link_search_at_the_source_url(original_url)
    
    if code_result:
        return {
            "short_link": code_result['short_link']
        }
    else:
        raise HTTPException(status_code=404, detail="Link not found")

#эндпоинт возвращает обзор всех ссылок для авторизованного пользователя.
@fastapi_application.get('/overview')
@cache(expire=60)
async def return_all_links_users(request: Request):
    client_id = request.headers.get('username')
    auth_token = request.headers.get('sign_up').split()[1] if request.headers.get('sign_up') else None
    
    logging.info(f"Request from user: {client_id}")

    if client_id and auth_token:
        user = await ipd.get_user_by_credentials(int(client_id), auth_token)
        if user:
            return await business_logic.return_all_links_users(client_id)
        else:
            raise HTTPException(status_code=401, detail="Error. you're not logged in")
 
#функция удаляет просроченные ссылки из базы данных. 
# Вызывается каждую минуту с помощью планировщика задач.
async def purge_old_links():
    await ipd.purge_old_links()