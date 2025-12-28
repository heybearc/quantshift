import nodemailer from 'nodemailer';

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST || 'smtp.gmail.com',
  port: parseInt(process.env.SMTP_PORT || '587'),
  secure: false,
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
  },
});

export async function sendVerificationEmail(
  email: string,
  fullName: string,
  verificationToken: string
) {
  const verificationUrl = `${process.env.NEXT_PUBLIC_APP_URL}/verify-email?token=${verificationToken}`;

  const mailOptions = {
    from: `"QuantShift Platform" <${process.env.SMTP_USER}>`,
    to: email,
    subject: 'Verify Your QuantShift Account',
    html: `
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 50%, #8b5cf6 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }
            .button { display: inline-block; background: #0ea5e9; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
            .warning { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; }
            .footer { text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>Welcome to QuantShift</h1>
              <p>Quantum Trading Intelligence Platform</p>
            </div>
            <div class="content">
              <h2>Hello ${fullName},</h2>
              <p>Thank you for registering with QuantShift. To complete your registration and access the platform, please verify your email address.</p>
              
              <div style="text-align: center;">
                <a href="${verificationUrl}" class="button">Verify Email Address</a>
              </div>
              
              <p>Or copy and paste this link into your browser:</p>
              <p style="word-break: break-all; color: #0ea5e9;">${verificationUrl}</p>
              
              <div class="warning">
                <strong>⚠️ Security Notice:</strong>
                <ul>
                  <li>This link will expire in 24 hours</li>
                  <li>Your account requires admin approval before full access</li>
                  <li>Never share your password with anyone</li>
                  <li>If you didn't create this account, please ignore this email</li>
                </ul>
              </div>
              
              <p>After email verification, an administrator will review and approve your account. You'll receive another email once approved.</p>
              
              <div class="footer">
                <p>This is an automated message from QuantShift. Please do not reply to this email.</p>
                <p>&copy; ${new Date().getFullYear()} QuantShift. All rights reserved.</p>
              </div>
            </div>
          </div>
        </body>
      </html>
    `,
  };

  try {
    await transporter.sendMail(mailOptions);
    return { success: true };
  } catch (error) {
    console.error('Error sending verification email:', error);
    return { success: false, error };
  }
}

export async function sendAccountApprovedEmail(
  email: string,
  fullName: string
) {
  const loginUrl = `${process.env.NEXT_PUBLIC_APP_URL}/login`;

  const mailOptions = {
    from: `"QuantShift Platform" <${process.env.SMTP_USER}>`,
    to: email,
    subject: 'Your QuantShift Account Has Been Approved',
    html: `
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }
            .button { display: inline-block; background: #10b981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
            .footer { text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>✅ Account Approved!</h1>
            </div>
            <div class="content">
              <h2>Hello ${fullName},</h2>
              <p>Great news! Your QuantShift account has been approved by an administrator.</p>
              <p>You can now log in and access the platform.</p>
              
              <div style="text-align: center;">
                <a href="${loginUrl}" class="button">Log In to QuantShift</a>
              </div>
              
              <p><strong>Next Steps:</strong></p>
              <ul>
                <li>Log in with your email and password</li>
                <li>Explore the dashboard and trading features</li>
                <li>Review platform documentation and tutorials</li>
                <li>Start with paper trading to familiarize yourself</li>
              </ul>
              
              <div class="footer">
                <p>&copy; ${new Date().getFullYear()} QuantShift. All rights reserved.</p>
              </div>
            </div>
          </div>
        </body>
      </html>
    `,
  };

  try {
    await transporter.sendMail(mailOptions);
    return { success: true };
  } catch (error) {
    console.error('Error sending approval email:', error);
    return { success: false, error };
  }
}

export async function sendSuspiciousLoginEmail(
  email: string,
  fullName: string,
  ipAddress: string,
  location?: string
) {
  const mailOptions = {
    from: `"QuantShift Security" <${process.env.SMTP_USER}>`,
    to: email,
    subject: '⚠️ Suspicious Login Attempt Detected',
    html: `
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }
            .alert { background: #fee2e2; border-left: 4px solid #ef4444; padding: 15px; margin: 20px 0; }
            .footer { text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>⚠️ Security Alert</h1>
            </div>
            <div class="content">
              <h2>Hello ${fullName},</h2>
              <p>We detected a login attempt on your QuantShift account from an unusual location.</p>
              
              <div class="alert">
                <strong>Login Details:</strong>
                <ul>
                  <li><strong>Time:</strong> ${new Date().toLocaleString()}</li>
                  <li><strong>IP Address:</strong> ${ipAddress}</li>
                  ${location ? `<li><strong>Location:</strong> ${location}</li>` : ''}
                </ul>
              </div>
              
              <p><strong>If this was you:</strong> No action needed. You can safely ignore this email.</p>
              
              <p><strong>If this wasn't you:</strong></p>
              <ul>
                <li>Change your password immediately</li>
                <li>Review your account activity</li>
                <li>Contact support if you notice any unauthorized access</li>
              </ul>
              
              <div class="footer">
                <p>This is an automated security alert from QuantShift.</p>
                <p>&copy; ${new Date().getFullYear()} QuantShift. All rights reserved.</p>
              </div>
            </div>
          </div>
        </body>
      </html>
    `,
  };

  try {
    await transporter.sendMail(mailOptions);
    return { success: true };
  } catch (error) {
    console.error('Error sending suspicious login email:', error);
    return { success: false, error };
  }
}

export async function sendPasswordResetEmail(
  email: string,
  fullName: string,
  resetToken: string
) {
  const resetUrl = `${process.env.NEXT_PUBLIC_APP_URL}/reset-password?token=${resetToken}`;

  const mailOptions = {
    from: `"QuantShift Platform" <${process.env.SMTP_USER}>`,
    to: email,
    subject: 'Reset Your QuantShift Password',
    html: `
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }
            .button { display: inline-block; background: #0ea5e9; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
            .warning { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; }
            .footer { text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>Password Reset Request</h1>
            </div>
            <div class="content">
              <h2>Hello ${fullName},</h2>
              <p>We received a request to reset your QuantShift password.</p>
              
              <div style="text-align: center;">
                <a href="${resetUrl}" class="button">Reset Password</a>
              </div>
              
              <p>Or copy and paste this link into your browser:</p>
              <p style="word-break: break-all; color: #0ea5e9;">${resetUrl}</p>
              
              <div class="warning">
                <strong>⚠️ Security Notice:</strong>
                <ul>
                  <li>This link will expire in 1 hour</li>
                  <li>If you didn't request this, please ignore this email</li>
                  <li>Your password will remain unchanged unless you click the link</li>
                </ul>
              </div>
              
              <div class="footer">
                <p>This is an automated message from QuantShift.</p>
                <p>&copy; ${new Date().getFullYear()} QuantShift. All rights reserved.</p>
              </div>
            </div>
          </div>
        </body>
      </html>
    `,
  };

  try {
    await transporter.sendMail(mailOptions);
    return { success: true };
  } catch (error) {
    console.error('Error sending password reset email:', error);
    return { success: false, error };
  }
}
