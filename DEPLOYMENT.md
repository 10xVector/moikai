# Deployment Guide

This guide provides instructions for deploying the Moikai application to different platforms.

## Prerequisites

1. Python 3.8 or higher
2. Git
3. A code editor
4. An email service account (Gmail recommended for testing)

## Environment Variables

Create a `.env` file with the following variables:

```env
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=your-secure-secret-key
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
DATABASE_URL=your-database-url
```

## Deployment Options

### 1. PythonAnywhere (Recommended for Beginners)

1. Sign up for a free account at [PythonAnywhere](https://www.pythonanywhere.com)
2. Go to the Dashboard and click "Add a new web app"
3. Choose "Flask" and select Python 3.8 or higher
4. In the virtual environment section:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.8 language-practice
   pip install -r requirements.txt
   ```
5. Upload your code using the Files tab or Git
6. Configure your web app:
   - Set the working directory to your project folder
   - Set the WSGI configuration file to point to your app
   - Add your environment variables in the "Environment variables" section
7. Reload your web app

### 2. DigitalOcean (Recommended for Production)

1. Create a DigitalOcean account
2. Create a new Droplet (Ubuntu 20.04 recommended)
3. Connect to your Droplet via SSH
4. Install required packages:
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx
   ```
5. Clone your repository:
   ```bash
   git clone your-repository-url
   cd your-project
   ```
6. Set up virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
7. Set up Gunicorn:
   ```bash
   pip install gunicorn
   ```
8. Create a systemd service:
   ```bash
   sudo nano /etc/systemd/system/language-practice.service
   ```
   Add the following:
   ```ini
   [Unit]
   Description=Moikai Gunicorn Service
   After=network.target

   [Service]
   User=your-username
   Group=www-data
   WorkingDirectory=/path/to/your/project
   Environment="PATH=/path/to/your/project/venv/bin"
   ExecStart=/path/to/your/project/venv/bin/gunicorn --workers 3 --bind unix:language-practice.sock -m 007 app:app

   [Install]
   WantedBy=multi-user.target
   ```
9. Configure Nginx:
   ```bash
   sudo nano /etc/nginx/sites-available/language-practice
   ```
   Add the following:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           include proxy_params;
           proxy_pass http://unix:/path/to/your/project/language-practice.sock;
       }
   }
   ```
10. Enable the site and start services:
    ```bash
    sudo ln -s /etc/nginx/sites-available/language-practice /etc/nginx/sites-enabled
    sudo systemctl start language-practice
    sudo systemctl enable language-practice
    sudo systemctl restart nginx
    ```

### 3. Heroku

1. Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Login to Heroku:
   ```bash
   heroku login
   ```
3. Create a new Heroku app:
   ```bash
   heroku create your-app-name
   ```
4. Add PostgreSQL:
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```
5. Set environment variables:
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set MAIL_USERNAME=your-email
   heroku config:set MAIL_PASSWORD=your-password
   ```
6. Deploy your application:
   ```bash
   git push heroku main
   ```

## Database Setup

After deployment, initialize the database:

```bash
flask db upgrade
```

## Setting up Daily Emails

1. For PythonAnywhere:
   - Go to the Tasks tab
   - Add a new daily task:
     ```bash
     /path/to/venv/bin/python /path/to/your/project/send_daily_emails.py
     ```

2. For DigitalOcean:
   - Add a cron job:
     ```bash
     crontab -e
     ```
     Add:
     ```
     0 8 * * * /path/to/your/project/venv/bin/python /path/to/your/project/send_daily_emails.py
     ```

3. For Heroku:
   - Use the Heroku Scheduler add-on:
     ```bash
     heroku addons:create scheduler:standard
     ```
   - Add the command in the Heroku dashboard:
     ```
     python send_daily_emails.py
     ```

## Monitoring

1. Set up logging:
   - Check the logs directory for application logs
   - Monitor error rates and user activity

2. Set up monitoring (optional):
   - Use services like Sentry for error tracking
   - Set up uptime monitoring with services like UptimeRobot

## Security Considerations

1. Always use HTTPS in production
2. Keep dependencies updated
3. Regularly backup your database
4. Monitor for suspicious activity
5. Use strong passwords and API keys
6. Enable security headers
7. Implement rate limiting for API endpoints

## Backup Strategy

1. Database backups:
   ```bash
   # For PostgreSQL
   pg_dump your_database > backup.sql
   
   # For SQLite
   cp language_practice.db backup.db
   ```

2. Set up automated backups:
   - Use cloud storage (AWS S3, Google Cloud Storage)
   - Implement regular backup schedules
   - Test backup restoration regularly 