# Сайт «Продуктовый помощник» 
![workflow](https://github.com/Bacepok/foodgram-project-react/actions/workflows/foodgram-workflow.yml/badge.svg)



## Описание

Сайт «Продуктовый помощник» это место для публикации рецептов. Рецепты можно добавлять в избранное, так же можно подписаться на других авторов и создавать список покупок для заданных блюд.

Продуктовый помощник [доступен по адресу](http://158.160.35.114/)

Логин и пароль супер пользователя для доступа в [админку](http://158.160.35.114/admin/) bacep 984357

## Технологии:

Python, Django, Django Rest Framework, Docker, Gunicorn, NGINX, PostgreSQL, Yandex Cloud

## Запуск проекта локально
### Клонировать репозиторий и перейти в него в командной строке:
Напечатайте в терминале команду git clone, после неё поставьте пробел, вставьте скопированный адрес и выполните команду:

<code>git clone git@github.com:Bacepok/foodgram-project-react.git</code>

### Cоздать и активировать виртуальное окружение:
```
python3 -m venv env
source env/bin/activate
python3 -m pip install --upgrade pip
```
### Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
### Создайте .env файл в каталоге infra:

Шаблон для запонения:
<pre><code>
DB_ENGINE=django.db.backends.postgresql # указываем, что работаем с postgresql
DB_NAME=postgres # имя базы данных
POSTGRES_USER=postgres # логин для подключения к базе данных
POSTGRES_PASSWORD=postgres # пароль для подключения к БД (установите свой)
DB_HOST=db # название сервиса (контейнера)
DB_PORT=5432 # порт для подключения к БД
</code></pre>

### Выполнить миграции:

python3 manage.py migrate

### Запустить проект:

Перейдите в директорию с файлом manage.py и запустите Gunicorn:
<pre><code>
gunicorn --bind 0.0.0.0:8000 yatube.wsgi
</code></pre>

После запуска проект будут доступен по адресу: http://localhost/

### Ссылка на образы проекта на Docker:
#### Backend
https://hub.docker.com/r/bacep/foodgram_backend
#### Frontend
https://hub.docker.com/r/bacep/frontend_foodgram

## Запуск проекта на удалённом сервере

### Клонировать репозиторий:

<code>git clone git@github.com:Bacepok/foodgram-project-react.git</code>

Установить на сервере Docker, Docker Compose:

Скопировать на сервер файлы docker-compose.yml, nginx.conf из папки infra 

Для работы с GitHub Actions необходимо в репозитории в разделе Secrets > Actions создать переменные окружения:

```
SECRET_KEY              # секретный ключ Django проекта
DOCKER_PASSWORD         # пароль от Docker Hub
DOCKER_USERNAME         # логин Docker Hub
HOST                    # публичный IP сервера
USER                    # имя пользователя на сервере
PASSPHRASE              # *если ssh-ключ защищен паролем
SSH_KEY                 # приватный ssh-ключ
TELEGRAM_TO             # ID телеграм-аккаунта для посылки сообщения
TELEGRAM_TOKEN          # токен бота, посылающего сообщение

ALLOWED_HOSTS           # публичный IP адрес на которосм будет размещён проект
DB_ENGINE               # django.db.backends.postgresql
DB_NAME                 # postgres
POSTGRES_USER           # postgres
POSTGRES_PASSWORD       # postgres
DB_HOST                 # db
DB_PORT                 # 5432 (порт по умолчанию)
```

Создать и запустить контейнеры Docker, выполнить команду на сервере (версии команд "docker compose" или "docker-compose" отличаются в зависимости от установленной версии Docker Compose):

После успешной сборки выполнить миграции:
<pre><code>
sudo docker compose exec backend python manage.py migrate
</code></pre>
Создать суперпользователя:
<pre><code>
sudo docker compose exec backend python manage.py createsuperuser
</code></pre>
Собрать статику:
<pre><code>
sudo docker compose exec backend python manage.py collectstatic --noinput
</code></pre>
