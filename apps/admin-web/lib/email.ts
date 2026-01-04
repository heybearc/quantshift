import nodemailer from 'nodemailer';
import { prisma } from './prisma';

interface EmailConfig {
  authType: 'gmail' | 'smtp';
  gmailEmail?: string;
  gmailAppPassword?: string;
  smtpServer?: string;
  smtpPort?: string;
  smtpUser?: string;
  smtpPassword?: string;
  smtpSecure?: boolean;
  fromEmail?: string;
  fromName?: string;
  replyToEmail?: string;
}

async function getEmailConfig(): Promise<EmailConfig> {
  const settings = await prisma.platformSettings.findMany({
    where: {
      key: {
        in: [
          'email_auth_type',
          'email_gmail_email',
          'email_gmail_app_password',
          'email_smtp_server',
          'email_smtp_port',
          'email_smtp_user',
          'email_smtp_password',
          'email_smtp_secure',
          'email_from_email',
          'email_from_name',
          'email_reply_to_email',
        ],
      },
    },
  });

  const config: EmailConfig = {
    authType: 'gmail',
    gmailEmail: '',
    gmailAppPassword: '',
    smtpServer: 'smtp.gmail.com',
    smtpPort: '587',
    smtpUser: '',
    smtpPassword: '',
    smtpSecure: false,
    fromEmail: '',
    fromName: 'QuantShift Trading Platform',
    replyToEmail: '',
  };

  settings.forEach((setting) => {
    const key = setting.key.replace('email_', '').replace(/_/g, '');
    let value: string | boolean = setting.value;

    if (key === 'smtpsecure') {
      value = value === 'true';
    }

    const keyMap: { [key: string]: keyof EmailConfig } = {
      authtype: 'authType',
      gmailemail: 'gmailEmail',
      gmailapppassword: 'gmailAppPassword',
      smtpserver: 'smtpServer',
      smtpport: 'smtpPort',
      smtpuser: 'smtpUser',
      smtppassword: 'smtpPassword',
      smtpsecure: 'smtpSecure',
      fromemail: 'fromEmail',
      fromname: 'fromName',
      replytoemail: 'replyToEmail',
    };

    const mappedKey = keyMap[key];
    if (mappedKey) {
      (config as any)[mappedKey] = value;
    }
  });

  return config;
}

async function createTransporter() {
  const config = await getEmailConfig();

  if (config.authType === 'gmail') {
    return nodemailer.createTransport({
      service: 'gmail',
      auth: {
        user: config.gmailEmail,
        pass: config.gmailAppPassword,
      },
    });
  } else {
    return nodemailer.createTransport({
      host: config.smtpServer,
      port: parseInt(config.smtpPort || '587'),
      secure: config.smtpSecure,
      auth: {
        user: config.smtpUser,
        pass: config.smtpPassword,
      },
    });
  }
}

export async function sendTestEmail(toEmail: string): Promise<{ success: boolean; error?: any }> {
  try {
    const transporter = await createTransporter();
    const config = await getEmailConfig();
    const fromEmail = config.fromEmail || config.gmailEmail || config.smtpUser;
    const fromName = config.fromName || 'QuantShift Platform';

    const mailOptions = {
      from: `"${fromName}" <${fromEmail}>`,
      to: toEmail,
      subject: 'QuantShift Email Test - Configuration Successful',
      html: `
        <!DOCTYPE html>
        <html>
          <head>
            <style>
              body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
              .container { max-width: 600px; margin: 0 auto; padding: 20px; }
              .header { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
              .content { background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }
              .success { background: #d1fae5; border-left: 4px solid #10b981; padding: 15px; margin: 20px 0; }
              .footer { text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; }
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header">
                <h1>✅ Email Test Successful!</h1>
              </div>
              <div class="content">
                <div class="success">
                  <strong>Congratulations!</strong> Your email configuration is working correctly.
                </div>
                <p>This is a test email from your QuantShift admin platform.</p>
                <p><strong>Configuration Details:</strong></p>
                <ul>
                  <li><strong>Auth Type:</strong> ${config.authType === 'gmail' ? 'Gmail App Password' : 'Custom SMTP'}</li>
                  <li><strong>From Email:</strong> ${fromEmail}</li>
                  <li><strong>From Name:</strong> ${fromName}</li>
                  <li><strong>Test Time:</strong> ${new Date().toLocaleString()}</li>
                </ul>
                <p>You can now use this email configuration to send notifications, invitations, and alerts.</p>
                <div class="footer">
                  <p>&copy; ${new Date().getFullYear()} QuantShift. All rights reserved.</p>
                </div>
              </div>
            </div>
          </body>
        </html>
      `,
      text: `Email Test Successful!\n\nYour QuantShift email configuration is working correctly.\n\nConfiguration Details:\n- Auth Type: ${config.authType}\n- From Email: ${fromEmail}\n- From Name: ${fromName}\n- Test Time: ${new Date().toLocaleString()}`,
    };

    await transporter.sendMail(mailOptions);
    return { success: true };
  } catch (error) {
    console.error('Error sending test email:', error);
    return { success: false, error };
  }
}

