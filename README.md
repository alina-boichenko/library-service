# Library Service

## Library Service
This is online management system for book borrowings. 
The system optimize the work of library administrators and will make the service much more user-friendly.

## Telegram bot
You need to create own telegram bot. Use @BotFather in telegram.

## Setting environment variables
Create an empty file .env in the following path: library_service/.env.sample.
Copy the entire content of the .env.sample file and paste it into the .env file.
Modify the placeholders in the .env file with the actual environment variables. For example (but don`t use "< >" in your project):
```
TELEGRAM_BOT_TOKEN=<your bot token>
STRIPE_API_KEY=<your secret api key in stripe>
```

## Installation:

Python3, Django, PostgreSQL must be already installed

```shell
git clone https://github.com/alina-boichenko/library-service.git
cd library_service
python3 -m venv venv
venv\Scripts\activate (on Windows)
source venv/bin/activate (on macOS)
pip install -r requirement.txt
python manage.py migrate
python manage.py runserver 
```

Input in next terminal:
```
python manage.py bot
```

## Run with docker
Docker should be installed
```
docker-compose build
docker-compose up
```

## Creating Admin user
1. Display containers list:
```
docker ps
```
2. Copy container ID
3. Run
```
docker exec -it <container ID> bash
```
4. Create superuser
```
python manage.py createsuperuser
```

## Getting access
```
Create user via /api/users/
Get access token via /api/users/token/
Install ModHeader extension and create Request header "Authorize" with value: Bearer <Your access token>
```
