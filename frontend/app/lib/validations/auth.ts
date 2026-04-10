import { z } from "zod";

// ── Sign In ──────────────────────────────────────────────────
export const signInSchema = z.object({
    email: z
        .string()
        .min(1, "Email is required")
        .email("Please enter a valid email address"),
    password: z
        .string()
        .min(1, "Password is required")
        .min(8, "Password must be at least 8 characters"),
});

export type SignInFormData = z.infer<typeof signInSchema>;

// ── Sign Up ──────────────────────────────────────────────────
export const signUpSchema = z
    .object({
        username: z
            .string()
            .min(1, "Username is required")
            .min(3, "Username must be at least 3 characters")
            .max(30, "Username must be at most 30 characters")
            .regex(
                /^[a-zA-Z0-9_]+$/,
                "Username can only contain letters, numbers, and underscores"
            ),
        email: z
            .string()
            .min(1, "Email is required")
            .email("Please enter a valid email address"),
        password: z
            .string()
            .min(1, "Password is required")
            .min(8, "Password must be at least 8 characters")
            .regex(/[A-Z]/, "Password must include at least one uppercase letter")
            .regex(/[a-z]/, "Password must include at least one lowercase letter")
            .regex(/[0-9]/, "Password must include at least one number"),
        confirmPassword: z.string().min(1, "Please confirm your password"),
    })
    .refine((data) => data.password === data.confirmPassword, {
        message: "Passwords do not match",
        path: ["confirmPassword"],
    });

export type SignUpFormData = z.infer<typeof signUpSchema>;
