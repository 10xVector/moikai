# Moikai

A web application that sends daily language practice exercises via email. Users can subscribe to receive either English or Japanese practice exercises, complete with comprehension questions and explanations.

## Features

- Daily email delivery of language practice exercises
- Support for both English and Japanese practice
- Multiple choice comprehension questions
- Immediate feedback and explanations
- Clean, modern UI with Tailwind CSS
- Email subscription management

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd daily-language-practice
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following variables:
```
SECRET_KEY=your-secret-key
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password
BASE_URL=http://your-domain.com
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

6. Run the application:
```bash
python app.py
```

## Setting up Daily Emails

To send daily practice emails, you'll need to set up a cron job or scheduled task to run the `send_daily_emails.py` script daily:

```bash
# Example cron job (runs at 8 AM daily)
0 8 * * * /path/to/venv/bin/python /path/to/send_daily_emails.py
```

## Adding Practice Exercises

You can add new practice exercises through the Flask shell:

```python
from app import app, db, DailyExercise
from datetime import datetime

with app.app_context():
    exercise = DailyExercise(
        language='english',  # or 'japanese'
        paragraph='Your practice paragraph here',
        correct_answer='A',  # or 'B', 'C', 'D'
        explanation='Detailed explanation of the correct answer'
    )
    db.session.add(exercise)
    db.session.commit()
```

## Manually Adding Real Questions and Answers

If you want to manually add real Japanese language questions and answers to your database, follow these steps:

### 1. Edit `generate_exercises.py`

Replace the dummy/sample data with a list of real exercises. For example:

```python
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

from app import db
from models import DailyExercise
from datetime import datetime

def generate_real_exercises():
    db.session.query(DailyExercise).delete()  # Clear old exercises
    for ex in real_exercises:
        exercise = DailyExercise(
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

if __name__ == "__main__":
    generate_real_exercises()

### 2. Reset and Populate the Database

1. Delete the old database (optional, for a clean start):
   ```sh
   rm -f instance/language_practice.db
   ```
2. Re-run migrations:
   ```sh
   flask db upgrade
   ```
3. Run your updated script:
   ```sh
   python generate_exercises.py
   ```

### 3. Test

Send yourself a test email or use the app to verify that real questions and answers appear.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 