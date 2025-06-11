import os
from sqlalchemy.orm import sessionmaker
from db.models import File, db
from utils.logging import logger, log_call
from utils.pinecone_client import PineconeClient

class SessionCleanup:
    """
    Cleanup helper — deletes DB rows and Pinecone vectors for a session.
    """
    def __init__(self, session):
        self.session = session
        self.SessionLocal = sessionmaker(bind=db.engine)

    @log_call()
    def run(self):
        logger.info("Starting cleanup for session %s", self.session.session_id)
        items = self.session.file_items
        if not items:
            logger.info("No file items to clean for session %s", self.session.session_id)
            return

        ids = []
        paths = []
        for x in items:
            if isinstance(x, int):
                ids.append(x)
            elif isinstance(x, dict) and "id" in x:
                ids.append(x["id"])
            elif isinstance(x, str):
                paths.append(x)

        if paths and not ids:
            db_sess = self.SessionLocal()
            files = db_sess.query(File).filter(File.file_path.in_(paths)).all()
            ids = [f.id for f in files]
            db_sess.close()
            logger.debug("Resolved %d DB IDs from file paths", len(ids))

        if not ids:
            logger.warning(
                "Nothing to delete from Pinecone / DB for session %s",
                self.session.session_id,
            )
            return

        # Delete vectors from Pinecone
        try:
            namespace = os.getenv("PINECONE_NAMESPACE", "default-namespace")
            PineconeClient().delete(ids=[str(i) for i in ids], namespace=namespace)
            logger.info(
                "Deleted %d vectors from Pinecone (namespace=%s)", len(ids), namespace
            )
        except Exception as e:
            logger.exception("Pinecone deletion error: %s", e)

        # Delete rows from DB
        db_sess = self.SessionLocal()
        try:
            db_sess.query(File).filter(File.id.in_(ids)).delete(synchronize_session=False)
            db_sess.commit()
            logger.info("Deleted %d rows from DB", len(ids))
        except Exception as e:
            db_sess.rollback()
            logger.exception("DB deletion error: %s", e)
        finally:
            db_sess.close()
