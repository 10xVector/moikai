from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_mail import Mail, Message
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from datetime import datetime, timedelta
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db, User, Card, UserExercise, OAuth
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import BaseForm
from wtforms import StringField, FormField, Form
from wtforms.fields import SelectField
from flask_admin.form.widgets import RenderTemplateWidget
from flask_admin.model.fields import InlineFormField
from flask_admin import helpers as admin_helpers
import openai
from flask_admin import expose
from flask import render_template_string
from flask_admin.helpers import get_url
from markupsafe import Markup
from flask_wtf import FlaskForm
import stripe
import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_babel import Babel, _

# Load environment variables
load_dotenv()

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/language_practice.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Set configuration based on environment
env = os.getenv('FLASK_ENV', 'development')
if env == 'production':
    app.config.from_object('config.ProductionConfig')
else:
    app.config.from_object('config.DevelopmentConfig')

# Stripe configuration
stripe.api_key = app.config['STRIPE_SECRET_KEY']
STRIPE_PUBLIC_KEY = app.config['STRIPE_PUBLIC_KEY']
STRIPE_PRICE_ID = app.config['STRIPE_PRICE_ID']  # Your $2.00/month price ID

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Add logging to app
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Moikai startup')

# Initialize Flask-Admin
class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return session.get('admin_authenticated', False)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin', next=request.url))

admin = Admin(app, name='Moikai Admin', template_mode='bootstrap4', index_view=MyAdminIndexView())

# Flask-Babel configuration
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'ja']
babel = Babel(app)

def get_locale():
    return session.get('lang', 'en')

babel.init_app(app, locale_selector=get_locale)

class CardAdmin(ModelView):
    # The audio_path field is auto-generated and not editable in the admin UI
    excluded_list_columns = ['audio_path']
    list_template = 'admin/card_list.html'

    def is_accessible(self):
        return session.get('admin_authenticated', False)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin', next=request.url))

    def _preview_link(self, context, model, name):
        from flask import url_for
        url = url_for('practice', card_id=model.id)
        return Markup(f'<a class="btn btn-info" href="{url}" target="_blank">Preview</a>')

    column_formatters = {
        'preview': _preview_link
    }
    column_list = ('id', 'front', 'preview', 'audio_path', 'created_at')

    def after_model_change(self, form, model, is_created):
        # Import here to avoid circular import
        from generate_audio import generate_audio_for_card
        generate_audio_for_card(model)
        super().after_model_change(form, model, is_created)

class UserForm(FlaskForm):
    learning_direction = SelectField(
        'Learning Direction',
        choices=[('ja-en', 'Japanese → English'), ('en-ja', 'English → Japanese')]
    )

class UserAdmin(ModelView):
    form = UserForm
    def is_accessible(self):
        return session.get('admin_authenticated', False)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin', next=request.url))

    def _send_email_link(self, context, model, name):
        url = url_for('send_email_admin', user_id=model.id)
        return Markup(f'''
            <form method="post" action="{url}" style="display:inline;">
                <button class="btn btn-warning" onclick="return confirm('Send email to this user?')">Send Email</button>
            </form>
        ''')
    def _reset_progress_link(self, context, model, name):
        url = url_for('reset_progress_admin', user_id=model.id)
        return Markup(f'''
            <form method="post" action="{url}" style="display:inline; margin-left: 4px;">
                <button class="btn btn-danger" onclick="return confirm('Reset progress for this user?')">Reset Progress</button>
            </form>
        ''')
    column_formatters = {
        'send_email': _send_email_link,
        'reset_progress': _reset_progress_link
    }
    column_list = ('id', 'email', 'learning_direction', 'subscribed', 'send_email', 'reset_progress', 'created_at')

