"""Regressao dos servicos com SQLite exclusivamente em memoria."""
import os
import unittest
from io import BytesIO
from unittest.mock import patch
from types import SimpleNamespace

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['JWT_SECRET_KEY'] = 'test-only-isolated-process'
os.environ['GEMINI_API_KEY'] = 'test-only-no-network'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers
from app.database.connection import Base
from app.database.models import User, UserRole, Application, ApplicationStatus
from app.modules.auth import service as auth
from app.modules.usuarios import service as users
from app.modules.vagas import service as jobs
from app.modules.candidaturas import service as applications
from app.modules.usuarios.schemas import UserCreate, UserUpdate
from app.modules.auth.schemas import RegisterRequest
from pydantic import ValidationError
from app.modules.vagas.schemas import JobCreate, JobUpdate
from app.modules.candidaturas.schemas import ApplicationStatusUpdate
from app.core.security import require_roles, get_current_user


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.users = {}
        for name, role in [('manager', UserRole.GERENTE_RH), ('recruiter', UserRole.RECRUTADOR), ('other', UserRole.RECRUTADOR), ('candidate', UserRole.CANDIDATO)]:
            user = User(email=f'{name}@example.com', full_name=name, hashed_password='unused', role=role)
            self.db.add(user)
            self.users[name] = user
        self.db.commit()
        self.manager = self.users['manager']
        self.candidate = self.users['candidate']
        self.ai = patch('app.modules.candidaturas.service.evaluate_resume_with_gemini', return_value={'score': 82.5, 'reasoning': 'Simulado'})
        self.ai_mock = self.ai.start()

    def tearDown(self):
        self.ai.stop()
        self.db.close()
        self.engine.dispose()

    def error(self, status, function, *args, **kwargs):
        with self.assertRaises(HTTPException) as raised:
            function(*args, **kwargs)
        self.assertEqual(raised.exception.status_code, status)

    def job(self):
        return jobs.create_job(JobCreate(title='Python', description='Backend', requirements=['Python'], recruiter_id=self.users['recruiter'].id), self.db, self.manager)

    def apply(self, job_id, mime='application/pdf'):
        file = UploadFile(filename='cv.pdf', file=BytesIO(b'%PDF-test'), headers=Headers({'content-type': mime}))
        return applications.apply_to_job(job_id, file, self.db, self.candidate)

    def test_user_crud_and_permissions(self):
        self.error(403, require_roles([UserRole.GERENTE_RH]), self.candidate)
        self.assertIs(require_roles([UserRole.GERENTE_RH])(self.manager), self.manager)
        self.assertEqual(len(users.list_users(self.db, self.manager)), 4)
        self.assertEqual(users.update_user(self.candidate.id, UserUpdate(full_name='Novo nome'), self.db, self.manager).full_name, 'Novo nome')
        self.error(400, users.delete_user, self.manager.id, self.db, self.manager)
        user_id = self.candidate.id
        users.delete_user(user_id, self.db, self.manager)
        self.error(404, users.get_user, user_id, self.db, self.manager)

    def test_job_crud_and_validation(self):
        job = self.job()
        self.assertEqual(len(jobs.list_jobs(self.db)), 1)
        self.assertEqual(jobs.get_job(job.id, self.db).title, 'Python')
        self.assertEqual(jobs.update_job(job.id, JobUpdate(title='Senior'), self.db, self.manager).title, 'Senior')
        with self.assertRaises(ValidationError):
            JobCreate(title='X', description='Y', requirements=[], recruiter_id=self.users['recruiter'].id)
        job_id = job.id
        jobs.delete_job(job_id, self.db, self.manager)
        self.error(404, jobs.get_job, job_id, self.db)

    def test_application_decision_ownership_and_duplicate(self):
        job = self.job()
        self.assertEqual(self.apply(job.id), {'message': 'Candidatura realizada com sucesso!'})
        self.ai_mock.assert_called_once_with(b'%PDF-test', ['Python'])
        self.assertEqual(applications.list_my_applications(self.db, self.candidate)[0]['vaga_id'], job.id)
        self.error(403, applications.get_job_candidates, job.id, self.db, self.users['other'])
        result = applications.get_job_candidates(job.id, self.db, self.users['recruiter'])
        self.assertEqual(result[0]['pontuacao_compatibilidade'], 82.5)
        self.assertEqual(result[0]['parecer_ia'], 'Simulado')
        application_id = result[0]['candidatura_id']
        rejected = ApplicationStatusUpdate(status='REJEITADO')
        self.error(403, applications.update_application_status, application_id, rejected, self.db, self.users['other'])
        self.error(400, applications.update_application_status, application_id, ApplicationStatusUpdate(status='PENDENTE'), self.db, self.users['recruiter'])
        applications.update_application_status(application_id, rejected, self.db, self.users['recruiter'])
        self.error(400, self.apply, job.id)
        self.db.expire_all()
        self.assertEqual(self.db.query(Application).one().status, ApplicationStatus.REJEITADO)
        self.assertEqual(self.ai_mock.call_count, 1)

    def test_invalid_pdf_closed_and_missing_job(self):
        job = self.job()
        self.error(400, self.apply, job.id, 'text/plain')
        self.error(404, self.apply, 999)
        jobs.update_job(job.id, JobUpdate(status='CONCLUIDA'), self.db, self.manager)
        self.error(400, self.apply, job.id)
        self.ai_mock.assert_not_called()
        self.assertEqual(self.db.query(Application).count(), 0)

    def test_register_login_and_token(self):
        # Hash simulado; geracao e validacao JWT reais, sem chamadas externas.
        with patch.object(auth, 'hash_password', return_value='test-hash'), patch.object(auth, 'verify_password', side_effect=lambda plain, hashed: plain == 'correct' and hashed == 'test-hash'):
            payload = RegisterRequest(email='new@example.com', password='correct', full_name='Novo')
            user = auth.register(payload, self.db)
            self.assertEqual(user.hashed_password, 'test-hash')
            self.assertEqual(user.role, UserRole.CANDIDATO)
            self.error(400, auth.register, payload, self.db)
            self.error(400, auth.login, SimpleNamespace(username=payload.email, password='wrong'), self.db)
            token = auth.login(SimpleNamespace(username=payload.email, password='correct'), self.db)['access_token']
            self.assertEqual(get_current_user(token, self.db).id, user.id)


    def test_public_registration_rejects_role_field(self):
        for role in UserRole:
            with self.subTest(role=role), self.assertRaises(ValidationError) as raised:
                RegisterRequest.model_validate({'email': 'new@example.com', 'password': 'correct', 'full_name': 'Novo', 'role': role.value})
            self.assertEqual(raised.exception.errors()[0]['type'], 'extra_forbidden')

    def test_registration_service_never_grants_privileged_role(self):
        # Mesmo uma chamada interna com o schema antigo nao eleva privilegios.
        with patch.object(auth, 'hash_password', return_value='test-hash'):
            for role in [UserRole.GERENTE_RH, UserRole.RECRUTADOR]:
                with self.subTest(role=role):
                    payload = UserCreate(email=f'{role.value.lower()}@example.com', password='correct', full_name='Novo', role=role)
                    user = auth.register(payload, self.db)
                    self.db.refresh(user)
                    self.assertEqual(user.role, UserRole.CANDIDATO)

    def test_role_management_requires_manager_dependency(self):
        # Exercita a dependencia realmente declarada na rota de atualizacao.
        import inspect
        from app.modules.usuarios.router import update_user
        guard = inspect.signature(update_user).parameters['current_user'].default.dependency
        for name in ['candidate', 'recruiter']:
            self.error(403, guard, self.users[name])
        manager = guard(self.manager)
        for role in [UserRole.RECRUTADOR, UserRole.GERENTE_RH, UserRole.CANDIDATO]:
            result = update_user(self.candidate.id, UserUpdate(role=role), self.db, manager)
            self.db.refresh(result)
            self.assertEqual(result.role, role)


if __name__ == '__main__':
    unittest.main()
