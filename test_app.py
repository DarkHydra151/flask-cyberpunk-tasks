import pytest
from app import app, db, User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' 
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client

def test_home_page(client):
    """Проверка, что главная открывается"""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Home" in response.data

def test_register(client):
    """Проверка регистрации"""
    response = client.post('/register', data={
        'username': 'testuser',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert User.query.filter_by(username='testuser').first() is not None