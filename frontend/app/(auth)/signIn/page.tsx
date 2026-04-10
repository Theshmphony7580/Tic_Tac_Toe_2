"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/app/contexts/AuthContext";
import { signInSchema, type SignInFormData } from "@/app/lib/validations/auth";
import {
    AuthFormWrapper,
    FormField,
    PasswordInput,
    OAuthButtons,
} from "@/app/components/auth";
import { Button } from "@/app/components/ui/button";
import { Loader2 } from "lucide-react";

export default function SignInPage() {
    const { login } = useAuth();
    const router = useRouter();

    const [formData, setFormData] = useState<SignInFormData>({
        email: "",
        password: "",
    });
    const [fieldErrors, setFieldErrors] = useState<
        Partial<Record<keyof SignInFormData, string>>
    >({});
    const [globalError, setGlobalError] = useState("");
    const [loading, setLoading] = useState(false);

    function updateField(field: keyof SignInFormData, value: string) {
        setFormData((prev) => ({ ...prev, [field]: value }));
        // Clear field error on change
        if (fieldErrors[field]) {
            setFieldErrors((prev) => ({ ...prev, [field]: undefined }));
        }
    }

    async function handleSubmit(e: FormEvent) {
        e.preventDefault();
        setGlobalError("");
        setFieldErrors({});

        // Validate
        const result = signInSchema.safeParse(formData);
        if (!result.success) {
            const errors: Partial<Record<keyof SignInFormData, string>> = {};
            result.error.issues.forEach((issue) => {
                const field = issue.path[0] as keyof SignInFormData;
                if (!errors[field]) errors[field] = issue.message;
            });
            setFieldErrors(errors);
            return;
        }

        setLoading(true);
        try {
            const res = await login(formData.email, formData.password);
            if (res.status === "pending_verification") {
                router.push(
                    `/verify-pending?email=${encodeURIComponent(formData.email)}`
                );
            } else {
                router.push("/dashboard");
            }
        } catch (err) {
            setGlobalError(
                err instanceof Error ? err.message : "Sign in failed. Please try again."
            );
        } finally {
            setLoading(false);
        }
    }

    return (
        <AuthFormWrapper
            title="Welcome back"
            description="Sign in to your account to continue"
            error={globalError}
        >
            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
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
                    value={formData.password}
                    onChange={(v) => updateField("password", v)}
                    error={fieldErrors.password}
                    autoComplete="current-password"
                    disabled={loading}
                />

                <Button
                    type="submit"
                    className="w-full h-10"
                    disabled={loading}
                    id="signin-btn"
                >
                    {loading ? (
                        <>
                            <Loader2 className="size-4 animate-spin" />
                            Signing in…
                        </>
                    ) : (
                        "Sign In"
                    )}
                </Button>
            </form>

            <OAuthButtons mode="signin" />

            <p className="mt-6 text-center text-sm text-muted-foreground">
                Don&apos;t have an account?{" "}
                <Link
                    href="/signUp"
                    className="font-medium text-primary underline-offset-4 hover:underline"
                >
                    Sign up
                </Link>
            </p>
        </AuthFormWrapper>
    );
}
