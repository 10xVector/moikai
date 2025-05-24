from app import app, db
from models import User, Card
from datetime import datetime, timedelta
import json
import random
from sqlalchemy import func

# Sample categories and grammar points for Japanese
JAPANESE_CATEGORIES = [
    'Greetings', 'Numbers', 'Food', 'Travel', 'Shopping',
    'Family', 'Time', 'Weather', 'Directions', 'Hobbies',
    'Work', 'School', 'Health', 'Transportation', 'Entertainment'
]

JAPANESE_GRAMMAR_POINTS = [
    'は (wa) particle', 'が (ga) particle', 'を (wo) particle',
    'に (ni) particle', 'で (de) particle', 'へ (e) particle',
    'て-form', 'た-form', 'ない-form', 'ます-form',
    'い-adjectives', 'な-adjectives', 'Potential form',
    'Conditional form', 'Passive form', 'Causative form'
]

# Sample exercises (you would replace this with AI-generated content)
SAMPLE_EXERCISES = [
    {
        'language': 'Japanese',
        'difficulty': 'beginner',
        'category': 'Greetings',
        'grammar_point': 'は (wa) particle',
        'paragraph': 'What is the Japanese word for "hello"?',
        'correct_answer': 'こんにちは',
        'explanation': 'こんにちは (konnichiwa) is the standard greeting for "hello" in Japanese.',
        'options': ['こんにちは', 'さようなら', 'ありがとう', 'おはよう'],
        'romaji': ['konnichiwa', 'sayonara', 'arigatou', 'ohayou'],
        'english_translation': 'What is the Japanese word for "hello"?'
    },
    {
        'language': 'Japanese',
        'difficulty': 'beginner',
        'category': 'Numbers',
        'grammar_point': 'Numbers',
        'paragraph': 'How do you say "one" in Japanese?',
        'correct_answer': 'いち',
        'explanation': 'いち (ichi) is the Japanese word for "one".',
        'options': ['いち', 'に', 'さん', 'よん'],
        'romaji': ['ichi', 'ni', 'san', 'yon'],
        'english_translation': 'How do you say "one" in Japanese?'
    }
]

real_exercises = [
    {
        "paragraph": "What is the Japanese word for 'apple'?",
        "options": ["りんご", "みかん", "バナナ", "ぶどう"],
        "correct_answer": "りんご",
        "explanation": "りんご (ringo) means 'apple' in Japanese.",
        "category": "Food",
        "difficulty": "beginner",
        "grammar_point": "Vocabulary"
    },
    {
        "paragraph": "How do you say 'Good morning' in Japanese?",
        "options": ["おはよう", "こんばんは", "こんにちは", "さようなら"],
        "correct_answer": "おはよう",
        "explanation": "おはよう (ohayou) means 'Good morning'.",
        "category": "Greetings",
        "difficulty": "beginner",
        "grammar_point": "Greetings"
    },
    # Add more questions here...
]

class ExercisePool:
    MIN_POOL_SIZE = 200  # Minimum number of exercises to maintain
    BATCH_SIZE = 20      # Number of exercises to generate per API call
    
    @classmethod
    def check_pool_status(cls):
        """Check if we need to generate more exercises."""
        with app.app_context():
            # Count available cards
            total_cards = Card.query.count()
            # Count how many cards were used in the last week (approximation)
            week_ago = datetime.utcnow() - timedelta(days=7)
            weekly_usage = User.query.filter(User.subscribed == True).count() * 7
            # Calculate cards needed
            cards_needed = max(0, cls.MIN_POOL_SIZE - (total_cards - weekly_usage))
            if cards_needed > 0:
                print(f"Pool running low. Generate more cards as needed!")
            else:
                print(f"Pool status healthy. {total_cards} cards available.")
            return cards_needed == 0

    @classmethod
    def get_exercise_for_user(cls, user):
        """Get an appropriate card for a user."""
        with app.app_context():
            # Get cards the user hasn't seen yet (approximation)
            # In production, you'd have a UserExercises table to track this
            # For now, match by learning_direction (e.g., 'ja-en', 'en-ja')
            direction = user.learning_direction
            if direction == 'ja-en':
                card = Card.query.filter_by(front_language='ja', back_language='en').order_by(func.random()).first()
            elif direction == 'en-ja':
                card = Card.query.filter_by(front_language='en', back_language='ja').order_by(func.random()).first()
            else:
                card = None
            # Check pool status after selecting a card
            cls.check_pool_status()
            return card

def generate_exercises():
    """Generate and add exercises to the database."""
    with app.app_context():
        try:
            # Clear existing exercises
            Card.query.delete()
            db.session.commit()
            
            # Add sample exercises
            for i, exercise_data in enumerate(SAMPLE_EXERCISES, 1):
                exercise = Card(
                    id=i,
                    date=datetime.utcnow(),
                    **exercise_data
                )
                db.session.add(exercise)
            
            db.session.commit()
            print(f"Added {len(SAMPLE_EXERCISES)} exercises successfully!")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()

def generate_ai_exercises(batch_size=20, total_exercises=1000):
    """Generate exercises in batches to optimize API usage and costs."""
    with app.app_context():
        try:
            current_count = Card.query.count()
            if current_count >= total_exercises:
                print(f"Already have {current_count} exercises. No need to generate more.")
                return
            
            exercises_needed = total_exercises - current_count
            batches_needed = (exercises_needed + batch_size - 1) // batch_size
            
            print(f"Generating {exercises_needed} exercises in {batches_needed} batches...")
            
            for batch in range(batches_needed):
                new_exercises = generate_batch(batch_size)
                
                for exercise_data in new_exercises:
                    exercise = Card(
                        date=datetime.utcnow(),
                        **exercise_data
                    )
                    db.session.add(exercise)
                
                db.session.commit()
                print(f"Batch {batch + 1}/{batches_needed} completed")
            
            final_count = Card.query.count()
            print(f"Successfully generated exercises. Total count: {final_count}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()

def generate_batch(size):
    """
    Generate a batch of exercises. In production, this would use an AI API.
    For now, it generates variations of sample exercises.
    """
    exercises = []
    for i in range(size):
        # Randomly select category and grammar point
        category = random.choice(JAPANESE_CATEGORIES)
        grammar = random.choice(JAPANESE_GRAMMAR_POINTS)
        
        # Create exercise with different variations
        exercise = {
            'language': 'Japanese',
            'difficulty': random.choice(['beginner', 'intermediate', 'advanced']),
            'category': category,
            'grammar_point': grammar,
            'paragraph': f'Practice question for {category} using {grammar}',
            'correct_answer': 'Sample Answer',
            'explanation': f'This is an explanation for {category} and {grammar}',
            'options': ['Sample Answer', 'Option 2', 'Option 3', 'Option 4'],
            'romaji': ['sample', 'option2', 'option3', 'option4'],
            'english_translation': f'English version of the {category} question'
        }
        exercises.append(exercise)
    
    return exercises

def generate_real_exercises():
    db.session.query(Card).delete()  # Clear old exercises
    for ex in real_exercises:
        exercise = Card(
            date=datetime.utcnow(),
            language='Japanese',
            paragraph=ex["paragraph"],
            correct_answer=ex["correct_answer"],
            explanation=ex["explanation"],
            options=ex["options"],
            category=ex["category"],
            difficulty=ex["difficulty"],
            grammar_point=ex["grammar_point"]
        )
        db.session.add(exercise)
    db.session.commit()
    print(f"Added {len(real_exercises)} real exercises.")

if __name__ == '__main__':
    # Check pool status and generate exercises if needed
    ExercisePool.check_pool_status()
    generate_real_exercises() 