export async function sendVerificationEmail(
  email: string,
  fullName: string,
  verificationToken: string
) {
  const verificationUrl = `${process.env.NEXT_PUBLIC_APP_URL}/verify-email?token=${verificationToken}`;
  const transporter = await createTransporter();
  const config = await getEmailConfig();
  const fromEmail = config.fromEmail || config.gmailEmail || config.smtpUser;
  const fromName = config.fromName || 'QuantShift Platform';

  const mailOptions = {
    from: `"${fromName}" <${fromEmail}>`,
    replyTo: config.replyToEmail || fromEmail,
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
  const transporter = await createTransporter();
  const config = await getEmailConfig();
  const fromEmail = config.fromEmail || config.gmailEmail || config.smtpUser;
  const fromName = config.fromName || 'QuantShift Platform';

  const mailOptions = {
    from: `"${fromName}" <${fromEmail}>`,
    replyTo: config.replyToEmail || fromEmail,
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
  const transporter = await createTransporter();
  const config = await getEmailConfig();
  const fromEmail = config.fromEmail || config.gmailEmail || config.smtpUser;

  const mailOptions = {
    from: `"QuantShift Security" <${fromEmail}>`,
    replyTo: config.replyToEmail || fromEmail,
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
  const transporter = await createTransporter();
  const config = await getEmailConfig();
  const fromEmail = config.fromEmail || config.gmailEmail || config.smtpUser;
  const fromName = config.fromName || 'QuantShift Platform';

  const mailOptions = {
    from: `"${fromName}" <${fromEmail}>`,
    replyTo: config.replyToEmail || fromEmail,
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

export async function sendUserInvitationEmail(
  email: string,
  invitedByName: string,
  invitationToken: string
) {
  const invitationUrl = `${process.env.NEXT_PUBLIC_APP_URL}/accept-invitation?token=${invitationToken}`;
  const transporter = await createTransporter();
  const config = await getEmailConfig();
  const fromEmail = config.fromEmail || config.gmailEmail || config.smtpUser;
  const fromName = config.fromName || 'QuantShift Platform';

  const mailOptions = {
    from: `"${fromName}" <${fromEmail}>`,
    replyTo: config.replyToEmail || fromEmail,
    to: email,
    subject: 'You\'re Invited to Join QuantShift',
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
            .info-box { background: #dbeafe; border-left: 4px solid #0ea5e9; padding: 15px; margin: 20px 0; }
            .warning { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; }
            .footer { text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>🎉 You're Invited!</h1>
              <p>Join QuantShift Trading Platform</p>
            </div>
            <div class="content">
              <h2>Hello,</h2>
              <p><strong>${invitedByName}</strong> has invited you to join the QuantShift Quantum Trading Intelligence Platform.</p>
              
              <div class="info-box">
                <strong>What is QuantShift?</strong>
                <p>QuantShift is an AI-driven quantum trading intelligence platform that provides advanced algorithmic trading capabilities, real-time market analysis, and comprehensive portfolio management.</p>
              </div>
              
              <p>To accept this invitation and create your account, click the button below:</p>
              
              <div style="text-align: center;">
                <a href="${invitationUrl}" class="button">Accept Invitation & Create Account</a>
              </div>
              
              <p>Or copy and paste this link into your browser:</p>
              <p style="word-break: break-all; color: #0ea5e9;">${invitationUrl}</p>
              
              <div class="warning">
                <strong>⚠️ Important Information:</strong>
                <ul>
                  <li>This invitation link will expire in 7 days</li>
                  <li>You'll need to create a password during registration</li>
                  <li>Your account will require admin approval before full access</li>
                  <li>If you didn't expect this invitation, you can safely ignore this email</li>
                </ul>
              </div>
              
              <p><strong>Next Steps:</strong></p>
              <ol>
                <li>Click the invitation link above</li>
                <li>Complete your registration with a secure password</li>
                <li>Verify your email address</li>
                <li>Wait for admin approval (you'll receive an email)</li>
                <li>Start exploring QuantShift's powerful trading features</li>
              </ol>
              
              <div class="footer">
                <p>This invitation was sent by ${invitedByName} from QuantShift.</p>
                <p>&copy; ${new Date().getFullYear()} QuantShift. All rights reserved.</p>
              </div>
            </div>
          </div>
        </body>
      </html>
    `,
    text: `You're Invited to Join QuantShift!\n\n${invitedByName} has invited you to join the QuantShift Quantum Trading Intelligence Platform.\n\nTo accept this invitation and create your account, visit:\n${invitationUrl}\n\nImportant Information:\n- This invitation link will expire in 7 days\n- You'll need to create a password during registration\n- Your account will require admin approval before full access\n\nNext Steps:\n1. Click the invitation link\n2. Complete your registration\n3. Verify your email address\n4. Wait for admin approval\n5. Start exploring QuantShift\n\nIf you didn't expect this invitation, you can safely ignore this email.\n\n© ${new Date().getFullYear()} QuantShift. All rights reserved.`,
  };

  try {
    await transporter.sendMail(mailOptions);
    return { success: true };
  } catch (error) {
    console.error('Error sending invitation email:', error);
    return { success: false, error };
  }
}
