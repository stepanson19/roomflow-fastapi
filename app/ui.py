HOME_PAGE = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RoomFlow API</title>
  <style>
    :root { color-scheme: light; font-family: Inter, Arial, sans-serif; }
    body { margin: 0; background: #f5f7fb; color: #172033; }
    main { max-width: 1020px; margin: 0 auto; padding: 42px 20px 54px; }
    .top { display: grid; gap: 14px; margin-bottom: 30px; }
    h1 { font-size: clamp(34px, 6vw, 62px); line-height: 1; margin: 0; letter-spacing: 0; }
    p { font-size: 18px; line-height: 1.55; max-width: 740px; margin: 0; color: #506070; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }
    .card {
      background: white; border: 1px solid #dde4ef; border-radius: 8px;
      padding: 18px; min-height: 128px;
      box-shadow: 0 12px 28px rgba(23, 32, 51, .08);
    }
    .card strong { display: block; font-size: 18px; margin-bottom: 8px; }
    .card span { display: block; color: #607083; line-height: 1.45; }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 26px; }
    a {
      color: white; text-decoration: none; background: #136f63;
      border-radius: 7px; padding: 12px 16px; font-weight: 700;
    }
    a.secondary { background: #27344a; }
    code { background: #e9eef6; border-radius: 5px; padding: 2px 5px; }
  </style>
</head>
<body>
<main>
  <section class="top">
    <h1>RoomFlow</h1>
    <p>
      REST-сервис для студии репетиций: комнаты, оборудование, бронирования,
      роли пользователей и подбор лучшего свободного слота по ограничениям клиента.
    </p>
  </section>
  <section class="grid">
    <div class="card">
      <strong>1. Вход</strong>
      <span>Первый зарегистрированный пользователь получает роль администратора.</span>
    </div>
    <div class="card">
      <strong>2. Каталог</strong>
      <span>Администратор добавляет комнаты и оборудование.</span>
    </div>
    <div class="card">
      <strong>3. Бронь</strong>
      <span>API проверяет вместимость, пересечения по времени и считает стоимость.</span>
    </div>
    <div class="card">
      <strong>4. Подбор</strong>
      <span><code>/recommendations/rooms</code> ранжирует свободные слоты.</span>
    </div>
  </section>
  <nav class="actions">
    <a href="/docs">Swagger UI</a>
    <a class="secondary" href="/redoc">ReDoc</a>
    <a class="secondary" href="/openapi.json">OpenAPI JSON</a>
  </nav>
</main>
</body>
</html>
"""
