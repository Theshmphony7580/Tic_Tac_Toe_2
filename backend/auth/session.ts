import { Router } from "express";
import type { Request, Response } from "express";
import prisma from "../../lib/prisma.js";
import { hashToken } from "../../lib/auth.js";
import { requireAuth } from "../../middleware/auth.middleware.js";
import { createSession } from "./helpers.js";

const router = Router();

// Refresh token (rotation)
router.post("/refresh", async (req: Request, res: Response) => {
    try {
        const rawToken = req.cookies?.refresh_token as string | undefined
        if (!rawToken) {
            res.status(401).json({ error: "No refresh token" })
            return
        }

        const tokenHash = hashToken(rawToken)
        const storedToken = await prisma.refreshToken.findUnique({
            where: { token_hash: tokenHash },
            include: { user: true },
        })

        if (!storedToken || storedToken.expires_at < new Date()) {
            if (storedToken) await prisma.refreshToken.delete({ where: { id: storedToken.id } })
            res.clearCookie("refresh_token", { path: "/auth/refresh" })
            res.clearCookie("access_token", { path: "/" })
            res.status(401).json({ error: "Session expired, please log in again" })
            return
        }

        await prisma.refreshToken.delete({ where: { id: storedToken.id } })

        // ✅ createSession sets cookies AND returns the raw access token
        const accessToken = await createSession(storedToken.userId, res, req)

        const { user } = storedToken
        res.json({
            accessToken, // ✅ send it back so frontend can store in memory
            user: {
                id: user.id,
                email: user.email,
                name: user.name,
                avatar_url: user.avatar_url,
            },
        })
    } catch (err) {
        console.error("[refresh]", err)
        res.status(401).json({ error: "Token refresh failed" })
    }
})

// Logout (protected)
router.post("/logout", requireAuth, async (req: Request, res: Response) => {
    try {
        const rawToken = req.cookies?.refresh_token as string | undefined;
        if (rawToken) {
            const tokenHash = hashToken(rawToken);
            await prisma.refreshToken.deleteMany({ where: { token_hash: tokenHash } });
        }
        res.clearCookie("refresh_token", { path: "/auth/refresh" });
        res.clearCookie("access_token", { path: "/" }); // ✅ clear this too
        res.json({ status: "logged_out" });
    } catch (err) {
        console.error("[logout]", err);
        res.status(500).json({ error: "Internal server error" });
    }
});
// Get current user (protected)
router.get("/me", requireAuth, async (req: Request, res: Response) => {
    try {
        const user = await prisma.user.findUnique({
            where: { id: req.userId as string },
            select: {
                id: true,
                email: true,
                name: true,
                avatar_url: true,
                provider: true,
                is_verified: true,
                createdAt: true,
            },
        });

        if (!user) {
            res.status(404).json({ error: "User not found" });
            return;
        }

        res.json({ user });
    } catch (err) {
        console.error("[me]", err);
        res.status(500).json({ error: "Internal server error" });
    }
});

export default router;
