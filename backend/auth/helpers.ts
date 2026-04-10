import type { Request, Response } from "express";
import prisma from "../../lib/prisma.js";
import { generateAccessToken, generateRefreshToken, hashToken } from "../../lib/auth.js";

export const FRONTEND_URL = process.env.FRONTEND_URL || "http://localhost:3001";

const REFRESH_EXPIRY_DAYS = 30;

export async function createSession(
    userId: string,
    res: Response,
    req: Request
): Promise<string> {
    const accessToken = generateAccessToken(userId)   // 15min expiry
    const rawRefresh = generateRefreshToken()
    const tokenHash = hashToken(rawRefresh)
    const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)

    await prisma.refreshToken.create({
        data: {
            userId,
            token_hash: tokenHash,
            device_name: req.headers["user-agent"]?.slice(0, 255) ?? null,
            ip_address: (req.headers["x-forwarded-for"] as string)
                ?.split(",")[0]?.trim() ?? req.socket.remoteAddress ?? null,
            expires_at: expiresAt,
        },
    })

    const isProd = process.env.NODE_ENV === "production"

    // ✅ Access token in HttpOnly cookie
    res.cookie("access_token", accessToken, {
        httpOnly: true,
        secure: isProd,
        sameSite: "lax",
        path: "/",
        maxAge: 15 * 60 * 1000, // 15 minutes
    })

    // ✅ Refresh token in HttpOnly cookie (scoped path)
    res.cookie("refresh_token", rawRefresh, {
        httpOnly: true,
        secure: isProd,
        sameSite: "lax",          // lax, not strict — OAuth redirects need this
        path: "/auth/refresh",    // only sent to refresh endpoint
        maxAge: 30 * 24 * 60 * 60 * 1000,
    })

    return accessToken;
}

// In-memory rate limit for resend-verification
const resendTracker = new Map<string, { count: number; windowStart: number }>();
const RESEND_MAX = 3;
const RESEND_WINDOW_MS = 30 * 60 * 1000;

export function canResend(email: string): boolean {
    const now = Date.now();
    const entry = resendTracker.get(email);
    if (!entry || now - entry.windowStart > RESEND_WINDOW_MS) {
        resendTracker.set(email, { count: 1, windowStart: now });
        return true;
    }
    if (entry.count >= RESEND_MAX) return false;
    entry.count++;
    return true;
}