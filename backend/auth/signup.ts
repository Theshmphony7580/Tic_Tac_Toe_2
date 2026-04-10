import { Router } from "express";
import type { Request, Response } from "express";
import prisma from "../../lib/prisma.js";
import { hashPassword } from "../../lib/auth.js";
import { generateVerificationToken } from "../../lib/auth.js";
import { sendVerificationEmail } from "../../lib/email.js";

const router = Router();

router.post("/", async (req: Request, res: Response) => {
    try {
        const { email, password, name } = req.body as {
            email?: string;
            password?: string;
            name?: string;
        };

        if (!email || !password || !name) {
            res.status(400).json({ error: "Email, password, and name are required" });
            return;
        }

        if (password.length < 8) {
            res.status(400).json({ error: "Password must be at least 8 characters" });
            return;
        }

        const existing = await prisma.user.findUnique({ where: { email } });
        if (existing) {
            res.status(409).json({ error: "Email already in use" });
            return;
        }

        const passwordHash = await hashPassword(password);
        const user = await prisma.user.create({
            data: {
                email,
                name,
                password_hash: passwordHash,
                provider: "email",
                is_verified: false,
            },
        });

        const verificationToken = generateVerificationToken(user.id, email);
        await sendVerificationEmail(email, verificationToken);

        res.status(201).json({ status: "pending_verification", email });
    } catch (err) {
        console.error("[signup]", err);
        res.status(500).json({ error: "Internal server error" });
    }
});

export default router;
