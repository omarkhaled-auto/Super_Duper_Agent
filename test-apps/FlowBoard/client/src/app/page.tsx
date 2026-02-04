import { redirect } from "next/navigation";

/**
 * Root page -- immediately redirects to the dashboard.
 *
 * Auth middleware will intercept unauthenticated users and send them to /login
 * before this redirect fires, so there is no flash of protected content.
 */
export default function RootPage() {
  redirect("/dashboard");
}
