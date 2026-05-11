"""Seeds the database with a demo org, project, users, and CSI vocab.

Run with:  python -m scripts.seed
"""

from __future__ import annotations

from passlib.hash import bcrypt

from app.db import SessionLocal
from app.projects.models import Membership, Organization, Project, User
from app.vocabulary.seeders.csi_masterformat import seed as seed_csi


def main() -> None:
    with SessionLocal() as db:
        org = db.query(Organization).filter(Organization.name == "Demo Co").first()
        if org is None:
            org = Organization(name="Demo Co")
            db.add(org)
            db.flush()

        project = (
            db.query(Project)
            .filter(Project.organization_id == org.id, Project.name == "Acme Tower")
            .first()
        )
        if project is None:
            project = Project(organization_id=org.id, name="Acme Tower")
            db.add(project)
            db.flush()

        for email, name, role in [
            ("reviewer@demo", "Reviewer Demo", "reviewer"),
            ("approver@demo", "Approver Demo", "approver"),
            ("uploader@demo", "Uploader Demo", "uploader"),
        ]:
            user = db.query(User).filter(User.email == email).first()
            if user is None:
                user = User(email=email, display_name=name, password_hash=bcrypt.hash("demo"))
                db.add(user)
                db.flush()
            existing_membership = (
                db.query(Membership)
                .filter(
                    Membership.user_id == user.id,
                    Membership.organization_id == org.id,
                    Membership.project_id == project.id,
                    Membership.role == role,
                )
                .first()
            )
            if existing_membership is None:
                db.add(
                    Membership(
                        user_id=user.id,
                        organization_id=org.id,
                        project_id=project.id,
                        role=role,
                    )
                )

        seed_csi(db)
        db.commit()
        print(f"[seed] org={org.name} project={project.name}")
        print("[seed] users: reviewer@demo, approver@demo, uploader@demo (password: demo)")
        print("[seed] vocab: csi_masterformat (2020)")


if __name__ == "__main__":
    main()
