"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { useAuth, ApiError } from "@/contexts/auth-context";
import { Logo } from "@/components/logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

// =============================================================================
// Login Page
//
// Linear-inspired minimal dark card. Email + password form with inline
// validation errors, loading spinner on submit, and a link to signup.
// =============================================================================

/** Simple email regex -- good enough for client-side pre-validation. */
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface FieldErrors {
  email?: string;
  password?: string;
}

export default function LoginPage() {
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // ---- Client-side validation ----
  function validate(): boolean {
    const next: FieldErrors = {};

    if (!email.trim()) {
      next.email = "Email is required.";
    } else if (!EMAIL_RE.test(email)) {
      next.email = "Please enter a valid email address.";
    }

    if (!password) {
      next.password = "Password is required.";
    } else if (password.length < 8) {
      next.password = "Password must be at least 8 characters.";
    }

    setErrors(next);
    return Object.keys(next).length === 0;
  }

  // ---- Submit handler ----
  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setServerError(null);

    if (!validate()) return;

    setLoading(true);
    try {
      await login(email, password);
      toast.success("Welcome back!");
    } catch (err) {
      if (err instanceof ApiError) {
        // Map field-level errors from the server
        if (err.errors?.length) {
          const fieldErrors: FieldErrors = {};
          for (const fe of err.errors) {
            if (fe.field === "email") fieldErrors.email = fe.message;
            if (fe.field === "password") fieldErrors.password = fe.message;
          }
          setErrors(fieldErrors);
        }
        setServerError(err.message);
        toast.error(err.message);
      } else {
        const message = "Something went wrong. Please try again.";
        setServerError(message);
        toast.error(message);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-center gap-8">
      {/* Logo */}
      <Logo size="lg" />

      <Card className="w-full">
        <CardHeader className="space-y-1 pb-4">
          <CardTitle className="text-center text-2xl">Sign in</CardTitle>
          <CardDescription className="text-center">
            Enter your credentials to access your workspace
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit} noValidate>
          <CardContent className="space-y-4">
            {/* Server-level error banner */}
            {serverError && (
              <div className="rounded-md border border-error/30 bg-error-muted px-3 py-2 text-sm text-error">
                {serverError}
              </div>
            )}

            {/* Email */}
            <div className="space-y-2">
              <Label htmlFor="login-email">Email</Label>
              <Input
                id="login-email"
                type="email"
                placeholder="you@company.com"
                autoComplete="email"
                autoFocus
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (errors.email) setErrors((p) => ({ ...p, email: undefined }));
                }}
                error={!!errors.email}
                disabled={loading}
              />
              {errors.email && (
                <p className="text-xs text-error">{errors.email}</p>
              )}
            </div>

            {/* Password */}
            <div className="space-y-2">
              <Label htmlFor="login-password">Password</Label>
              <Input
                id="login-password"
                type="password"
                placeholder="Enter your password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errors.password)
                    setErrors((p) => ({ ...p, password: undefined }));
                }}
                error={!!errors.password}
                disabled={loading}
              />
              {errors.password && (
                <p className="text-xs text-error">{errors.password}</p>
              )}
            </div>
          </CardContent>

          <CardFooter className="flex flex-col gap-4 pt-2">
            <Button
              type="submit"
              size="lg"
              loading={loading}
              className="w-full"
            >
              {loading ? "Signing in..." : "Sign in"}
            </Button>

            <p className="text-center text-sm text-text-secondary">
              Don&apos;t have an account?{" "}
              <Link
                href="/signup"
                className="font-medium text-primary hover:text-accent-hover underline-offset-4 hover:underline"
              >
                Create one
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
