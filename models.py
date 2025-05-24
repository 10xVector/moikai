from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy without a Flask app (yet)
db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255))
    language_preference = db.Column(db.String(20), default='english')
    subscribed = db.Column(db.Boolean, default=True)
    subscription_status = db.Column(db.String(20), default='free')
    subscription_end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    streak_count = db.Column(db.Integer, default=0)
    last_practice_date = db.Column(db.DateTime)
    total_practices = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    incorrect_answers = db.Column(db.Integer, default=0)
    average_score = db.Column(db.Float, default=0.0)
    preferred_practice_time = db.Column(db.String(5), default='08:00')
    timezone = db.Column(db.String(50), default='UTC')
    notification_preferences = db.Column(db.JSON, default={'email': True, 'push': False})
    progress_data = db.Column(db.JSON, default={})
    is_active = db.Column(db.Boolean, default=True)
    stripe_customer_id = db.Column(db.String(120), nullable=True)
    subscription_plan = db.Column(db.String(20), default='free')
    payment_history = db.Column(db.JSON, default=[])
    learning_direction = db.Column(db.String(10), default='ja-en')
    
    # Subscription related fields
    subscription_start = db.Column(db.DateTime)
    trial_end = db.Column(db.DateTime)
    stripe_subscription_id = db.Column(db.String(120), nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)

    # OAuth related fields
    oauth_google = db.Column(db.String(100))
    oauth_google_email = db.Column(db.String(120))
    oauth_google_name = db.Column(db.String(120))
    oauth_google_picture = db.Column(db.String(200))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def is_in_trial(self):
        if not self.trial_end:
            return False
        return datetime.utcnow() < self.trial_end
        
    def days_left_in_trial(self):
        if not self.is_in_trial():
            return 0
        return (self.trial_end - datetime.utcnow()).days

    __table_args__ = (
        db.UniqueConstraint('email', name='uq_user_email'),
        db.UniqueConstraint('stripe_customer_id', name='uq_user_stripe_customer_id'),
        db.UniqueConstraint('stripe_subscription_id', name='uq_user_stripe_subscription_id'),
        db.UniqueConstraint('oauth_google', name='uq_user_oauth_google_id'),
        db.UniqueConstraint('oauth_google_email', name='uq_user_oauth_google_email'),
    )

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    front = db.Column(db.String(500), nullable=False)
    back = db.Column(db.String(500), nullable=False)
    option_1 = db.Column(db.String(200), nullable=False)
    option_2 = db.Column(db.String(200), nullable=False)
    option_3 = db.Column(db.String(200), nullable=False)
    option_4 = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)  # 1, 2, 3, or 4
    front_language = db.Column(db.String(2), default="ja")
    back_language = db.Column(db.String(2), default="en")
    audio_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserExercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id', ondelete='CASCADE'), nullable=False)
    answer = db.Column(db.String(200), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('exercises', lazy=True))
    card = db.relationship('Card', backref=db.backref('exercises', lazy=True))

    @classmethod
    def record_attempt(cls, user, card, answer):
        """Record a user's attempt at an exercise."""
        # Determine the correct answer text based on card.correct_option
        correct_option_text = getattr(card, f"option_{card.correct_option}")
        attempt = cls(
            user_id=user.id,
            card_id=card.id,
            answer=answer,
            is_correct=(answer == correct_option_text)
        )
        db.session.add(attempt)
        db.session.commit()
        return attempt 

class OAuth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)
    provider_user_id = db.Column(db.String(100), nullable=False)
    token = db.Column(db.JSON, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('oauth_tokens', lazy='dynamic')) 