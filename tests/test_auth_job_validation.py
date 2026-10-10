"""Regressões de autenticação e validação; usa somente SQLite em memória."""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "isolated-validation-tests"
os.environ["GEMINI_API_KEY"] = "no-network"

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.connection import Base
from app.database.models import User, UserRole
from app.core.security import create_access_token, get_current_user, require_roles
from app.modules.auth import service as auth
from app.modules.vagas.schemas import JobCreate, JobUpdate


class AuthJobValidationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.user = User(email="original@example.com", full_name="Candidato",
                         role=UserRole.CANDIDATO, hashed_password="test-hash")
        self.db.add(self.user)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_login_token_stays_with_original_account_after_email_reuse(self):
        with patch.object(auth, "verify_password", return_value=True):
            token = auth.login(SimpleNamespace(username=self.user.email, password="test"), self.db)["access_token"]
        original_id = self.user.id
        original_email = self.user.email
        self.user.email = "changed@example.com"
        self.db.add(User(email=original_email, full_name="Outra conta",
                         role=UserRole.GERENTE_RH, hashed_password="other-hash"))
        self.db.commit()
        resolved = get_current_user(token, self.db)
        self.assertEqual(resolved.id, original_id)
        self.assertEqual(resolved.role, UserRole.CANDIDATO)
        with self.assertRaises(HTTPException) as raised:
            require_roles([UserRole.GERENTE_RH])(resolved)
        self.assertEqual(raised.exception.status_code, 403)

    def test_legacy_and_invalid_subjects_rejected(self):
        for subject in [self.user.email, None, "", "0", "-1", "1.5", "9" * 100, "9223372036854775808"]:
            with self.subTest(subject=subject):
                token = create_access_token({"sub": subject})
                with self.assertRaises(HTTPException) as raised:
                    get_current_user(token, self.db)
                self.assertEqual(raised.exception.status_code, 401)

    def test_deleted_user_token_rejected(self):
        token = create_access_token({"sub": str(self.user.id)})
        self.db.delete(self.user)
        self.db.commit()
        with self.assertRaises(HTTPException) as raised:
            get_current_user(token, self.db)
        self.assertEqual(raised.exception.status_code, 401)

    def test_current_database_role_is_used(self):
        token = create_access_token({"sub": str(self.user.id), "role": "GERENTE_RH"})
        self.assertEqual(get_current_user(token, self.db).role, UserRole.CANDIDATO)
        self.user.role = UserRole.RECRUTADOR
        self.db.commit()
        self.assertEqual(get_current_user(token, self.db).role, UserRole.RECRUTADOR)

    def test_blank_job_fields_rejected_on_create_and_update(self):
        valid = dict(title="Python", description="Backend", requirements=["Python"], recruiter_id=1)
        for invalid in [{"title": ""}, {"title": "  "}, {"description": "\n"},
                        {"requirements": []}, {"requirements": [" "]}, {"requirements": ["Python", ""]}]:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValidationError):
                    JobCreate(**{**valid, **invalid})
                with self.assertRaises(ValidationError):
                    JobUpdate(**invalid)

    def test_normalization_and_partial_updates_preserved(self):
        job = JobCreate(title=" Python ", description=" Backend ", requirements=[" SQL "], recruiter_id=1)
        self.assertEqual((job.title, job.description, job.requirements), ("Python", "Backend", ["SQL"]))
        self.assertEqual(JobUpdate(status="CONCLUIDA").model_dump(exclude_unset=True), {"status": "CONCLUIDA"})
        self.assertEqual(JobUpdate().model_dump(exclude_unset=True), {})


if __name__ == "__main__":
    unittest.main()
