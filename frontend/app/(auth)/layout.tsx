import { AuthLayout } from "@/app/components/auth";

export default function AuthGroupLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <AuthLayout>{children}</AuthLayout>;
}
