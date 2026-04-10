import { Router } from "express";
import type { Request, Response } from "express";
import prisma from "../../lib/prisma.js";
import { verifyPassword } from "../../lib/auth.js";
import { createSession } from "./helpers.js";

const router = Router();

router.post("/", async (req: Request, res: Response) => {
    try {
        const { email, password } = req.body as {
            email?: string;
            password?: string;
        };

        if (!email || !password) {
            res.status(400).json({ error: "Email and password are required" });
            return;
        }

        const user = await prisma.user.findUnique({ where: { email } });
        if (!user || !user.password_hash) {
            res.status(401).json({ error: "Invalid email or password" });
            return;
        }

        if (!user.is_verified) {
            res.status(403).json({ status: "pending_verification", email });
            return;
        }

        const valid = await verifyPassword(password, user.password_hash);
        if (!valid) {
            res.status(401).json({ error: "Invalid email or password" });
            return;
        }

        const accessToken = await createSession(user.id, res, req);
        res.json({
            accessToken,
            user: { id: user.id, email: user.email, name: user.name, avatar_url: user.avatar_url },
        });
    } catch (err) {
        console.error("[signin]", err);
        res.status(500).json({ error: "Internal server error" });
    }
});

export default router;
