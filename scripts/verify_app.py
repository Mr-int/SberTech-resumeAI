from app.main import create_app

app = create_app()
print(app.title)
print('Routes:')
for r in app.router.routes:
    print('-', r.path)
