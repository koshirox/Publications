# Publications

Лабораторные работы по технологиям сетевого программирования.

ЛР1 - работа с PostgreSQL через SQLAlchemy.
ЛР2 - REST API на FastAPI, JWT-авторизация и Nginx.

В приложении есть пользователи, посты, категории, комментарии, лайки и подписки.
Роли - пользователь, модератор и администратор. Пароли хранятся в виде хешей Argon2,
JWT действует один час.

## Запуск

1. Создать базу `Publications` в PostgreSQL.
2. Скопировать `.env.example` в `.env`, заполнить подключение к БД и `JWT_SECRET`
   случайной строкой длиной от 32 символов.
3. В папке проекта выполнить команды.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe init_db.py
.\.venv\Scripts\python.exe main.py
```

На настроенном компьютере достаточно запустить `main.py`.
Swagger - [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

Для Nginx используется `nginx.conf`. На этом компьютере он запускается отдельно.

```powershell
$nginx = "$env:LOCALAPPDATA\Publications\nginx-1.31.10"
Start-Process "$nginx\nginx.exe" -WorkingDirectory $nginx -ArgumentList '-c','C:/Projects/TCP/nginx.conf' -WindowStyle Hidden
```

Через Nginx API доступен на порту `8080`, статический файл - `/status.txt`.
Файл `static/status.txt` должен лежать в папке `html` установленного Nginx.

В новой базе сначала зарегистрировать администратора и назначить ему роль через SQL,
подставив его email.

```sql
UPDATE users SET role = 'admin' WHERE email = 'admin@example.com';
```