admin.add_view(CardAdmin(Card, db.session))
admin.add_view(UserAdmin(User, db.session))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Routes
@app.route('/')
def home():
    if current_user.is_authenticated:
        # Calculate streak
        streak = current_user.streak_count
        # Fallback streak calculation if streak_count is not up-to-date or zero
        if not streak or streak == 0: # Check if streak is None or 0
            from datetime import date, timedelta # Ensure date is imported
            today_date = date.today() # Use date.today() for date objects
            current_streak = 0
            # Iterate backwards from today to find consecutive practice days
            for i in range(365): # Check up to a year back for a more robust streak
                day_to_check = today_date - timedelta(days=i)
                practiced_on_day = UserExercise.query.filter(
                    UserExercise.user_id == current_user.id,
                    db.func.date(UserExercise.completed_at) == day_to_check
                ).first()
                if practiced_on_day:
                    current_streak += 1
                elif i > 0 and current_streak > 0 : # if not practiced today, but had a streak before
                    # if we are checking previous days and streak was broken
                    break 
                elif i == 0 and not practiced_on_day: # Not practiced today
                    current_streak = 0 # Reset if not practiced today
                    break # No need to check further if not practiced today
                elif i > 0 and not practiced_on_day: # Streak broken before today
                    break
            streak = current_streak

        # Heatmap data (last 90 days)
        from datetime import date, timedelta # timedelta already imported but good for clarity
        today_date = date.today()
        days_in_heatmap = 90
        heatmap_data = {} # Using a dict for easier lookup in template: {date: practiced_boolean}
        
        recent_practices = UserExercise.query.filter(
            UserExercise.user_id == current_user.id,
            UserExercise.completed_at >= today_date - timedelta(days=days_in_heatmap-1)
        ).all()
        
        # Convert completed_at to date objects for comparison
        practiced_dates = {p.completed_at.date() for p in recent_practices}

        for i in range(days_in_heatmap):
            day = today_date - timedelta(days=i)
            heatmap_data[day] = day in practiced_dates

        # Other stats
        total_practices = UserExercise.query.filter_by(user_id=current_user.id).count()
        correct_practices = UserExercise.query.filter_by(user_id=current_user.id, is_correct=True).count()
        overall_accuracy = (correct_practices / total_practices * 100) if total_practices > 0 else 0
        
        return render_template('dashboard.html', 
                               streak=streak, 
                               heatmap_data=heatmap_data, 
                               total_practices=total_practices,
                               overall_accuracy=overall_accuracy,
                               heatmap_start_date=today_date - timedelta(days=days_in_heatmap-1),
                               heatmap_today=today_date,
                               timedelta=timedelta) # Pass timedelta to the template context
    return render_template('home.html')

