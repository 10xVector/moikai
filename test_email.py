from app import app, mail
from flask_mail import Message

def test_email():
    with app.app_context():
        try:
            msg = Message('Test Email',
                         recipients=[app.config['MAIL_USERNAME']])
            msg.body = 'This is a test email from your Language Practice app!'
            mail.send(msg)
            print("Test email sent successfully!")
        except Exception as e:
            print(f"Failed to send email: {str(e)}")

if __name__ == '__main__':
    test_email() 