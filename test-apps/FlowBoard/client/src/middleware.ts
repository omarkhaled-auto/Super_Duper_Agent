import { NextResponse, type NextRequest } from "next/server";

// =============================================================================
// Next.js Middleware -- Auth Route Guard
//
// Runs on the Edge for every matched route. Checks for the `access_token`
// cookie that the client sets alongside the localStorage token.
//
//   - No token + protected route  -> redirect to /login
//   - Has token + auth route      -> redirect to /dashboard
//
// This is a lightweight gate; the actual token validation happens server-side
// when the API client sends the Authorization header.
// =============================================================================

/** Routes that do NOT require authentication. */
const PUBLIC_PATHS = new Set(["/login", "/signup"]);

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasToken = request.cookies.has("access_token");

  // ---- Authenticated user visiting login/signup -> redirect to dashboard ----
  if (hasToken && PUBLIC_PATHS.has(pathname)) {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard";
    return NextResponse.redirect(url);
  }

  // ---- Unauthenticated user visiting protected route -> redirect to login ----
  if (!hasToken && !PUBLIC_PATHS.has(pathname)) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    // Preserve the originally-requested URL so we can redirect back after login.
    url.searchParams.set("redirect", pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

// ---------------------------------------------------------------------------
// Route matcher -- only run middleware on app routes, skip static assets,
// API routes, Next.js internals, and public files.
// ---------------------------------------------------------------------------

export const config = {
  matcher: [
    /*
     * Match all request paths EXCEPT:
     *   - _next/static    (static files)
     *   - _next/image     (image optimization)
     *   - favicon.ico     (browser icon)
     *   - public assets   (images, fonts, etc.)
     *   - api routes      (handled server-side)
     */
    "/((?!_next/static|_next/image|favicon\\.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|woff|woff2|ttf|eot)$).*)",
  ],
};