@app.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    if current_user.is_authenticated:
        if current_user.subscribed and \
           (current_user.subscription_status in ['trial', 'active', 'cancelling']) and \
           current_user.current_period_end and \
           current_user.current_period_end > datetime.utcnow():
            flash(_('You already have an active subscription. Manage it from your account page.'), 'info')
            return redirect(url_for('account'))

    if request.method == 'POST':
        email = None
        password = None # Will not be used if current_user is authenticated
        user_is_authenticated_with_stripe_id = current_user.is_authenticated and current_user.stripe_customer_id
        discount_code = request.form.get('discount_code')

        if current_user.is_authenticated:
            email = current_user.email
        else:
            email = request.form.get('email')
            password = request.form.get('password') 
            confirm_password = request.form.get('confirm_password')
            if not email or not password or not confirm_password:
                flash(_('Email and password fields are required for new users.'), 'danger')
                return redirect(url_for('subscribe'))
            if password != confirm_password:
                flash(_('Passwords do not match.'), 'danger')
                return redirect(url_for('subscribe'))
            if len(password) < 8:
                flash(_('Password must be at least 8 characters long.'), 'danger')
                return redirect(url_for('subscribe'))
            # Check if email exists only if a new user is signing up
            existing_new_user_check = User.query.filter_by(email=email).first()
            if existing_new_user_check and not existing_new_user_check.stripe_customer_id: # if user exists but no stripe id, treat as new for payment
                flash(_('Email already registered. Please log in or use a different email.'), 'danger')
                return redirect(url_for('login')) # or subscribe, depending on desired flow for this edge case
            elif existing_new_user_check and existing_new_user_check.stripe_customer_id: # User exists and has stripe ID, should be logged in path
                 flash(_('Email already registered. Please log in to subscribe.'), 'info')
                 return redirect(url_for('login'))
        
        learning_direction = request.form.get('learning_direction')

        if not learning_direction:
            flash(_('Please select a learning direction.'), 'danger')
            return redirect(url_for('subscribe'))

        try:
            customer_id = None
            if user_is_authenticated_with_stripe_id:
                customer_id = current_user.stripe_customer_id
                try:
                    stripe.Customer.retrieve(customer_id) # Validate Stripe customer ID
                except stripe.error.StripeError:
                    customer_id = None # Invalid or deleted in Stripe, force creation
                    # No need to ask for payment info again, Payment Element already handled it
            
            if not customer_id: # Create new customer if needed
                customer = stripe.Customer.create(
                    email=email
                )
                customer_id = customer.id

            # Ensure user object exists and has stripe_customer_id set
            user = User.query.filter_by(email=email).first()
            if not user: # Should only be for new, unauthenticated users
                user = User(email=email, learning_direction=learning_direction)
                user.set_password(password) # Password is set only for new users
                db.session.add(user)
            else: 
                user.learning_direction = learning_direction # Update learning direction if changed
            
            user.stripe_customer_id = customer_id # Ensure it's set/updated on our user model

            # Create subscription with trial period and apply discount if provided
            subscription_params = {
                'customer': customer_id,
                'items': [{'price': STRIPE_PRICE_ID}],
                'trial_period_days': 7,
                'payment_behavior': 'default_incomplete',
                'expand': ['latest_invoice.payment_intent']
            }

            # Apply discount code if provided
            if discount_code:
                try:
                    # Verify the coupon exists and is valid
                    coupon = stripe.Coupon.retrieve(discount_code)
                    subscription_params['coupon'] = discount_code
                except stripe.error.StripeError as e:
                    flash(_('Invalid discount code. Please try again.'), 'danger')
                    return redirect(url_for('subscribe'))

            subscription = stripe.Subscription.create(**subscription_params)
            
            user.subscribed = True
            user.subscription_status = 'trial' if 'trial_period_days' in subscription_params else 'active'
            user.stripe_subscription_id = subscription.id
            
            if hasattr(subscription, 'created') and subscription.created is not None:
                user.subscription_start = datetime.utcfromtimestamp(subscription.created)
            else:
                user.subscription_start = datetime.utcnow() # Fallback, though .created should always be there
                app.logger.warning(
                    f"Stripe subscription {getattr(subscription, 'id', 'Unknown')} for user {user.email} "
                    f"created with missing or None 'created' timestamp."
                )

            if hasattr(subscription, 'current_period_end') and subscription.current_period_end is not None:
                user.current_period_end = datetime.utcfromtimestamp(subscription.current_period_end)
            else:
                user.current_period_end = None
                app.logger.warning(
                    f"Stripe subscription {getattr(subscription, 'id', 'Unknown')} for user {user.email} "
                    f"created with missing or None current_period_end. "
                    f"Subscription status: {getattr(subscription, 'status', 'Unknown')}. "
                    f"Raw current_period_end: {getattr(subscription, 'current_period_end', 'NotSet')}"
                )
            
            if 'trial_period_days' in subscription_params:
                if hasattr(subscription, 'trial_end') and subscription.trial_end is not None:
                    user.trial_end = datetime.utcfromtimestamp(subscription.trial_end)
                else:
                    user.trial_end = None 
                    app.logger.warning(
                        f"Stripe trial subscription {getattr(subscription, 'id', 'Unknown')} for user {user.email} "
                        f"created without a trial_end or trial_end was None. Status: {getattr(subscription, 'status', 'Unknown')}."
                    )
            else: # Not a trial subscription
                user.trial_end = None # Clear trial_end

            db.session.commit()

            # Send first daily practice email immediately
            send_daily_exercise(user)

            # Fetch price dynamically from Stripe
            price_obj = stripe.Price.retrieve(STRIPE_PRICE_ID)
            amount = price_obj['unit_amount'] / 100  # Stripe stores in cents
            currency = price_obj['currency'].upper()
            
            # Calculate discounted amount if coupon was applied
            if discount_code and hasattr(subscription, 'discount'):
                if subscription.discount.coupon.percent_off:
                    amount = amount * (1 - subscription.discount.coupon.percent_off / 100)
                elif subscription.discount.coupon.amount_off:
                    amount = max(0, amount - subscription.discount.coupon.amount_off / 100)

            if user.subscription_status == 'trial':
                charge_message = f"After your 7-day free trial, you will be charged ${amount:.2f} {currency}/month."
            else:
                charge_message = f"You will be charged ${amount:.2f} {currency}/month."
            try:
                msg = Message('Welcome to Moikai!',
                            recipients=[email])
                msg.body = f'''Welcome to your daily {learning_direction} practice!
                
You're starting {user.subscription_status} today. 
Access will continue until {user.current_period_end.strftime('%Y-%m-%d %H:%M UTC') if user.current_period_end else 'the end of your current period'}.

{charge_message}

You will receive your first exercise tomorrow.

To manage your subscription, visit your account page: {url_for('account', _external=True)}'''
                mail.send(msg)
                app.logger.info(f'Welcome email sent to {email}')
            except Exception as e:
                app.logger.error(f'Failed to send welcome email to {email}: {str(e)}')

            login_user(user)
            flash(_('Successfully subscribed! Your %(status)s starts now.', status=user.subscription_status))    
            return redirect(url_for('home'))

        except stripe.error.CardError as e:
            flash(_('Payment failed: %(message)s', message=e.error.message), 'danger')
            return redirect(url_for('subscribe'))
        except stripe.error.StripeError as e:
            app.logger.error(f'Stripe error during subscription: {str(e)}')
            flash(_('A Stripe error occurred: %(message)s. Please try again.', message=(e.user_message or str(e))), 'danger')
            return redirect(url_for('subscribe'))
        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            # Try to get email if available, otherwise use a placeholder
            user_email_for_log = "unknown"
            if 'email' in locals() and email:
                user_email_for_log = email
            elif current_user.is_authenticated and hasattr(current_user, 'email') and current_user.email:
                user_email_for_log = current_user.email

            app.logger.error(f'Error in subscription for email {user_email_for_log}: {str(e)}\nType: {type(e)}\nTraceback: {tb_str}')
            flash('An error occurred. Please try again.', 'danger')
            return redirect(url_for('subscribe'))

    # GET: create a PaymentIntent and pass client_secret to template
    intent = stripe.PaymentIntent.create(
        amount=200,  # $2.00 in cents
        currency='usd',
        automatic_payment_methods={'enabled': True},
    )
    return render_template(
        'subscribe.html',
        stripe_public_key=STRIPE_PUBLIC_KEY,
        client_secret=intent.client_secret
    )

