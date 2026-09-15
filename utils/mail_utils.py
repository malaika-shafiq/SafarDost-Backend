import logging
import os
import smtplib
from email.mime.text import MIMEText
import resend
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
    Dispatches a secure 6-Digit account recovery OTP directly to the user's inbox
    via HTTPS web REST API layers, completely bypassing SMTP port locks.
    """
    # 🚀 Automatically reads the token from your active environmental maps
    resend.api_key = os.getenv("RESEND_API_KEY")

    if not resend.api_key:
        logger.warning("RESEND_API_KEY Missing in Environmental Variable Maps. Skipping live dispatch.")
        return False

    try:
        # Fire request over standard port 443
        params: dict = {
            "from": "Safar Dost Security <onboarding@resend.dev>",  # Free sandbox sending domain
            "to": [recipient_email],
            "subject": "Safardost Account Password Recovery OTP",
            "html": f"""
                    <h3>Hello,</h3>
                    <p>You requested a password reset for your Safardost account.</p>
                    <p>Your secure 6-digit verification code is:</p>
                    <h2 style='color: #4F46E5;'>👉 {otp_code} 👈</h2>
                    <p>This verification code will expire in 15 minutes.</p>
                    <p>Regards,<br>The Safardost Security Team</p>
                    """
        }

        resend.emails.send(params)
        return True

    except Exception as api_error:
        logger.error(f"Resend HTTPS API Transport Error Frame: {str(api_error)}")
        return False