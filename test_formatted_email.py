import os
os.environ['FLASK_ENV'] = 'testing'
from app import app, db, Card, User, UserExercise
from datetime import datetime
import random

def send_test_email():
    # Configure server settings for URL generation
    app.config['SERVER_NAME'] = '127.0.0.1:8080'
    app.config['PREFERRED_URL_SCHEME'] = 'http'
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Get or create test user
        user = User.query.filter_by(email='jwinroadto10x@gmail.com').first()
        if not user:
            user = User(
                email='jwinroadto10x@gmail.com',
                learning_direction='ja-en',
                subscribed=True,
                created_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
        
        # Create a more advanced test card if it doesn't exist
        test_card = Card.query.filter_by(front="昨日の会議で提案された新しいプロジェクトは、予算と人員の面で多くの課題があるため、実現するには慎重な計画が必要です。").first()
        if not test_card:
            test_card = Card(
                front="昨日の会議で提案された新しいプロジェクトは、予算と人員の面で多くの課題があるため、実現するには慎重な計画が必要です。",
                back="The new project proposed at yesterday's meeting faces many challenges in terms of budget and personnel, so careful planning is necessary for its realization.",
                option_1="The project was completed quickly because there were no budget or personnel issues.",
                option_2="The meeting was canceled due to budget constraints.",
                option_3="The new project proposed at yesterday's meeting faces many challenges in terms of budget and personnel, so careful planning is necessary for its realization.",
                option_4="The new project will start next week without any problems.",
                correct_option=3,
                front_language="ja",
                back_language="en",
                created_at=datetime.utcnow()
            )
            db.session.add(test_card)
            db.session.commit()
            print("Test card created successfully!")
        
        # Send the email
        from app import send_daily_exercise
        success = send_daily_exercise(user, test_card)
        
        if success:
            app.logger.info(f"Daily exercise email sent to {user.email}")
            print(f"Formatted test email sent successfully! Card ID: {test_card.id}")
        else:
            print("Failed to send formatted test email.")

if __name__ == '__main__':
    send_test_email() 