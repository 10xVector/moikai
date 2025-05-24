from app import app, db, mail, User, Card
from flask_mail import Message
from datetime import datetime
import random

def send_daily_emails():
    with app.app_context():
        # Get all subscribed users
        users = User.query.filter_by(subscribed=True).all()
        
        for user in users:
            # Get a card for the user's language preference
            card = Card.query.filter_by(front_language=user.language_preference).order_by(db.func.random()).first()
            if card:
                # Create email message
                msg = Message(
                    'Your Daily Moikai Practice',
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[user.email]
                )
                
                # Create email body with HTML
                msg.html = f'''
                <html>
                    <body>
                        <h2>Daily {user.language_preference.capitalize()} Practice</h2>
                        <p>{card.front}</p>
                        <p>Click the link below to answer the comprehension question:</p>
                        <a href="{app.config['BASE_URL']}/practice/{card.id}">Start Practice</a>
                    </body>
                </html>
                '''
                
                # Send email
                mail.send(msg)

if __name__ == '__main__':
    send_daily_emails() 