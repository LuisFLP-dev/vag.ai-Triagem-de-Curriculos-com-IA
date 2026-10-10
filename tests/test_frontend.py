"""Integracao HTTP do frontend; execute em processo separado via unittest."""
import os
import unittest
from unittest.mock import patch

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['JWT_SECRET_KEY'] = 'test-frontend-memory-only'
os.environ['GEMINI_API_KEY'] = 'test-no-external-calls'

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database.connection import Base, get_db
from app.database.models import User, UserRole
from app.core.security import hash_password, create_access_token


class FrontendHttpTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.people = {}
        for name, role in [('manager', UserRole.GERENTE_RH), ('recruiter', UserRole.RECRUTADOR), ('candidate', UserRole.CANDIDATO), ('other', UserRole.RECRUTADOR)]:
            person = User(full_name=name, email=f'{name}@example.com', hashed_password='unused', role=role)
            self.db.add(person)
            self.people[name] = person
        self.db.commit()
        def memory_db():
            yield self.db
        app.dependency_overrides[get_db] = memory_db
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        app.dependency_overrides.clear()
        self.db.close()
        self.engine.dispose()

    def headers(self, who):
        return {'Authorization': 'Bearer ' + create_access_token({'sub': str(self.people[who].id)})}

    def test_pages_assets_and_existing_docs(self):
        for path in ['/', '/login', '/cadastro', '/painel', '/frontend/usuarios.html']:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertIn('text/html', response.headers['content-type'])
            self.assertIn('Vag.ai', response.text)
        for path in ['/frontend/js/login.js', '/frontend/js/cadastro.js', '/frontend/js/painel.js', '/frontend/js/usuarios.js', '/frontend/js/admin-ui.js', '/docs']:
            self.assertEqual(self.client.get(path).status_code, 200, path)
        self.assertEqual(self.client.get('/frontend/../database/models.py').status_code, 404)
        self.assertEqual(self.client.get('/static/app.js').status_code, 404)

    def test_registration_login_and_profile(self):
        payload = {'full_name': 'Pessoa teste', 'email': 'new@example.com', 'password': 'PortalTest123!'}
        response = self.client.post('/auth/register', json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()['role'], 'CANDIDATO')
        self.assertNotIn('hashed_password', response.json())
        self.assertEqual(self.client.post('/auth/register', json={**payload, 'email': 'bad@example.com', 'role': 'GERENTE_RH'}).status_code, 422)
        self.assertEqual(self.client.get('/auth/me').status_code, 401)
        self.assertEqual(self.client.post('/auth/login', data={'username': payload['email'], 'password': 'incorrect'}).status_code, 400)
        response = self.client.post('/auth/login', data={'username': payload['email'], 'password': payload['password']})
        self.assertEqual(response.status_code, 200, response.text)
        headers = {'Authorization': 'Bearer ' + response.json()['access_token']}
        response = self.client.get('/auth/me', headers=headers)
        self.assertEqual(response.json()['email'], payload['email'])
        self.assertNotIn('hashed_password', response.json())
        self.assertEqual(self.client.get('/usuarios', headers=headers).status_code, 403)

    def test_live_profile_and_manager_role_assignment(self):
        candidate = self.people['candidate']
        headers = self.headers('candidate')
        url = f'/usuarios/{candidate.id}'
        self.assertEqual(self.client.put(url, headers=headers, json={'role': 'GERENTE_RH'}).status_code, 403)
        self.assertEqual(self.client.put(url, headers=self.headers('recruiter'), json={'role': 'GERENTE_RH'}).status_code, 403)
        self.assertEqual(self.client.put(url, headers=self.headers('manager'), json={'role': 'RECRUTADOR'}).status_code, 200)
        self.assertEqual(self.client.get('/auth/me', headers=headers).json()['role'], 'RECRUTADOR')

    def test_job_application_and_recruiter_decision(self):
        response = self.client.post('/vagas', headers=self.headers('manager'), json={'title': 'Backend', 'description': 'API Python', 'requirements': ['Python'], 'recruiter_id': self.people['recruiter'].id})
        self.assertEqual(response.status_code, 201, response.text)
        job_id = response.json()['id']
        self.assertEqual(len(self.client.get('/vagas').json()), 1)
        with patch('app.modules.candidaturas.service.evaluate_resume_with_gemini', return_value={'score': 85, 'reasoning': 'Teste simulado'}) as ai:
            response = self.client.post(f'/vagas/{job_id}/candidatar', headers=self.headers('candidate'), files={'file': ('cv.pdf', b'%PDF-test', 'application/pdf')})
            self.assertEqual(response.status_code, 200, response.text)
            ai.assert_called_once()
        mine = self.client.get('/minhas-candidaturas', headers=self.headers('candidate')).json()
        self.assertEqual(mine[0]['vaga_id'], job_id)
        self.assertEqual(self.client.get(f'/vagas/{job_id}/candidatos', headers=self.headers('other')).status_code, 403)
        response = self.client.get(f'/vagas/{job_id}/candidatos', headers=self.headers('recruiter'))
        application_id = response.json()[0]['candidatura_id']
        response = self.client.patch(f'/candidaturas/{application_id}/status', headers=self.headers('recruiter'), json={'status': 'CONTRATADO'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get('/minhas-candidaturas', headers=self.headers('candidate')).json()[0]['status_candidatura'], 'CONTRATADO')


if __name__ == '__main__':
    unittest.main()
