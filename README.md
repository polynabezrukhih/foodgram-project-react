## Сайт

http://food-grammyp.ddns.net

# Данные для администратора:
<br/>
Логин: polyna<br/>
Email: polyna@mail.ru<br/>
Пароль: 12345678<br/>

# Foodgram - «Продуктовый помощник»

Сайт, на котором пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», скачивать список продуктов, согласно выбранных блюд.


# Установка

<br/>
Клонируйте репозиторий<br/>
в каталоге /infra/ Создайте .env файл в формате<br/>
<br/>
DEBUG=False<br/>
SECRET_KEY=<секретный ключ из одноименного параметра><br/>
ALLOWED_HOSTS=127.0.0.1,localhost,130.193.55.178,food-grammyp.ddns.net,backend<br/>
CSRF_TRUSTED_ORIGINS = http://localhost http://127.0.0.1 https://food-grammyp.ddns.net<br/>
DB_ENGINE=django.db.backends.postgresql<br/>
DB_NAME=food_db<br/>
POSTGRES_USER=postgres<br/>
POSTGRES_PASSWORD=1234<br/>
DB_HOST=db<br/>
DB_PORT=5432<br/>

<br/>
скопируйте папку /infra/<br/>
scp -r infra/* di@<you server ip>:/home/< username >/foodgram/<br/>
<br/>
подключитесь к серверу через ssh и перейдите в каталог<br/>
/home/< username >/foodgram/<br/>
<br/>
запустите установку и сборку контейнеров<br/>
docker compose up -d<br/>

# команды при работе с Docker
посмотреть логи контейнера<br/>
docker logs --since=1h <container_id><br/>
<br/>
подключить к контейнеру<br/>
docker exec -it <id контейнера> sh<br/>
<br/>
список контейнеров, образов, и volumes<br/>
docker ps<br/>
docker image ls<br/>
docker volume ls<br/>
<br/>
остановить все контейнеры и удалить<br/>
docker compose stop<br/>
sudo docker compose rm web<br/>
docker stop $(docker ps -a -q)<br/>
docker rm $(docker ps -a -q)<br/>
docker rmi $(docker image ls)<br/>
<br/>
создать суперпользователя <br/>
docker ps<br/>
docker exec -it < id контейнера > bash <br/>
python manage.py createsuperuser<br/>



# Автор backend сервисов
[Полина Безруких](https://github.com/polynabezrukhih)

# Автор frontend сервисов
[Yandex Praktikum](https://github.com/yandex-praktikum)
