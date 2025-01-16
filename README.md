Находясь в папке infra, выполните команду docker-compose up. При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.

По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.

# Foodgram: Продуктовый помощник

**Foodgram** — это веб-приложение для публикации рецептов, подписки на других пользователей, добавления рецептов в избранное, формирования списка покупок и удобной фильтрации рецептов по тегам.

## Основные возможности

### Для авторизованных пользователей:
- **Главная страница**: Доступ к рецептам с сортировкой по дате публикации (новые рецепты сверху).
- **Профили пользователей**: Возможность просматривать страницы других пользователей и их рецепты.
- **Рецепты**: 
  - Возможность добавлять рецепты в избранное.
  - Фильтрация рецептов по тегам на всех страницах, включая избранное и рецепты одного автора.
  - Пагинация для удобной навигации.
- **Мои подписки**:
  - Подписка на авторов рецептов и управление подписками.
  - Рецепты подписанных авторов автоматически отображаются на странице «Мои подписки».
- **Список покупок**:
  - Добавление рецептов в список покупок.
  - Скачивание списка покупок в формате `.txt` или `.pdf`.
  - Ингредиенты в списке покупок суммируются.
- **Создание и управление рецептами**:
  - Публикация, редактирование и удаление собственных рецептов.
- **Профиль пользователя**:
  - Изменение пароля.
  - Обновление или удаление изображения профиля.
- **Выход из системы**.

### Для неавторизованных пользователей:
- Просмотр главной страницы с рецептами.
- Доступ к странице рецептов и профилей пользователей.
- Доступ к формам входа и регистрации.

### Для администратора:
- Все модели доступны в админ-зоне.
- Поиск пользователей по имени и электронной почте.
- Поиск и фильтрация рецептов по названию, автору и тегам.
- Статистика для рецептов: общее количество добавлений в избранное.
- Поиск ингредиентов по названию.

## Техническая реализация

- **СУБД**: PostgreSQL.
- **Контейнеризация**:
  - Проект запущен на виртуальном сервере в Docker-контейнерах:
    - `nginx` для обработки запросов и раздачи статики.
    - `PostgreSQL` для базы данных.
    - `Django+Gunicorn` для бэкенда.
    - Отдельный контейнер для сборки фронтенд-ресурсов.
  - Статические файлы и медиа-файлы сохраняются в volumes.
- **Обновление проекта**: Автоматическое обновление Docker-образа из облачного хранилища.
- **Соответствие стандартам**: Код написан в соответствии с PEP 8.

## Как запустить проект локально

1. Склонируйте репозиторий:
  ```
  git clone https://github.com/Dauletnazarr/foodgram
  ```


2. Перейдите в директорию /foodgram, и соберите образы и запустите их
  ```
  docker compose up --build
  ```
3. Импортируйте все ингредиенты.
  ```
  docker exec -it foodgram-backend-1 python manage.py import_ingredients
  ```
4. Создайте супер-пользователя.
```
docker exec -it foodgram-backend-1 python manage.py createsuperuser
```

5. Затем откройте в браузере ссылку 127.0.0.1:8000
  ```
  127.0.0.1:8000/admin/
  ```
6. Перейдите во вкладку Теги и создайте несколько тегов.

## Технологии
* Python - версия 3.9.13
* Django — основной фреймворк для разработки.
* Django REST Framework — для создания API.
* SQLite3 (рекомендуется) — в качестве базы данных.
* JWT — для аутентификации пользователей.
## Авторы
Проект разработан:
* [Dauletnazar Mambetnazarov.](https://github.com/Dauletnazarr/)
