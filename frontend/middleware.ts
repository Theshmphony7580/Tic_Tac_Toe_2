import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Routes that require authentication
const protectedRoutes = ["/dashboard", "/analyser", "/deep-analysis", "/keywords-tracking"];

// Routes only for unauthenticated users
const authRoutes = ["/", "/signIn", "/signUp"];

function isProtectedRoute(pathname: string): boolean {
    return protectedRoutes.some(
        (route) => pathname === route || pathname.startsWith(route + "/")
    );
}

function isAuthRoute(pathname: string): boolean {
    return authRoutes.some(
        (route) => pathname === route || (route !== "/" && pathname.startsWith(route + "/"))
    );
}

export function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;
    const hasSession = request.cookies.get("has_session")?.value === "1";

    // Unauthenticated user trying to access protected route → redirect to sign in
    // Exception: allow OAuth/verification callback with ?token= param
    if (isProtectedRoute(pathname) && !hasSession) {
        const hasTokenParam = request.nextUrl.searchParams.has("token");
        if (!hasTokenParam) {
            const signInUrl = new URL("/signIn", request.url);
            signInUrl.searchParams.set("callbackUrl", pathname);
            return NextResponse.redirect(signInUrl);
        }
    }

    // Authenticated user trying to access auth pages → redirect to dashboard
    if (isAuthRoute(pathname) && hasSession) {
        return NextResponse.redirect(new URL("/analyser", request.url));
    }

    return NextResponse.next();
}

export const config = {
    matcher: [
        /*
         * Match all request paths except:
         * - _next/static (static files)
         * - _next/image (image optimization)
         * - favicon.ico, sitemap.xml, robots.txt
         * - api routes
         */
        "/((?!_next/static|_next/image|favicon\\.ico|sitemap\\.xml|robots\\.txt|api).*)",
    ],
};