@app.route('/practice/<int:card_id>')
def practice(card_id):
    print(f"Accessed /practice/{card_id}")
    try:
        card = Card.query.get_or_404(card_id)
        print(f"Found card: {card}")
        answer = request.args.get('answer')
        print(f"Answer param: {answer}")

        if answer and current_user.is_authenticated:
            print("User is authenticated, recording attempt")
            UserExercise.record_attempt(current_user, card, answer)

        if answer:
            print("Answer provided")
            # Determine the correct answer text based on card.correct_option
            correct_option_text = getattr(card, f"option_{card.correct_option}")
            if answer == correct_option_text:
                print("Correct answer")
                return render_template('success.html', card=card)
            else:
                print("Incorrect answer")
                return render_template('explanation.html', card=card)

        print("Rendering practice page")
        return render_template('practice.html', card=card)

    except Exception as e:
        print(f"Exception: {e}")
        app.logger.error(f'Error in practice: {str(e)}')
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('home'))

@app.route('/unsubscribe/<token>')
def unsubscribe(token):
    try:
        user = User.query.filter_by(email=token).first()
        if user:
            # Cancel Stripe subscription
            if user.stripe_subscription_id:
                stripe.Subscription.modify(
                    user.stripe_subscription_id,
                    cancel_at_period_end=True
                )
            
            user.subscribed = False
            user.subscription_status = 'cancelled'
            db.session.commit()
            
            flash('Successfully unsubscribed. You will not be charged again.', 'info')
        else:
            flash('Invalid unsubscribe link.', 'danger')
    except Exception as e:
        app.logger.error(f'Error in unsubscribe: {str(e)}')
        flash('An error occurred. Please try again.', 'danger')
    return redirect(url_for('home'))

