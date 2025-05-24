from app import app, db, Card, User, UserExercise
from datetime import datetime
import random

def send_test_email():
    # Configure server settings for URL generation
    app.config['SERVER_NAME'] = '127.0.0.1:8080'
    app.config['PREFERRED_URL_SCHEME'] = 'http'
    
    with app.app_context():
        # Get or create test user
        user = User.query.filter_by(email='thehtjohn@gmail.com').first()
        if not user:
            user = User(
                email='thehtjohn@gmail.com',
                learning_direction='ja-en',
                subscribed=True,
                created_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
        
        # Get cards the user hasn't completed yet
        completed_card_ids = [ue.card_id for ue in UserExercise.query.filter_by(user_id=user.id).all()]
        direction = user.learning_direction
        if direction == 'ja-en':
            available_cards = Card.query.filter(~Card.id.in_(completed_card_ids), Card.front_language=='ja', Card.back_language=='en').all()
        elif direction == 'en-ja':
            available_cards = Card.query.filter(~Card.id.in_(completed_card_ids), Card.front_language=='en', Card.back_language=='ja').all()
        else:
            available_cards = []
        
        if not available_cards:
            print("No new cards available! All cards have been sent.")
            return
            
        # Pick a random card from available ones
        card = random.choice(available_cards)
        
        # Send the email
        from app import send_daily_exercise
        success = send_daily_exercise(user, card)
        
        if success:
            app.logger.info(f"Daily exercise email sent to {user.email}")
            print(f"Formatted test email sent successfully! Card ID: {card.id}")
        else:
            print("Failed to send formatted test email.")

if __name__ == '__main__':
    send_test_email() 