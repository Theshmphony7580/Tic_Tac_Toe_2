

import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/app/components/ui/card";
import { cn } from "@/app/lib/utils";

interface AuthFormWrapperProps {
    title: string;
    description?: string;
    error?: string;
    children: React.ReactNode;
    className?: string;
}

export function AuthFormWrapper({
    title,
    description,
    error,
    children,
    className,
}: AuthFormWrapperProps) {
    return (
        <Card
            className={cn(
                "w-full max-w-md border-none shadow-none bg-transparent",
                className
            )}
        >
            <CardHeader className="space-y-1 px-0">
                <CardTitle className="text-2xl font-bold tracking-tight">
                    {title}
                </CardTitle>
                {description && (
                    <CardDescription className="text-sm">
                        {description}
                    </CardDescription>
                )}
            </CardHeader>

            <CardContent className="px-0">
                {/* Global error banner */}
                {error && (
                    <div className="mb-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                        {error}
                    </div>
                )}
                {children}
            </CardContent>
        </Card>
    );
}
