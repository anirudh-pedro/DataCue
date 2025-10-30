import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import nodemailer from 'nodemailer';

const app = express();
const PORT = process.env.PORT || 4000;
const OTP_EXPIRY_SECONDS = Number(process.env.OTP_EXPIRY_SECONDS || 300);
const MAX_OTP_ATTEMPTS = 3;
const RATE_LIMIT_WINDOW_MS = 60000; // 1 minute
const MAX_REQUESTS_PER_WINDOW = 5;

if (!process.env.EMAIL_USER || !process.env.EMAIL_APP_PASSWORD) {
	console.warn('Warning: EMAIL_USER or EMAIL_APP_PASSWORD not set. Email sending will fail.');
}

const transporter = nodemailer.createTransport({
	service: 'gmail',
	auth: {
		user: process.env.EMAIL_USER,
		pass: process.env.EMAIL_APP_PASSWORD,
	},
});

const otpStore = new Map();
const rateLimitStore = new Map();

// Cleanup expired OTPs every 5 minutes
setInterval(() => {
	const now = Date.now();
	let cleaned = 0;
	for (const [email, data] of otpStore.entries()) {
		if (now > data.expiresAt) {
			otpStore.delete(email);
			cleaned++;
		}
	}
	if (cleaned > 0) {
		console.log(`Cleaned ${cleaned} expired OTP(s)`);
	}
}, 5 * 60 * 1000);

// Cleanup rate limit data every 2 minutes
setInterval(() => {
	const now = Date.now();
	let cleaned = 0;
	for (const [email, data] of rateLimitStore.entries()) {
		if (now > data.resetAt) {
			rateLimitStore.delete(email);
			cleaned++;
		}
	}
	if (cleaned > 0) {
		console.log(`Cleaned ${cleaned} rate limit record(s)`);
	}
}, 2 * 60 * 1000);

app.use(cors({ origin: '*', credentials: true }));
app.use(express.json());

function generateOtp() {
	return Math.floor(100000 + Math.random() * 900000).toString();
}

function saveOtp(email, otp) {
	const expiresAt = Date.now() + OTP_EXPIRY_SECONDS * 1000;
	otpStore.set(email, { otp, expiresAt, attempts: 0, createdAt: Date.now() });
}

function verifyOtp(email, otp) {
	const record = otpStore.get(email);
	if (!record) return { valid: false, message: 'No OTP found for this email' };
	
	if (Date.now() > record.expiresAt) {
		otpStore.delete(email);
		return { valid: false, message: 'OTP has expired' };
	}
	
	if (record.attempts >= MAX_OTP_ATTEMPTS) {
		otpStore.delete(email);
		return { valid: false, message: 'Too many failed attempts. Please request a new OTP' };
	}
	
	if (record.otp !== otp) {
		record.attempts++;
		return { valid: false, message: `Invalid OTP. ${MAX_OTP_ATTEMPTS - record.attempts} attempts remaining` };
	}
	
	// Success - remove OTP
	otpStore.delete(email);
	return { valid: true, message: 'OTP verified successfully' };
}

function checkRateLimit(email) {
	const now = Date.now();
	const record = rateLimitStore.get(email);
	
	if (!record) {
		rateLimitStore.set(email, { count: 1, resetAt: now + RATE_LIMIT_WINDOW_MS });
		return { allowed: true };
	}
	
	if (now > record.resetAt) {
		rateLimitStore.set(email, { count: 1, resetAt: now + RATE_LIMIT_WINDOW_MS });
		return { allowed: true };
	}
	
	if (record.count >= MAX_REQUESTS_PER_WINDOW) {
		return { 
			allowed: false, 
			resetIn: Math.ceil((record.resetAt - now) / 1000) 
		};
	}
	
	record.count++;
	return { allowed: true };
}

app.post('/send-otp', async (req, res) => {
	const { email } = req.body;
	if (!email) {
		return res.status(400).json({ success: false, message: 'Email is required' });
	}

	// Check rate limit
	const rateLimit = checkRateLimit(email);
	if (!rateLimit.allowed) {
		return res.status(429).json({ 
			success: false, 
			message: `Too many requests. Please try again in ${rateLimit.resetIn} seconds` 
		});
	}

	const otp = generateOtp();
	saveOtp(email, otp);

	try {
		await transporter.sendMail({
			from: `DataCue <${process.env.EMAIL_USER}>`,
			to: email,
			subject: 'Your DataCue verification code',
			html: `
				<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
					<h2 style="color: #333;">DataCue Email Verification</h2>
					<p>Your one-time verification code is:</p>
					<p style="font-size: 2rem; font-weight: bold; letter-spacing: 0.3rem; color: #0066cc; text-align: center; padding: 20px; background: #f5f5f5; border-radius: 8px;">
						${otp}
					</p>
					<p style="color: #666;">This code will expire in ${Math.floor(OTP_EXPIRY_SECONDS / 60)} minutes.</p>
					<p style="color: #999; font-size: 0.9rem;">If you didn't request this code, please ignore this email.</p>
				</div>
			`,
		});
		console.log(`OTP sent successfully to ${email}`);
		res.json({ success: true, message: 'OTP sent successfully' });
	} catch (error) {
		console.error('Failed to send OTP email', error);
		otpStore.delete(email); // Remove OTP if email failed
		res.status(500).json({ success: false, message: 'Failed to send OTP email' });
	}
});

app.post('/verify-otp', (req, res) => {
	const { email, otp } = req.body;
	if (!email || !otp) {
		return res.status(400).json({ success: false, message: 'Email and OTP are required' });
	}

	const result = verifyOtp(email, otp);
	
	if (!result.valid) {
		console.log(`OTP verification failed for ${email}: ${result.message}`);
		return res.status(400).json({ success: false, message: result.message });
	}

	console.log(`OTP verified successfully for ${email}`);
	res.json({ success: true, message: result.message });
});

app.get('/health', (req, res) => {
	res.json({ 
		status: 'ok', 
		activeOtps: otpStore.size,
		rateLimitedEmails: rateLimitStore.size,
		uptime: process.uptime()
	});
});

app.listen(PORT, () => {
	console.log(`Email service running on port ${PORT}`);
});
