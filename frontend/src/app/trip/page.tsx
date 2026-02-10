import { Suspense } from "react";
import { TripPageClient } from "./TripPageClient";

export const dynamic = "force-dynamic";

export default function TripPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center bg-white">
          <p className="text-slate-500">Loading...</p>
        </div>
      }
    >
      <TripPageClient />
    </Suspense>
  );
}
