from orville_core.api import create_app
print('CREATE_APP_BEGIN', flush=True)
app = create_app()
print('CREATE_APP_OK', app.title, flush=True)
