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
// Signup Page
//
// Four-field form: name, email, password, confirm password.
// Inline validation, loading state, server error banner, link to login.
// =============================================================================

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface FieldErrors {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

export default function SignupPage() {
  const { signup } = useAuth();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // ---- Client-side validation ----
  function validate(): boolean {
    const next: FieldErrors = {};

    if (!name.trim()) {
      next.name = "Name is required.";
    } else if (name.trim().length < 2) {
      next.name = "Name must be at least 2 characters.";
    }

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

    if (!confirmPassword) {
      next.confirmPassword = "Please confirm your password.";
    } else if (password !== confirmPassword) {
      next.confirmPassword = "Passwords do not match.";
    }

    setErrors(next);
    return Object.keys(next).length === 0;
  }

  // ---- Clear a single field error on change ----
  function clearError(field: keyof FieldErrors) {
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  }

  // ---- Submit handler ----
  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setServerError(null);

    if (!validate()) return;

    setLoading(true);
    try {
      await signup(name.trim(), email.trim(), password);
      toast.success("Account created! Welcome to FlowBoard.");
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.errors?.length) {
          const fieldErrors: FieldErrors = {};
          for (const fe of err.errors) {
            if (fe.field === "name") fieldErrors.name = fe.message;
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
          <CardTitle className="text-center text-2xl">
            Create your account
          </CardTitle>
          <CardDescription className="text-center">
            Get started with FlowBoard in seconds
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

            {/* Name */}
            <div className="space-y-2">
              <Label htmlFor="signup-name">Full name</Label>
              <Input
                id="signup-name"
                type="text"
                placeholder="Jane Smith"
                autoComplete="name"
                autoFocus
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  clearError("name");
                }}
                error={!!errors.name}
                disabled={loading}
              />
              {errors.name && (
                <p className="text-xs text-error">{errors.name}</p>
              )}
            </div>

            {/* Email */}
            <div className="space-y-2">
              <Label htmlFor="signup-email">Email</Label>
              <Input
                id="signup-email"
                type="email"
                placeholder="you@company.com"
                autoComplete="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  clearError("email");
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
              <Label htmlFor="signup-password">Password</Label>
              <Input
                id="signup-password"
                type="password"
                placeholder="At least 8 characters"
                autoComplete="new-password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  clearError("password");
                }}
                error={!!errors.password}
                disabled={loading}
              />
              {errors.password && (
                <p className="text-xs text-error">{errors.password}</p>
              )}
            </div>

            {/* Confirm Password */}
            <div className="space-y-2">
              <Label htmlFor="signup-confirm-password">Confirm password</Label>
              <Input
                id="signup-confirm-password"
                type="password"
                placeholder="Repeat your password"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  clearError("confirmPassword");
                }}
                error={!!errors.confirmPassword}
                disabled={loading}
              />
              {errors.confirmPassword && (
                <p className="text-xs text-error">{errors.confirmPassword}</p>
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
              {loading ? "Creating account..." : "Create account"}
            </Button>

            <p className="text-center text-sm text-text-secondary">
              Already have an account?{" "}
              <Link
                href="/login"
                className="font-medium text-primary hover:text-accent-hover underline-offset-4 hover:underline"
              >
                Sign in
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
