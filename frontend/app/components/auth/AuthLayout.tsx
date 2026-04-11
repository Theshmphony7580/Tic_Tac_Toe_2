import Image from "next/image";

export function AuthLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className="flex min-h-screen">
            {/* ── Left panel (hidden on mobile) ── */}
            <div className="relative hidden lg:flex lg:w-1/2 items-center justify-center bg-muted/40 p-12">
                {/* Gradient overlay */}
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/10" />

                <div className="relative z-10 flex flex-col items-center gap-8 max-w-lg">
                    <Image
                        src="/auth-hero.png"
                        alt="SEO Analytics illustration"
                        width={480}
                        height={480}
                        className="rounded-2xl object-cover"
                        priority
                    />
                </div>
            </div>

            {/* ── Right panel (form area) ── */}
            <div className="flex flex-1 items-center justify-center px-6 py-12 lg:px-16">
                <div className="w-full max-w-md">{children}</div>
            </div>
        </div>
    );
}
