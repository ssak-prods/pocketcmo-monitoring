import os
import datetime
import resend
import logging
from app.models import SessionLocal, DailyStat

logger = logging.getLogger(__name__)

# Very strict daily cap
MAX_EMAILS_PER_DAY = 10
TARGET_EMAIL = "pikachuball3@gmail.com"

def send_alert_email(service_name: str, level: str, message: str, ai_summary: str):
    """Sends an email alert using Resend, adhering strictly to the 10 emails/day limit."""
    resend.api_key = os.getenv("RESEND_API_KEY")
    sender_email = os.getenv("RESEND_SENDER", "onboarding@resend.dev") # Default Resend free tier email
    
    if not resend.api_key:
        logger.error("RESEND_API_KEY not set. Cannot send alert email.")
        return False
        
    db = SessionLocal()
    try:
        today_str = datetime.date.today().isoformat()
        daily_stat = db.query(DailyStat).filter_by(date_str=today_str).first()
        
        if not daily_stat:
            daily_stat = DailyStat(date_str=today_str, emails_sent=0)
            db.add(daily_stat)
            db.commit()
            
        if daily_stat.emails_sent >= MAX_EMAILS_PER_DAY:
            logger.warning(f"BLOCKED: Daily email limit ({MAX_EMAILS_PER_DAY}) reached. Email will not be sent.")
            return False
            
        # We are under limit, send the email
        subject = f"[{level}] PocketCMO Alert: {service_name} failing"
        html_content = f"""
        <h2>PocketCMO Production Alert</h2>
        <p><strong>Service:</strong> {service_name}</p>
        <p><strong>Level:</strong> {level}</p>
        <p><strong>Message:</strong> {message}</p>
        <hr/>
        <h3>AI Diagnosis</h3>
        <p>{ai_summary}</p>
        <br/>
        <p><small>PocketCMO Monitor Service (Resend daily usage: {daily_stat.emails_sent + 1}/{MAX_EMAILS_PER_DAY})</small></p>
        """
        
        params = {
            "from": sender_email,
            "to": TARGET_EMAIL,
            "subject": subject,
            "html": html_content
        }
        
        resend.Emails.send(params)
        
        # Increment counter
        daily_stat.emails_sent += 1
        db.commit()
        
        logger.info(f"Email sent successfully to {TARGET_EMAIL}. ({daily_stat.emails_sent}/{MAX_EMAILS_PER_DAY} used today)")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False
    finally:
        db.close()
