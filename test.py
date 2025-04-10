from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)

# Flask-Mail configuration
app.config["MAIL_SERVER"] = "mail.privateemail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False
app.config["MAIL_USERNAME"] = "support@videosummarization.online"
app.config["MAIL_PASSWORD"] = '!yds,,fLL5F!Xbm'

mail = Mail(app)


@app.route("/send-reset-password-email")
def send_reset_password_email():
    try:
        html_message = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                /* Modern styling with teal theme */
                :root {
                    --primary-color: #008080;
                    --primary-light: #b2d8d8;
                    --primary-dark: #006666;
                    --text-color: #333333;
                    --background-light: #f5f5f5;
                }
                
                body {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background-color: var(--background-light);
                    margin: 0;
                    padding: 20px;
                    line-height: 1.6;
                }
                
                .email-container {
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }
                
                .email-header {
                    background-color: var(--primary-color);
                    color: #ffffff;
                    padding: 30px 20px;
                    text-align: center;
                }
                
                .email-header h1 {
                    margin: 0;
                    font-size: 24px;
                    font-weight: 600;
                }
                
                .email-body {
                    padding: 30px;
                    color: var(--text-color);
                }
                
                .email-body p {
                    margin: 0 0 20px;
                    font-size: 16px;
                }
                
                .btn-container {
                    text-align: center;
                    margin: 30px 0;
                }
                
                .btn {
                    display: inline-block;
                    padding: 12px 32px;
                    font-size: 16px;
                    font-weight: 600;
                    color: #ffffff;
                    background-color: var(--primary-color);
                    text-decoration: none;
                    border-radius: 6px;
                    transition: background-color 0.3s ease;
                }
                
                .btn:hover {
                    background-color: var(--primary-dark);
                }
                
                .divider {
                    height: 1px;
                    background-color: #e0e0e0;
                    margin: 25px 0;
                }
                
                .email-footer {
                    text-align: center;
                    padding: 20px;
                    background-color: var(--background-light);
                    color: #666666;
                    font-size: 14px;
                }
                
                .logo {
                    width: 120px;
                    height: auto;
                    margin-bottom: 15px;
                }
                
                .social-links {
                    margin-top: 20px;
                }
                
                .social-links a {
                    color: var(--primary-color);
                    text-decoration: none;
                    margin: 0 10px;
                }
                
                @media (max-width: 600px) {
                    body {
                        padding: 10px;
                    }
                    
                    .email-container {
                        border-radius: 8px;
                    }
                    
                    .email-header {
                        padding: 20px;
                    }
                    
                    .email-body {
                        padding: 20px;
                    }
                }
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <img src="https://your-logo-url.com/logo.png" alt="Logo" class="logo">
                    <h1>Reset Your Password</h1>
                </div>
                <div class="email-body">
                    <p>Hello,</p>
                    <p>We received a request to reset your password for your Video Summarization account. 
                       If you didn't make this request, you can safely ignore this email.</p>
                    
                    <div class="btn-container">
                        <a href="https://example.com/reset-password?token=your-token" class="btn">
                            Reset Password
                        </a>
                    </div>
                    
                    <p>This password reset link will expire in 24 hours. If you need to reset your password 
                       after that, please make a new request.</p>
                    
                    <div class="divider"></div>
                    
                    <p>If you're having trouble clicking the button, copy and paste the URL below into your browser:</p>
                    <p style="font-size: 14px; color: #666666;">
                        https://example.com/reset-password?token=your-token
                    </p>
                    
                    <p>Best regards,<br>The Video Summarization Team</p>
                </div>
                <div class="email-footer">
                    <p>&copy; 2024 Video Summarization. All rights reserved.</p>
                    <div class="social-links">
                        <a href="#">Twitter</a> |
                        <a href="#">Facebook</a> |
                        <a href="#">LinkedIn</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        msg = Message(
            subject="Reset Your Password",
            sender=(app.config["MAIL_USERNAME"]),
            recipients=["yatharthk2406@gmail.com"],  # Replace with recipient's email
            html=html_message,
        )
        mail.send(msg)
        return "Reset password email sent successfully!"
    except Exception as e:
        return f"Failed to send email: {e}"


if __name__ == "__main__":
    app.run(debug=True)
