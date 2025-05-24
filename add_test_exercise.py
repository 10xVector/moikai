from app import app, db
from datetime import datetime

def add_test_exercise():
    with app.app_context():
        try:
            # Check if exercise already exists
            existing = DailyExercise.query.filter_by(id=1).first()
            if existing:
                print("Test exercise already exists!")
                return

            # Create the test exercise
            test_exercise = DailyExercise(
                id=1,
                date=datetime.utcnow(),
                language='Japanese',
                paragraph='What is the Japanese word for "hello"?',
                correct_answer='こんにちは',
                explanation='こんにちは (konnichiwa) is the standard greeting for "hello" in Japanese.',
                options=['こんにちは', 'さようなら', 'ありがとう', 'おはよう']
            )
            
            # Add to database
            db.session.add(test_exercise)
            db.session.commit()
            print("Test exercise added successfully!")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    add_test_exercise() 