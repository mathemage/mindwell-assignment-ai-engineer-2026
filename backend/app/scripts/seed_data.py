"""Seed database with sample data."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.logging import get_logger, setup_logging
from app.core.security import hash_password, pseudonymize_user_id
from app.db.models import User
from app.db.session import SessionLocal
from app.services.document_service import DocumentService

setup_logging()
logger = get_logger(__name__)

# Sample CBT content
CBT_INTRO = """# Introduction to Cognitive Behavioral Therapy (CBT)

## What is CBT?

Cognitive Behavioral Therapy (CBT) is a form of psychological treatment that has been demonstrated to be effective for a range of problems including depression, anxiety disorders, alcohol and drug use problems, marital problems, eating disorders, and severe mental illness.

## Core Principles

CBT is based on several core principles:

1. **Psychological problems are based, in part, on faulty or unhelpful ways of thinking.**
2. **Psychological problems are based, in part, on learned patterns of unhelpful behavior.**
3. **People suffering from psychological problems can learn better ways of coping with them, thereby relieving their symptoms and becoming more effective in their lives.**

## How CBT Works

CBT treatment usually involves efforts to change thinking patterns and behavioral patterns.

### Changing Thinking Patterns

These strategies might include:
- Learning to recognize one's distortions in thinking that are creating problems
- Gaining a better understanding of the behavior and motivation of others
- Using problem-solving skills to cope with difficult situations
- Learning to develop a greater sense of confidence in one's own abilities

### Changing Behavioral Patterns

These strategies might include:
- Facing one's fears instead of avoiding them
- Using role playing to prepare for potentially problematic interactions with others
- Learning to calm one's mind and relax one's body
"""

COGNITIVE_DISTORTIONS = """# Common Cognitive Distortions

## What are Cognitive Distortions?

Cognitive distortions are irrational thoughts that can influence your emotions. Everyone experiences cognitive distortions to some degree, but in their more extreme forms they can be harmful.

## Common Types

### 1. All-or-Nothing Thinking

Seeing things in black and white categories. If a situation falls short of perfect, you see it as a total failure.

**Example:** "If I'm not perfect, I'm a failure."

### 2. Overgeneralization

Seeing a single negative event as a never-ending pattern of defeat.

**Example:** "This always happens to me" or "I never get anything right."

### 3. Mental Filter

Picking out a single negative detail and dwelling on it exclusively.

**Example:** Focusing only on the one criticism in a performance review that was otherwise positive.

### 4. Catastrophizing

Expecting disaster to strike, no matter what. Also known as "magnifying" or "minimizing."

**Example:** "If I fail this test, my life is over."

### 5. Emotional Reasoning

Assuming that negative emotions necessarily reflect the way things really are.

**Example:** "I feel inadequate, therefore I must be a worthless person."

## How to Challenge Cognitive Distortions

1. **Identify the distortion:** Recognize which type of cognitive distortion you're experiencing
2. **Examine the evidence:** Look for facts that support or contradict your thought
3. **Consider alternatives:** Think of other ways to interpret the situation
4. **Practice balanced thinking:** Replace distorted thoughts with more realistic ones
"""

COPING_STRATEGIES = """# Coping Strategies and Techniques

## Stress Management

### Deep Breathing

Deep breathing is one of the best ways to lower stress in the body. When you breathe deeply, it sends a message to your brain to calm down and relax.

**How to practice:**
1. Sit or lie down in a comfortable position
2. Place one hand on your belly
3. Breathe in slowly through your nose, feeling your belly rise
4. Breathe out slowly through your mouth
5. Repeat for 5-10 minutes

### Progressive Muscle Relaxation

This technique involves tensing and then relaxing different muscle groups in your body.

**Steps:**
1. Find a quiet place to sit or lie down
2. Starting with your feet, tense the muscles for 5 seconds
3. Release and notice the difference for 10 seconds
4. Move up your body, tensing and releasing each muscle group

## Thought Records

Thought records help you identify and challenge negative thoughts.

**Components:**
1. **Situation:** What happened?
2. **Thoughts:** What went through your mind?
3. **Emotions:** What did you feel?
4. **Evidence For:** What supports this thought?
5. **Evidence Against:** What contradicts this thought?
6. **Alternative Thought:** What's a more balanced perspective?

## Behavioral Activation

When feeling depressed, it's important to engage in activities that provide a sense of accomplishment or pleasure.

**Guidelines:**
- Start small with manageable activities
- Schedule pleasant activities daily
- Track your mood before and after activities
- Gradually increase activity level

## Grounding Techniques

Grounding techniques help when you feel overwhelmed or anxious.

**5-4-3-2-1 Technique:**
- Name 5 things you can see
- Name 4 things you can touch
- Name 3 things you can hear
- Name 2 things you can smell
- Name 1 thing you can taste
"""


def seed_database() -> None:
    """Seed the database with sample data."""
    logger.info("Starting database seeding")
    
    settings = get_settings()
    
    # Prevent creating test accounts in production
    if settings.is_production:
        logger.error("Refusing to seed test accounts in production environment")
        raise RuntimeError(
            "Test accounts cannot be created in production. "
            "Set ENVIRONMENT=development or ENVIRONMENT=staging to run seed script."
        )

    db = SessionLocal()

    try:
        # Create admin user
        admin = db.query(User).filter(User.email == "admin@mindwell.ai").first()
        if not admin:
            logger.warning(
                "Creating test admin account with weak password - DO NOT USE IN PRODUCTION",
                email="admin@mindwell.ai"
            )
            admin = User(
                email="admin@mindwell.ai",
                hashed_password=hash_password("admin123456"),
                pseudonym_id=pseudonymize_user_id("admin@mindwell.ai"),
                is_admin=1,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            logger.info("Admin user created", user_id=admin.id)
        else:
            logger.info("Admin user already exists")

        # Create test user
        user = db.query(User).filter(User.email == "user@example.com").first()
        if not user:
            logger.warning(
                "Creating test user account with weak password - DO NOT USE IN PRODUCTION",
                email="user@example.com"
            )
            user = User(
                email="user@example.com",
                hashed_password=hash_password("password123"),
                pseudonym_id=pseudonymize_user_id("user@example.com"),
                is_admin=0,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("Test user created", user_id=user.id)
        else:
            logger.info("Test user already exists")

        # Create sample documents
        doc_service = DocumentService(db)

        documents = [
            ("Introduction to CBT", CBT_INTRO, "markdown"),
            ("Cognitive Distortions", COGNITIVE_DISTORTIONS, "markdown"),
            ("Coping Strategies", COPING_STRATEGIES, "markdown"),
        ]

        for title, content, source_type in documents:
            # Check if document already exists
            from app.db.models import Document

            existing = db.query(Document).filter(Document.title == title).first()
            if not existing:
                doc_service.process_document(title, content, source_type)
                logger.info("Document created", title=title)
            else:
                logger.info("Document already exists", title=title)

        logger.info("Database seeding complete")

    except Exception as e:
        logger.error("Database seeding failed", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
