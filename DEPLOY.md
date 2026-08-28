# Как выложить Resume Designer в интернет

## Важно про Netlify

**Netlify Drag & Drop не подойдёт для этого проекта.**

Туда можно закинуть только статику (HTML/CSS/JS). У нас:

- бэкенд на **Python / FastAPI**;
- ключи **GigaChat**;
- API `/api/v1/chat`, PDF, сессии.

Без сервера сайт на Netlify откроется, но кнопки «Отправить» работать не будут.

Для полноценного запуска используйте **Render** (ниже) или аналог: Railway, Fly.io.

---

## Вариант: Render (рекомендуется)

Бесплатный публичный URL, Docker уже в репозитории.

### Шаги

1. Зарегистрируйтесь на [render.com](https://render.com).
2. **New → Web Service** (или **Blueprint** и выберите `render.yaml`).
3. Подключите репозиторий GitVerse/GitHub с этим проектом  
   (если GitVerse не подключается — загрузите код на GitHub и подключите его).
4. Настройки:
   - **Runtime:** Docker  
   - **Health Check Path:** `/health`
5. В **Environment** добавьте переменные (как в `.env`, **без** файла `.env` в git):

| Ключ | Пример |
|------|--------|
| `GIGACHAT_USE_STUB` | `false` |
| `GIGACHAT_VERIFY_SSL` | `false` |
| `GIGACHAT_AUTH_KEY` | ваш base64-ключ |
| `GIGACHAT_CLIENT_ID` | ваш client id |
| `GIGACHAT_MODEL_LIGHT` | `GigaChat-2` |
| `GIGACHAT_MODEL_HEAVY` | `GigaChat-2-Pro` |

6. **Create Web Service** → дождитесь Deploy.
7. Откройте выданный URL — главная сразу ведёт на интерфейс (`/site/`).

Документация API: `https://ВАШ-СЕРВИС.onrender.com/docs`  
Проверка: `https://ВАШ-СЕРВИС.onrender.com/health`

> На бесплатном плане сервис «засыпает» без трафика (~15 мин). Первый запрос после сна может занять 30–60 секунд.

---

## Вариант: Railway

1. [railway.app](https://railway.app) → New Project → Deploy from GitHub.
2. Добавьте те же env-переменные.
3. Railway подхватит `Dockerfile` или `Procfile`.

---

## Локально перед выкладкой

```bash
pip install -r requirements.txt
# или: pip install .
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Откройте http://127.0.0.1:8000/ — редирект на сайт.

---

## Что не класть в публичный репозиторий

- файл `.env` с ключами;
- `GIGACHAT_AUTH_KEY` / секреты в коде.

Только Environment Variables в панели хостинга.
