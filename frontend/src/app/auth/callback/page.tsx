import { Suspense } from "react";
import { AuthCallbackClient } from "./AuthCallbackClient";

export const dynamic = "force-dynamic";

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <p className="text-slate-500">Completing sign in...</p>
        </div>
      }
    >
      <AuthCallbackClient />
    </Suspense>
  );
}
