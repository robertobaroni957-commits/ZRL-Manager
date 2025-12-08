from newZRL import create_app

app = create_app()

with app.test_request_context():
    print(app.url_map)
