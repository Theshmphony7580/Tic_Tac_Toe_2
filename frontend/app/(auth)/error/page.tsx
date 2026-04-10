"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { AuthFormWrapper } from "@/app/components/auth";
import { Button } from "@/app/components/ui/button";
import { AlertCircle, Loader2 } from "lucide-react";

function ErrorContent() {
    const searchParams = useSearchParams();
    const msg = searchParams.get("msg") || "An unexpected error occurred";

    return (
        <AuthFormWrapper title="Something went wrong">
            <div className="flex flex-col items-center text-center space-y-6">
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-destructive/10">
                    <AlertCircle className="size-7 text-destructive" />
                </div>

                <p className="text-sm text-muted-foreground max-w-xs">{msg}</p>

                <Button asChild className="w-full h-10" id="error-back-btn">
                    <Link href="/signIn">Back to Sign In</Link>
                </Button>
            </div>
        </AuthFormWrapper>
    );
}

export default function ErrorPage() {
    return (
        <Suspense
            fallback={
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="size-6 animate-spin text-muted-foreground" />
                </div>
            }
        >
            <ErrorContent />
        </Suspense>
    );
}
