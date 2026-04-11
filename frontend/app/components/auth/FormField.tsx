

import { Input } from "@/app/components/ui/input";
import { Label } from "@/app/components/ui/label";
import { cn } from "@/app/lib/utils";

interface FormFieldProps {
    id: string;
    label: string;
    type?: string;
    placeholder?: string;
    value: string;
    onChange: (value: string) => void;
    error?: string;
    autoComplete?: string;
    disabled?: boolean;
    className?: string;
}

export function FormField({
    id,
    label,
    type = "text",
    placeholder,
    value,
    onChange,
    error,
    autoComplete,
    disabled,
    className,
}: FormFieldProps) {
    return (
        <div className={cn("space-y-2", className)}>
            <Label htmlFor={id}>{label}</Label>
            <Input
                id={id}
                type={type}
                placeholder={placeholder}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                autoComplete={autoComplete}
                disabled={disabled}
                aria-invalid={!!error}
                className={cn(
                    "h-10",
                    error && "border-destructive focus-visible:ring-destructive/20"
                )}
            />
            {error && (
                <p className="text-xs text-destructive font-medium">{error}</p>
            )}
        </div>
    );
}
