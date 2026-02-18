"""Test configuration fixtures."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    # Use in-memory SQLite for fast tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_markdown_content():
    """Sample markdown content for testing."""
    return """# Introduction to CBT

Cognitive Behavioral Therapy is an evidence-based treatment.

## Key Principles

1. Thoughts affect feelings
2. Behaviors can be changed
3. Skills can be learned

### Techniques

- Thought records
- Behavioral activation
- Exposure therapy
"""


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "pseudonym_id": "abc123def456",
        "is_admin": 0,
    }
