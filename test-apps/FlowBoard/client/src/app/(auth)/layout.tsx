// =============================================================================
// Auth Layout -- centered card on dark background, no sidebar/nav.
//
// Used for /login and /signup routes. The background uses a subtle radial
// gradient with a hint of brand violet for depth.
//
// Wraps with AuthProvider so login/signup pages can use useAuth() for
// login(), signup(), and session rehydration.
// =============================================================================

import { AuthProvider } from "@/contexts/auth-context";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <div className="relative flex min-h-screen items-center justify-center bg-background">
        {/* Subtle radial gradient accent behind the card */}
        <div
          className="pointer-events-none absolute inset-0 overflow-hidden"
          aria-hidden="true"
        >
          <div className="absolute left-1/2 top-0 -translate-x-1/2 -translate-y-1/4 h-[600px] w-[600px] rounded-full bg-primary/[0.04] blur-3xl" />
        </div>

        {/* Auth card area */}
        <div className="relative z-10 w-full max-w-md px-4">{children}</div>

        {/* Bottom branding / copyright */}
        <p className="absolute bottom-6 left-0 right-0 text-center text-xs text-text-quaternary">
          &copy; {new Date().getFullYear()} FlowBoard. All rights reserved.
        </p>
      </div>
    </AuthProvider>
  );
}
