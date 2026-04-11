"use client";

import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const SESSION_COOKIE = "has_session";
const SESSION_MAX_AGE_DAYS = 30;

function setSessionCookie() {
    document.cookie = `${SESSION_COOKIE}=1; path=/; max-age=${SESSION_MAX_AGE_DAYS * 24 * 60 * 60}; SameSite=Lax`;
}

function clearSessionCookie() {
    document.cookie = `${SESSION_COOKIE}=; path=/; max-age=0; SameSite=Lax`;
}

interface User {
    id: string;
    email: string;
    name: string | null;
    avatar_url: string | null;
}

interface AuthContextType {
    user: User | null;
    accessToken: string | null;
    loading: boolean;
    login: (email: string, password: string) => Promise<{ status: string; email?: string }>;
    signup: (name: string, email: string, password: string) => Promise<{ status: string; email?: string }>;
    logout: () => Promise<void>;
    refreshSession: () => Promise<boolean>;
    apiFetch: (url: string, options?: RequestInit) => Promise<Response>;
    setAccessToken: (token: string) => void;
    setUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);

    const accessTokenRef = useRef<string | null>(null)
    const [accessToken, setAccessToken] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const refreshingRef = useRef(false);
    // If arriving from OAuth redirect with ?token= in the URL, skip auto-refresh
    // to prevent it from racing against the dashboard's /auth/me fetch.

    useEffect(() => {
        accessTokenRef.current = accessToken
    }, [accessToken])

    const refreshSession = useCallback(async (): Promise<boolean> => {
        if (refreshingRef.current) return false;
        refreshingRef.current = true;
        try {
            const res = await fetch(`${API_BASE}/auth/refresh`, {
                method: "POST",
                credentials: "include",
            });
            if (!res.ok) {
                setUser(null);
                setAccessToken(null);
                clearSessionCookie();
                return false;
            }
            const data = await res.json();
            setAccessToken(data.accessToken);
            setUser(data.user);
            localStorage.setItem("cached_user", JSON.stringify(data.user))
            setSessionCookie();
            return true;
        } catch {
            setUser(null);
            setAccessToken(null);
            clearSessionCookie();
            return false;
        } finally {
            refreshingRef.current = false;
        }
    }, []);

    const login = useCallback(async (email: string, password: string) => {
        const res = await fetch(`${API_BASE}/auth/signin`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ email, password }),
        });
        const data = await res.json();
        if (!res.ok) {
            if (data.status === "pending_verification") {
                return { status: "pending_verification", email: data.email };
            }
            throw new Error(data.error || "Sign in failed");
        }
        setAccessToken(data.accessToken);
        setUser(data.user);
        setSessionCookie();
        return { status: "ok" };
    }, []);

    const signup = useCallback(async (name: string, email: string, password: string) => {
        const res = await fetch(`${API_BASE}/auth/signup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password, name }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Sign up failed");
        return { status: data.status, email: data.email };
    }, []);

    const logout = useCallback(async () => {
        await fetch(`${API_BASE}/auth/logout`, {
            method: "POST",
            credentials: "include",
            headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
        })
        localStorage.removeItem("cached_user")
        setUser(null)
        setAccessToken(null)
        clearSessionCookie()
        window.location.href = "/signIn" // hard redirect, clears all state
    }, [accessToken])

    const apiFetch = useCallback(
        async (url: string, options: RequestInit = {}): Promise<Response> => {
            const headers = new Headers(options.headers);
            if (accessTokenRef.current) {
                headers.set("Authorization", `Bearer ${accessTokenRef.current}`)
            }

            let res = await fetch(`${API_BASE}${url}`, {
                ...options,
                headers,
                credentials: "include",
            });

            // If 401, try refreshing once
            if (res.status === 401) {
                const refreshed = await refreshSession();
                if (refreshed) {
                    headers.set("Authorization", `Bearer ${accessTokenRef.current}`)
                    res = await fetch(`${API_BASE}${url}`, {
                        ...options,
                        headers,
                        credentials: "include",
                    });
                }
            }

            return res;
        },
        [accessToken, refreshSession]
    );

    // Auto-refresh on mount
    useEffect(() => {
        // Load from cache immediately on mount to avoid flicker
        try {
            const cached = localStorage.getItem("cached_user")
            if (cached) setUser(JSON.parse(cached))
        } catch { }

        const params = new URLSearchParams(window.location.search)
        const token = params.get("token")

        if (token) {
            setAccessToken(token)
            // Clean URL
            window.history.replaceState({}, "", window.location.pathname)
            // Still need to fetch user
            fetch(`${API_BASE}/auth/me`, {
                credentials: "include",
                headers: { Authorization: `Bearer ${token}` },
            })
                .then(r => r.json())
                .then(data => { if (data.user) setUser(data.user) })
                .finally(() => setLoading(false))
        } else {
            refreshSession().finally(() => setLoading(false))
        }
    }, []) // only on mount

    return (
        <AuthContext.Provider
            value={{
                user,
                accessToken,
                loading,
                login,
                signup,
                logout,
                refreshSession,
                apiFetch,
                setAccessToken,
                setUser,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be used within AuthProvider");
    return ctx;
}
