"use client";

import { Suspense, useState, useEffect, useCallback, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { AuthFormWrapper } from "@/app/components/auth";
import { Button } from "@/app/components/ui/button";
import { Mail, Loader2, RefreshCw } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const RESEND_COOLDOWN = 60; // seconds

function VerifyPendingContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const email = searchParams.get("email") || "";

    const [resendStatus, setResendStatus] = useState("");
    const [resendError, setResendError] = useState("");
    const [resending, setResending] = useState(false);
    const [cooldown, setCooldown] = useState(0);
    const pollCount = useRef(0);
    const MAX_POLLS = 100
    // ── Poll verification status every 3 s ──
    const checkStatus = useCallback(async () => {
        if (!email || pollCount.current >= MAX_POLLS) return;
        pollCount.current++;
        try {
            const res = await fetch(
                `${API_BASE}/auth/verification-status?email=${encodeURIComponent(email)}`
            );
            const data = await res.json();
            if (data.verified) {
                router.push("/signIn");
            }
        } catch {
            /* ignore polling errors */
        }
    }, [email, router]);

    useEffect(() => {
        const interval = setInterval(checkStatus, 3000);
        return () => clearInterval(interval);
    }, [checkStatus]);

    // ── Cooldown timer ──
    useEffect(() => {
        if (cooldown <= 0) return;
        const timer = setTimeout(() => setCooldown((c) => c - 1), 1000);
        return () => clearTimeout(timer);
    }, [cooldown]);

    async function handleResend() {
        setResendStatus("");
        setResendError("");
        setResending(true);

        try {
            const res = await fetch(`${API_BASE}/auth/resend-verification`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email }),
            });

            if (res.status === 429) {
                setResendError("Too many requests. Please wait before trying again.");
            } else if (!res.ok) {
                setResendError("Failed to resend email. Please try again.");
            } else {
                setResendStatus("Verification email sent!");
                setCooldown(RESEND_COOLDOWN);
            }
        } catch {
            setResendError("Network error. Please try again.");
        } finally {
            setResending(false);
        }
    }

    // ── Missing email fallback ──
    if (!email) {
        return (
            <AuthFormWrapper title="Missing email" description="No email address was provided.">
                <Button asChild className="w-full h-10 mt-2">
                    <Link href="/signUp">Go to Sign Up</Link>
                </Button>
            </AuthFormWrapper>
        );
    }

    return (
        <AuthFormWrapper
            title="Check your inbox"
            description="We've sent a verification link to your email"
        >
            <div className="flex flex-col items-center text-center space-y-6">
                {/* Animated mail icon */}
                <div className="relative flex items-center justify-center">
                    <div className="absolute inset-0 rounded-full bg-primary/10 animate-ping" />
                    <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                        <Mail className="size-7 text-primary" />
                    </div>
                </div>

                {/* Email display */}
                <p className="text-sm font-medium break-all">{email}</p>

                {/* Waiting indicator */}
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Loader2 className="size-3 animate-spin" />
                    Waiting for verification…
                </div>

                <p className="text-xs text-muted-foreground leading-relaxed max-w-xs">
                    Click the link in the email to verify your account. This page will
                    automatically redirect once verified.
                </p>

                {/* Status / Error messages */}
                {resendStatus && (
                    <div className="w-full rounded-md bg-emerald-500/10 px-3 py-2 text-sm text-emerald-600">
                        {resendStatus}
                    </div>
                )}
                {resendError && (
                    <div className="w-full rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                        {resendError}
                    </div>
                )}

                {/* Resend button with cooldown */}
                <Button
                    variant="outline"
                    className="w-full h-10 gap-2"
                    onClick={handleResend}
                    disabled={resending || cooldown > 0}
                    id="resend-btn"
                >
                    {resending ? (
                        <>
                            <Loader2 className="size-4 animate-spin" />
                            Sending…
                        </>
                    ) : cooldown > 0 ? (
                        `Resend in ${cooldown}s`
                    ) : (
                        <>
                            <RefreshCw className="size-4" />
                            Resend verification email
                        </>
                    )}
                </Button>

                <p className="text-sm text-muted-foreground">
                    Wrong email?{" "}
                    <Link
                        href="/signUp"
                        className="font-medium text-primary underline-offset-4 hover:underline"
                    >
                        Sign up again
                    </Link>
                </p>
            </div>
        </AuthFormWrapper>
    );
}

export default function VerifyPendingPage() {
    return (
        <Suspense
            fallback={
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="size-6 animate-spin text-muted-foreground" />
                </div>
            }
        >
            <VerifyPendingContent />
        </Suspense>
    );
}
