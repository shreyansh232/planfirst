import { Suspense } from "react";
import { TripPageClient } from "./TripPageClient";

export const dynamic = "force-dynamic";

export default function TripPage() {
  return (
    <Suspense fallback={null}>
      <TripPageClient />
    </Suspense>
  );
}
