import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import nodemailer from 'nodemailer';

const app = express();
const PORT = process.env.PORT || 4000;
const OTP_EXPIRY_SECONDS = Number(process.env.OTP_EXPIRY_SECONDS || 300);

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

app.use(cors({ origin: '*', credentials: true }));
app.use(express.json());

function generateOtp() {
	return Math.floor(100000 + Math.random() * 900000).toString();
}

function saveOtp(email, otp) {
	const expiresAt = Date.now() + OTP_EXPIRY_SECONDS * 1000;
	otpStore.set(email, { otp, expiresAt });
}

function verifyOtp(email, otp) {
	const record = otpStore.get(email);
	if (!record) return false;
	if (Date.now() > record.expiresAt) {
		otpStore.delete(email);
		return false;
	}
	const isValid = record.otp === otp;
	if (isValid) {
		otpStore.delete(email);
	}
	return isValid;
}

app.post('/send-otp', async (req, res) => {
	const { email } = req.body;
	if (!email) {
		return res.status(400).json({ success: false, message: 'Email is required' });
	}

	const otp = generateOtp();
	saveOtp(email, otp);

	try {
		await transporter.sendMail({
			from: `DataCue <${process.env.EMAIL_USER}>`,
			to: email,
			subject: 'Your DataCue verification code',
			html: `<p>Your one-time verification code is:</p><p style="font-size: 1.5rem; font-weight: bold; letter-spacing: 0.2rem;">${otp}</p><p>This code will expire in ${Math.floor(OTP_EXPIRY_SECONDS / 60)} minutes.</p>`,
		});
		res.json({ success: true, message: 'OTP sent successfully' });
	} catch (error) {
		console.error('Failed to send OTP email', error);
		res.status(500).json({ success: false, message: 'Failed to send OTP email' });
	}
});

app.post('/verify-otp', (req, res) => {
	const { email, otp } = req.body;
	if (!email || !otp) {
		return res.status(400).json({ success: false, message: 'Email and OTP are required' });
	}

	const isValid = verifyOtp(email, otp);
	if (!isValid) {
		return res.status(400).json({ success: false, message: 'Invalid or expired OTP' });
	}

	res.json({ success: true, message: 'OTP verified successfully' });
});

app.get('/health', (req, res) => {
	res.json({ status: 'ok', activeOtps: otpStore.size });
});

app.listen(PORT, () => {
	console.log(`Email service running on port ${PORT}`);
});
