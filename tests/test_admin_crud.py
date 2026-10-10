"""Gestão administrativa em SQLite em memória, sem rede ou banco real."""
import os
import unittest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "isolated-admin-tests"
os.environ["GEMINI_API_KEY"] = "no-network"

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.connection import Base
from app.database.models import User, UserRole, Application, JobOpening
from app.core.security import verify_password
from app.modules.usuarios import service as users
from app.modules.usuarios.schemas import UserCreate, UserUpdate, UserResponse
from app.modules.usuarios.router import router as users_router
from app.modules.vagas import service as jobs
from app.modules.vagas.schemas import JobCreate, JobUpdate
from app.modules.vagas.router import router as jobs_router


class AdminCrudTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.manager = User(email="manager@example.com", full_name="Manager",
                            hashed_password="unused", role=UserRole.GERENTE_RH)
        self.db.add(self.manager)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def create_user(self, role="RECRUTADOR", email="recruiter@example.com"):
        return users.create_user(UserCreate(full_name="Nome", email=email,
                                 password="Senha123!", role=role), self.db, self.manager)

    def error(self, status, function, *args):
        with self.assertRaises(HTTPException) as raised:
            function(*args)
        self.assertEqual(raised.exception.status_code, status)

    def test_user_crud_and_duplicate_email(self):
        user = self.create_user()
        user_id = user.id
        self.assertNotIn("hashed_password", UserResponse.model_validate(user).model_dump())
        self.assertTrue(verify_password("Senha123!", user.hashed_password))
        self.error(400, self.create_user)
        updated = users.update_user(user_id, UserUpdate(full_name="Novo", role="CANDIDATO"), self.db, self.manager)
        self.assertEqual(updated.full_name, "Novo")
        self.assertTrue(verify_password("Senha123!", updated.hashed_password))
        users.delete_user(user_id, self.db, self.manager)
        self.error(404, users.get_user, user_id, self.db, self.manager)

    def test_job_crud_and_relationship_protection(self):
        recruiter = self.create_user()
        job = jobs.create_job(JobCreate(title="Python", description="Backend",
                              requirements=["Python"], recruiter_id=recruiter.id), self.db, self.manager)
        self.error(409, users.delete_user, recruiter.id, self.db, self.manager)
        self.error(409, users.update_user, recruiter.id, UserUpdate(role="CANDIDATO"), self.db, self.manager)
        candidate = self.create_user("CANDIDATO", "candidate@example.com")
        self.db.add(Application(job_id=job.id, candidate_id=candidate.id,
                                compatibility_score=50, ai_feedback="Mock"))
        self.db.commit()
        self.error(409, users.delete_user, candidate.id, self.db, self.manager)
        updated = jobs.update_job(job.id, JobUpdate(title="Senior", status="CONCLUIDA"), self.db, self.manager)
        self.assertEqual(updated.status, "CONCLUIDA")
        jobs.delete_job(job.id, self.db, self.manager)
        self.assertEqual(self.db.query(Application).count(), 0)
        self.assertEqual(self.db.query(JobOpening).count(), 0)
        users.delete_user(recruiter.id, self.db, self.manager)

    def test_role_permissions_and_self_protection(self):
        self.error(400, users.delete_user, self.manager.id, self.db, self.manager)
        self.error(400, users.update_user, self.manager.id, UserUpdate(role="CANDIDATO"), self.db, self.manager)
        checked = 0
        for router in (users_router, jobs_router):
            for route in router.routes:
                if not route.methods.intersection({"POST", "PUT", "DELETE"}):
                    continue
                guard = next(dep.call for dep in route.dependant.dependencies if dep.name == "current_user")
                self.assertIs(guard(self.manager), self.manager)
                for role in (UserRole.CANDIDATO, UserRole.RECRUTADOR):
                    self.error(403, guard, User(id=99, role=role))
                checked += 1
        self.assertEqual(checked, 6)


if __name__ == "__main__":
    unittest.main()