def send_daily_exercise(user, card=None):
    """Send a daily exercise email to a user."""
    try:
        # Get a card from the pool if none provided
        if card is None:
            from generate_exercises import ExercisePool
            card = ExercisePool.get_exercise_for_user(user)
            if card is None:
                app.logger.error(f"No suitable card found for user {user.email}")
                return False
        
        msg = Message('Your Daily Moikai Practice',
                     recipients=[user.email])
        
        # Render the HTML template
        html_content = render_template('email/daily_exercise.html',
                                     user=user,
                                     card=card,
                                     answer_url=url_for('practice', 
                                                      card_id=card.id,
                                                      _external=True),
                                     unsubscribe_url=url_for('unsubscribe',
                                                           token=user.email,
                                                           _external=True))
        
        msg.html = html_content
        mail.send(msg)
        app.logger.info(f"Daily exercise email sent to {user.email}")
        return True
    except Exception as e:
        app.logger.error(f"Failed to send daily exercise email: {str(e)}")
        return False

# @login_required  # Uncomment this in production to restrict to admin users
@app.route('/admin/generate_card', methods=['POST'])
def generate_card():
    data = request.get_json() or {}
    direction = data.get('direction', 'ja-en')
    if direction == 'ja-en':
        prompt = (
            "Generate a Japanese paragraph for language learners, its English translation, "
            "and 4 multiple-choice options (with the correct one marked as the answer). "
            "Format the response as JSON with keys: front, back, option_1, option_2, option_3, option_4, correct_option (1-4). "
            "'front' should be Japanese, 'back' should be English."
        )
        front_language = 'ja'
        back_language = 'en'
    elif direction == 'en-ja':
        prompt = (
            "Generate an English paragraph for language learners, its Japanese translation, "
            "and 4 multiple-choice options (all in Japanese, with the correct one marked as the answer). "
            "Format the response as JSON with keys: front, back, option_1, option_2, option_3, option_4, correct_option (1-4). "
            "'front' should be English, 'back' and all options should be Japanese."
        )
        front_language = 'en'
        back_language = 'ja'
    else:
        return jsonify({"success": False, "error": "Invalid direction."})

    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    import json
    try:
        content = response.choices[0].message.content
        data = json.loads(content)
        card = Card(
            front=data['front'],
            back=data['back'],
            option_1=data['option_1'],
            option_2=data['option_2'],
            option_3=data['option_3'],
            option_4=data['option_4'],
            correct_option=data['correct_option'],
            front_language=front_language,
            back_language=back_language
        )
        db.session.add(card)
        db.session.commit()
        # Generate audio for the new card
        from generate_audio import generate_audio_for_card
        generate_audio_for_card(card)
        return jsonify({"success": True, "card": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/admin/send_email/<int:user_id>', methods=['POST'])
def send_email_admin(user_id):
    user = User.query.get_or_404(user_id)
    success = send_daily_exercise(user)
    if success:
        return '<script>alert("Email sent!");window.history.back();</script>'
    else:
        return '<script>alert("Failed to send email. Check logs for details.");window.history.back();</script>'

@app.route('/admin/reset_progress/<int:user_id>', methods=['POST'])
def reset_progress_admin(user_id):
    from models import UserExercise
    UserExercise.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return '<script>alert("Progress reset for user!");window.history.back();</script>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('login'))
            
        login_user(user, remember=remember)
        return redirect(url_for('home'))
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/set_language', methods=['GET', 'POST'])
def set_language():
    lang = request.values.get('lang', 'en')
    session['lang'] = lang
    next_url = request.values.get('next') or url_for('home')
    return redirect(next_url)

@app.route('/account', methods=['GET'])
@login_required
def account():
    # Ensure current_period_end is a datetime object for comparison
    # This is important if it comes from the database and might be None
    period_end_for_display = current_user.current_period_end
    show_resubscribe_button = False

    if current_user.subscription_status == 'cancelling' and \
       current_user.current_period_end and \
       current_user.current_period_end <= datetime.utcnow():
        # If period end has passed, mark as fully cancelled
        current_user.subscribed = False
        current_user.subscription_status = 'cancelled'
        # current_user.current_period_end = None # Optionally clear it or leave as is for history
        db.session.commit()
        show_resubscribe_button = True # Now they can resubscribe
    
    elif not current_user.subscribed and current_user.subscription_status == 'cancelled':
        show_resubscribe_button = True

    return render_template('account.html', 
                           user=current_user, 
                           period_end_for_display=period_end_for_display,
                           show_resubscribe_button=show_resubscribe_button)

@app.route('/account/unsubscribe', methods=['GET', 'POST'])
@login_required
def account_unsubscribe():
    if request.method == 'POST':
        try:
            user = current_user
            if user.stripe_subscription_id:
                # Cancel Stripe subscription at period end
                subscription = stripe.Subscription.retrieve(user.stripe_subscription_id)
                stripe.Subscription.modify(
                    user.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                user.subscription_status = 'cancelling'
                # current_period_end should already be set, but Stripe might update it on cancel_at_period_end action
                # It's good to re-fetch and store it to be sure.
                if hasattr(subscription, 'current_period_end') and subscription.current_period_end is not None:
                    user.current_period_end = datetime.utcfromtimestamp(subscription.current_period_end)
                else:
                    user.current_period_end = None
                    app.logger.warning(
                        f"Stripe subscription {getattr(subscription, 'id', 'Unknown')} for user {user.email} "
                        f"missing or None current_period_end during unsubscribe. "
                        f"Status: {getattr(subscription, 'status', 'Unknown')}."
                    )
                # user.subscribed remains True until current_period_end
                db.session.commit()
                # The success page will explain they have access until current_period_end
                return render_template('unsubscribe_success.html', current_period_end=user.current_period_end)
            else:
                # This case should ideally not happen if they are on this page
                # but as a fallback, mark as unsubscribed if no Stripe ID
                user.subscribed = False
                user.subscription_status = 'cancelled' # Or a more appropriate status
                user.current_period_end = datetime.utcnow() # Or None
                db.session.commit()
                flash(_('Your subscription has been processed. If you had an active plan, it is now set to cancel.'), 'info')
                return redirect(url_for('account'))

        except stripe.error.StripeError as e:
            app.logger.error(f'Stripe error in account unsubscribe: {str(e)}')
            flash(_('A Stripe error occurred: {error}. Please try again.').format(error=str(e.user_message or e.code or 'Unknown Stripe error')), 'danger')
            return redirect(url_for('account'))
        except Exception as e:
            app.logger.error(f'Error in account unsubscribe: {str(e)}')
            flash('An error occurred. Please try again.', 'danger')
            return redirect(url_for('account'))
    # GET: show confirmation page
    return render_template('unsubscribe_confirm.html')

ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'changeme')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('admin_authenticated'):
        return redirect('/admin/')
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_authenticated'] = True
            return redirect('/admin/')
        else:
            flash('Incorrect password', 'danger')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_authenticated', None)
    flash('Logged out of admin.', 'info')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() in ['true', 'on', '1'], port=8080) 