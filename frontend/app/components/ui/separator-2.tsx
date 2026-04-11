import { cn } from "@/app/lib/utils";

export default function Separator({ className }: { className?: string }) {
    return (
        <div
            className={cn(
                "h-8 w-full",
                "[background-size:10px_10px] [background-image:repeating-linear-gradient(315deg,rgba(255,255,255,0.2)_0,rgba(255,255,255,0.2)_1px,transparent_1px,transparent_50%)]",
                className
            )}
        />
    );
}

