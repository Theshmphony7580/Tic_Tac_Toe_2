import { Router } from "express";
import type { Request, Response } from "express";
import prisma from "../../lib/prisma.js";
import { createSession, FRONTEND_URL } from "./helpers.js";

const router = Router();

const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID;
const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET;
const APP_URL = process.env.APP_URL || "http://localhost:3000";
const CALLBACK_URL = `${APP_URL}/auth/google/callback`;

interface GoogleTokenResponse {
    access_token: string;
    id_token: string;
    token_type: string;
    expires_in: number;
    refresh_token?: string;
}

interface GoogleUserInfo {
    sub: string;
    email: string;
    email_verified: boolean;
    name: string;
    picture?: string;
}

if (GOOGLE_CLIENT_ID && GOOGLE_CLIENT_SECRET) {
    // Step 1: Redirect to Google consent screen
    router.get("/google", (_req: Request, res: Response) => {
        const params = new URLSearchParams({
            client_id: GOOGLE_CLIENT_ID,
            redirect_uri: CALLBACK_URL,
            response_type: "code",
            scope: "openid email profile",
            access_type: "offline",
            prompt: "consent",
        });

        res.redirect(`https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`);
    });

    // Step 2: Handle callback — exchange code for tokens, fetch profile, upsert user
    router.get("/google/callback", async (req: Request, res: Response) => {
        try {
            const code = req.query.code as string | undefined;
            const error = req.query.error as string | undefined;

            if (error || !code) {
                res.redirect(`${FRONTEND_URL}/error?msg=Google+login+cancelled`);
                return;
            }

            // Exchange authorization code for tokens
            const tokenRes = await fetch("https://oauth2.googleapis.com/token", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: new URLSearchParams({
                    code,
                    client_id: GOOGLE_CLIENT_ID,
                    client_secret: GOOGLE_CLIENT_SECRET,
                    redirect_uri: CALLBACK_URL,
                    grant_type: "authorization_code",
                }),
            });

            if (!tokenRes.ok) {
                console.error("[google] Token exchange failed:", await tokenRes.text());
                res.redirect(`${FRONTEND_URL}/error?msg=Google+login+failed`);
                return;
            }

            const tokens = (await tokenRes.json()) as GoogleTokenResponse;

            // Fetch user profile from Google
            const userRes = await fetch("https://www.googleapis.com/oauth2/v3/userinfo", {
                headers: { Authorization: `Bearer ${tokens.access_token}` },
            });

            if (!userRes.ok) {
                console.error("[google] Failed to fetch user info:", await userRes.text());
                res.redirect(`${FRONTEND_URL}/error?msg=Google+login+failed`);
                return;
            }

            const profile = (await userRes.json()) as GoogleUserInfo;

            if (!profile.email) {
                res.redirect(`${FRONTEND_URL}/error?msg=No+email+from+Google`);
                return;
            }

            // Upsert user
            let user = await prisma.user.findUnique({ where: { email: profile.email } });
            if (!user) {
                user = await prisma.user.create({
                    data: {
                        email: profile.email,
                        name: profile.name ?? profile.email.split("@")[0] ?? "User",
                        avatar_url: profile.picture ?? null,
                        provider: "google",
                        is_verified: true,
                    },
                });
            } else {
                user = await prisma.user.update({
                    where: { email: profile.email },
                    data: {
                        name: user.name ?? profile.name,
                        avatar_url: user.avatar_url ?? profile.picture ?? null,
                        is_verified: true,
                    },
                });
            }

            // Upsert OAuthAccount
            await prisma.oAuthAccount.upsert({
                where: {
                    provider_provider_account_id: {
                        provider: "google",
                        provider_account_id: profile.sub,
                    },
                },
                create: {
                    userId: user.id,
                    provider: "google",
                    provider_account_id: profile.sub,
                    access_token: tokens.access_token,
                    refresh_token: tokens.refresh_token ?? null,
                },
                update: {
                    access_token: tokens.access_token,
                    refresh_token: tokens.refresh_token ?? null,
                },
            });

            // ✅ No token in URL — cookies handle everything
            const accessToken = await createSession(user.id, res, req)
            res.redirect(`${FRONTEND_URL}/dashboard`)
        } catch (err) {
            console.error("[google-callback]", err);
            res.redirect(`${FRONTEND_URL}/error?msg=Google+login+failed`);
        }
    });
} else {
    console.warn("[auth] Google OAuth not configured — missing GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET");
}

export default router;
