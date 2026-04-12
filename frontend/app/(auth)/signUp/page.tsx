"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/app/contexts/AuthContext";
import { signUpSchema, type SignUpFormData } from "@/app/lib/validations/auth";
import {
    AuthFormWrapper,
    FormField,
    PasswordInput,
    OAuthButtons,
} from "@/app/components/auth";
import { Button } from "@/app/components/ui/button";
import { Loader2 } from "lucide-react";

export default function SignUpPage() {
    const { signup, setAccessToken, setUser } = useAuth();
    const router = useRouter();

    const [formData, setFormData] = useState<SignUpFormData>({
        username: "",
        email: "",
        password: "",
        confirmPassword: "",
    });
    const [fieldErrors, setFieldErrors] = useState<
        Partial<Record<keyof SignUpFormData, string>>
    >({});
    const [globalError, setGlobalError] = useState("");
    const [loading, setLoading] = useState(false);

    function updateField(field: keyof SignUpFormData, value: string) {
        setFormData((prev) => ({ ...prev, [field]: value }));
        if (fieldErrors[field]) {
            setFieldErrors((prev) => ({ ...prev, [field]: undefined }));
        }
    }

    async function handleSubmit(e: FormEvent) {
        e.preventDefault();
        setGlobalError("");
        setFieldErrors({});

        // Validate
        const result = signUpSchema.safeParse(formData);
        if (!result.success) {
            const errors: Partial<Record<keyof SignUpFormData, string>> = {};
            result.error.issues.forEach((issue) => {
                const field = issue.path[0] as keyof SignUpFormData;
                if (!errors[field]) errors[field] = issue.message;
            });
            setFieldErrors(errors);
            return;
        }

        setLoading(true);
        try {
            const res = await signup(formData.username, formData.email, formData.password);
            if (res.status === "pending_verification") {
                router.push(
                    `/verify-pending?email=${encodeURIComponent(formData.email)}`
                );
            }
        } catch (err) {
            setGlobalError(
                err instanceof Error ? err.message : "Sign up failed. Please try again."
            );
        } finally {
            setLoading(false);
        }
    }

    return (
        <AuthFormWrapper
            title="Create an account"
            description="Get started with your free account"
            error={globalError}
        >
            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
                <FormField
                    id="username"
                    label="Username"
                    placeholder="johndoe"
                    value={formData.username}
                    onChange={(v) => updateField("username", v)}
                    error={fieldErrors.username}
                    autoComplete="username"
                    disabled={loading}
                />

                <FormField
                    id="email"
                    label="Email"
                    type="email"
                    placeholder="you@example.com"
                    value={formData.email}
                    onChange={(v) => updateField("email", v)}
                    error={fieldErrors.email}
                    autoComplete="email"
                    disabled={loading}
                />

                <PasswordInput
                    id="password"
                    label="Password"
                    placeholder="Min. 8 characters"
                    value={formData.password}
                    onChange={(v) => updateField("password", v)}
                    error={fieldErrors.password}
                    autoComplete="new-password"
                    disabled={loading}
                />

                <PasswordInput
                    id="confirmPassword"
                    label="Confirm Password"
                    placeholder="Re-enter your password"
                    value={formData.confirmPassword}
                    onChange={(v) => updateField("confirmPassword", v)}
                    error={fieldErrors.confirmPassword}
                    autoComplete="new-password"
                    disabled={loading}
                />

                <Button
                    type="submit"
                    className="w-full h-10"
                    disabled={loading}
                    id="signup-btn"
                >
                    {loading ? (
                        <>
                            <Loader2 className="size-4 animate-spin" />
                            Creating account…
                        </>
                    ) : (
                        "Create Account"
                    )}
                </Button>
            </form>

            <OAuthButtons mode="signup" />

            <p className="mt-6 text-center text-sm text-muted-foreground">
                Already have an account?{" "}
                <Link
                    href="/signIn"
                    className="font-medium text-primary underline-offset-4 hover:underline"
                >
                    Sign in
                </Link>
            </p>

            <div className="mt-4 flex justify-center">
                <button
                    type="button"
                    onClick={(e) => {
                        e.preventDefault();
                        document.cookie = "has_session=1; path=/; max-age=2592000; SameSite=Lax";
                        localStorage.setItem("dummy_session", "1");
                        setAccessToken("dummy_token");
                        setUser({
                            id: "dummy_id",
                            email: "dummy@example.com",
                            name: "Dummy User",
                            avatar_url: null,
                        });
                        router.push("/analyser");
                    }}
                    className="text-xs text-muted-foreground hover:text-primary underline"
                >
                    [Dev] Dummy Sign-In Bypass
                </button>
            </div>
        </AuthFormWrapper>
    );
}
