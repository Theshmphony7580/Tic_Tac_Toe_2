"use client";

import { useState } from "react";
import { Input } from "@/app/components/ui/input";
import { Label } from "@/app/components/ui/label";
import { Button } from "@/app/components/ui/button";
import { Eye, EyeOff } from "lucide-react";
import { cn } from "@/app/lib/utils";

interface PasswordInputProps {
    id: string;
    label: string;
    placeholder?: string;
    value: string;
    onChange: (value: string) => void;
    error?: string;
    autoComplete?: string;
    disabled?: boolean;
    className?: string;
}

export function PasswordInput({
    id,
    label,
    placeholder = "••••••••",
    value,
    onChange,
    error,
    autoComplete,
    disabled,
    className,
}: PasswordInputProps) {
    const [visible, setVisible] = useState(false);

    return (
        <div className={cn("space-y-2", className)}>
            <Label htmlFor={id}>{label}</Label>
            <div className="relative">
                <Input
                    id={id}
                    type={visible ? "text" : "password"}
                    placeholder={placeholder}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    autoComplete={autoComplete}
                    disabled={disabled}
                    aria-invalid={!!error}
                    className={cn(
                        "h-10 pr-10",
                        error && "border-destructive focus-visible:ring-destructive/20"
                    )}
                />
                <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="absolute right-0 top-0 h-10 w-10 text-muted-foreground hover:text-foreground"
                    onClick={() => setVisible((v) => !v)}
                    tabIndex={-1}
                    aria-label={visible ? "Hide password" : "Show password"}
                >
                    {visible ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </Button>
            </div>
            {error && (
                <p className="text-xs text-destructive font-medium">{error}</p>
            )}
        </div>
    );
}
