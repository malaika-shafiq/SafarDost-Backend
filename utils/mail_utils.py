import logging
import os
import smtplib
from email.mime.text import MIMEText
from datetime import date

logger = logging.getLogger("uvicorn.error")


def send_vendor_booking_email(booking_id: int, hotel_name: str, location: str, check_in: date, check_out: date,
                              total_price: int, customer_email: str):
    """
    Synchronous utility helper that securely transmits a detailed reservation
    alert email directly to management operations desk.
    """
    try:
        email_body = f"""
Dear Hotel Management Operations Team,

A brand new guest reservation has been successfully confirmed via the SafarDost Platform.

=======================================================
RESERVATION DETAILS
=======================================================
Booking Reference ID: #{booking_id}
Target Property Name: {hotel_name}
Property Location:   {location}
Guest Account Email: {customer_email}
Check-In Date:       {check_in}
Check-Out Date:      {check_out}
Total Payout Amount: {total_price:,} PKR (Cash on Arrival)
=======================================================

Please cross-reference this Booking Reference ID inside your vendor administration dashboard panel on arrival.

Safe Travels,
The SafarDost/TravelMate Pakistan Backend System Automation
        """
        msg = MIMEText(email_body)
        msg['Subject'] = f"🔔 NEW RESERVATION ALERT - Booking Reference ID #{booking_id}"

        smtp_sender = os.environ.get("SAFARDOST_EMAIL_USER", "notifications@safardost.com")
        smtp_receiver = os.environ.get("SAFARDOST_VENDOR_DESK", "vendor-desk@safardost.com")

        msg['From'] = smtp_sender
        msg['To'] = smtp_receiver

        smtp_host = os.environ.get("SAFARDOST_SMTP_HOST", "://gmail.com")
        smtp_port = int(os.environ.get("SAFARDOST_SMTP_PORT", 587))
        smtp_password = os.environ.get("SAFARDOST_EMAIL_PASSWORD")

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_password:
                server.login(smtp_sender, smtp_password)
            server.send_message(msg)
    except Exception as email_error:
        print(f"[SECURITY/OPERATIONS WARNING]: Automated reservation alert email execution failed: {email_error}")


def send_restaurant_booking_email(booking_id: int, restaurant_name: str, location: str, res_date: date, res_time: str,
                                  guests: int, customer_email: str):
    """
    Synchronous utility helper that securely transmits a detailed dining
    reservation alert email directly to the restaurant operations desk.
    """
    try:
        email_body = f"""
Dear Restaurant Management Team,

A brand new table reservation has been successfully confirmed via the SafarDost Platform.

=======================================================
DINING RESERVATION DETAILS
=======================================================
Booking Reference ID: #{booking_id}
Restaurant Name:      {restaurant_name}
Location:             {location}
Guest Account Email:  {customer_email}
Reservation Date:     {res_date}
Reservation Time:     {res_time} (PKT)
Number of Guests:     {guests} Person(s)
=======================================================

Please ensure a table is allocated and held matching this operational reference ID.

Best Regards,
The SafarDost/TravelMate Pakistan Backend System Automation
        """
        msg = MIMEText(email_body)
        msg['Subject'] = f"🍽️ NEW TABLE RESERVATION - Reference ID #{booking_id}"

        smtp_sender = os.environ.get("SAFARDOST_EMAIL_USER", "notifications@safardost.com")
        smtp_receiver = os.environ.get("SAFARDOST_VENDOR_DESK", "vendor-desk@safardost.com")

        msg['From'] = smtp_sender
        msg['To'] = smtp_receiver

        smtp_host = os.environ.get("SAFARDOST_SMTP_HOST", "://gmail.com")
        smtp_port = int(os.environ.get("SAFARDOST_SMTP_PORT", 587))
        smtp_password = os.environ.get("SAFARDOST_EMAIL_PASSWORD")

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_password:
                server.login(smtp_sender, smtp_password)
            server.send_message(msg)
    except Exception as email_error:
        print(f"[RESTAURANT NOTIFICATION WARNING]: Dining alert email failed to execute: {email_error}")


def send_transport_booking_email(booking_id: int, transport_type: str, departure: date, source: str, destination: str,
                                 total_price: int, customer_email: str):
    """
    Synchronous utility helper that securely transmits a detailed logistics
    booking alert email directly to the transport provider operations desk.
    ```"""
    try:
        email_body = f"""
Dear Transport Logistics Team,

A brand new vehicle/ticket booking has been successfully confirmed via the SafarDost Platform.

=======================================================
LOGISTICS BOOKING DETAILS
=======================================================
Booking Reference ID: #{booking_id}
Vehicle/Service Type: {transport_type}
Departure Date:       {departure}
Route Fleet Matrix:   From {source} To {destination}
Passenger Email:      {customer_email}
Total Fleet Payout:   {total_price:,} PKR (Cash on Departure)
=======================================================

Please ensure the requested transit assets are verified and dispatched cleanly matching this operational reference ID.

Safe Journey,
The SafarDost/TravelMate Pakistan Backend System Automation
        """
        msg = MIMEText(email_body)
        msg['Subject'] = f"🚗 NEW TRANSPORT LOGISTICS CONFIRMATION - Reference ID #{booking_id}"

        smtp_sender = os.environ.get("SAFARDOST_EMAIL_USER", "notifications@safardost.com")
        smtp_receiver = os.environ.get("SAFARDOST_VENDOR_DESK", "vendor-desk@safardost.com")

        msg['From'] = smtp_sender
        msg['To'] = smtp_receiver

        smtp_host = os.environ.get("SAFARDOST_SMTP_HOST", "://gmail.com")
        smtp_port = int(os.environ.get("SAFARDOST_SMTP_PORT", 587))
        smtp_password = os.environ.get("SAFARDOST_EMAIL_PASSWORD")

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_password:
                server.login(smtp_sender, smtp_password)
            server.send_message(msg)
    except Exception as email_error:
        print(f"[TRANSPORT NOTIFICATION WARNING]: Transit alert email failed to execute: {email_error}")


def send_otp_email(recipient_email: str, otp_code: str) -> bool:
    """
    Dispatches a secure 6-Digit password recovery OTP directly to the user's inbox.
    Returns True if sent successfully, False otherwise.
    """
    sender_email = os.getenv("SAFARDOST_EMAIL_USER")
    sender_password = os.getenv("SAFARDOST_EMAIL_PASSWORD")

    # 🛡️ Safety Shield Guardrail: If credentials are unassigned, don't crash the server loop execution thread!
    if not sender_email or not sender_password:
        logger.warning("SMTP Mail Credentials Missing in Environmental Variable Maps. Skipping live dispatch.")
        return False

    msg = MIMEText(f"""
    Hello,

    You requested a password reset for your Safardost account.
    Your secure 6-digit verification code is:

    👉 {otp_code} 👈

    This verification code will expire in 15 minutes. If you did not make this request, 
    please secure your account credentials immediately.

    Regards,
    The Safardost Security Team
    """)

    msg["Subject"] = "Safardost Account Password Recovery OTP"
    msg["From"] = sender_email
    msg["To"] = recipient_email

    try:
        # ✅ FIXED: Correct public endpoint server host layout path for Google Mail SMTP routing channel
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        return True

    except Exception as smtp_error:
        # Catches local firewall blocks or authentication hiccups gracefully without an app crash
        logger.error(f"SMTP Mail Gateway Dispatch Interruption Error Frame: {str(smtp_error)}")
        return False