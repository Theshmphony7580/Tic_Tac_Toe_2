import { Router } from "express";
import type { Request, Response } from "express";
import prisma from "../../lib/prisma.js";
import { verifyVerificationToken, generateVerificationToken } from "../../lib/auth.js";
import { sendVerificationEmail } from "../../lib/email.js";
import { createSession, canResend, FRONTEND_URL } from "./helpers.js";

const router = Router();

// Verify email (user clicks magic link)
router.get("/verify-email", async (req: Request, res: Response) => {
    try {
        const token = req.query.token as string | undefined;
        if (!token) {
            res.redirect(`${FRONTEND_URL}/error?msg=Missing+verification+token`);
            return;
        }

        let payload: { sub: string; email: string };
        try {
            payload = verifyVerificationToken(token);
        } catch {
            res.redirect(`${FRONTEND_URL}/error?msg=Invalid+or+expired+verification+link`);
            return;
        }

        const user = await prisma.user.findUnique({ where: { id: payload.sub } });
        if (!user) {
            res.redirect(`${FRONTEND_URL}/error?msg=User+not+found`);
            return;
        }

        if (user.is_verified) {
            const accessToken = await createSession(user.id, res, req);
            res.redirect(`${FRONTEND_URL}/dashboard?token=${accessToken}`);
            return;
        }

        await prisma.user.update({
            where: { id: payload.sub },
            data: { is_verified: true },
        });

        const accessToken = await createSession(user.id, res, req);
        res.redirect(`${FRONTEND_URL}/dashboard?token=${accessToken}`);
    } catch (err) {
        console.error("[verify-email]", err);
        res.redirect(`${FRONTEND_URL}/error?msg=Verification+failed`);
    }
});

// Resend verification email (rate limited: 3 per 30 min)
router.post("/resend-verification", async (req: Request, res: Response) => {
    try {
        const { email } = req.body as { email?: string };
        if (!email) {
            res.status(400).json({ error: "Email is required" });
            return;
        }

        if (!canResend(email)) {
            res.status(429).json({ error: "Too many requests. Try again in 30 minutes." });
            return;
        }

        const user = await prisma.user.findUnique({ where: { email } });
        if (!user || user.is_verified) {
            res.json({ status: "ok" });
            return;
        }

        const verificationToken = generateVerificationToken(user.id, email);
        await sendVerificationEmail(email, verificationToken);
        res.json({ status: "ok" });
    } catch (err) {
        console.error("[resend-verification]", err);
        res.status(500).json({ error: "Internal server error" });
    }
});

// Poll verification status
router.get("/verification-status", async (req: Request, res: Response) => {
    try {
        const email = req.query.email as string | undefined;
        if (!email) {
            res.status(400).json({ error: "Email is required" });
            return;
        }

        const user = await prisma.user.findUnique({
            where: { email },
            select: { is_verified: true },
        });

        res.json({ verified: user?.is_verified ?? false });
    } catch (err) {
        console.error("[verification-status]", err);
        res.status(500).json({ error: "Internal server error" });
    }
});

export default router;
