"use client";

import {
  ExternalLink,
  Hotel,
  Plane,
  TrainFront,
} from "lucide-react";
import { cn } from "@/lib/utils";

import type { PlanMetaPayload } from "@/lib/api";

interface PlanInsightsPanelProps {
  meta: PlanMetaPayload;
}

const BAD_URL_TOKENS = ["example.com", "localhost", "...", "<", ">", "{", "}"];

function clamp(value: number): number {
  return Math.max(0, Math.min(100, value));
}

function isSafeHttpUrl(url: string): boolean {
  if (!url) return false;
  const lowered = url.toLowerCase();
  if (BAD_URL_TOKENS.some((token) => lowered.includes(token))) {
    return false;
  }
  return lowered.startsWith("http://") || lowered.startsWith("https://");
}

function fallbackFlightLink(route: string, airline?: string | null): string {
  const query = [route, airline ?? "", "flight"].filter(Boolean).join(" ");
  return `https://www.google.com/travel/flights?q=${encodeURIComponent(query)}`;
}

function fallbackStayLink(name: string, location?: string | null): string {
  const query = [name, location ?? "", "hotel booking"].filter(Boolean).join(" ");
  return `https://www.booking.com/searchresults.html?ss=${encodeURIComponent(query)}`;
}

function fallbackTrainLink(route: string, trainName?: string | null): string {
  const query = [route, trainName ?? "", "IRCTC train booking"]
    .filter(Boolean)
    .join(" ");
  return `https://www.google.com/search?q=${encodeURIComponent(query)}`;
}

function isDirectFlight(flight: PlanMetaPayload["flights"][number]): boolean {
  const haystack = `${flight.route} ${flight.notes ?? ""} ${flight.duration ?? ""}`.toLowerCase();
  return (
    haystack.includes("direct") ||
    haystack.includes("non-stop") ||
    haystack.includes("nonstop")
  );
}

function toneText(level: string): string {
  if (level === "HIGH") return "text-emerald-700";
  if (level === "MEDIUM") return "text-amber-700";
  return "text-rose-700";
}

function scoreStroke(value: number): string {
  if (value >= 80) return "#059669";
  if (value >= 60) return "#d97706";
  return "#dc2626";
}

export function PlanInsightsPanel({ meta }: PlanInsightsPanelProps) {
  const flights = meta.flights ?? [];
  const trains = meta.trains ?? [];
  const lodgings = meta.lodgings ?? [];
  const hasFlights = flights.length > 0;
  const hasTrains = trains.length > 0;
  const hasLodgings = lodgings.length > 0;
  const confidence = meta.confidence;
  const score = clamp(confidence?.score ?? 0);
  const gaugeRadius = 18;
  const gaugeCircumference = 2 * Math.PI * gaugeRadius;
  const gaugeOffset = gaugeCircumference * (1 - score / 100);
  const hasDirectFlight = flights.some(isDirectFlight);
  const isIndianTravel = hasTrains;
  const shouldPreferTrains = hasTrains && (isIndianTravel || !hasDirectFlight);
  const showFlightsSection = hasFlights && !shouldPreferTrains;
  const showTrainsSection = shouldPreferTrains;

  if (!confidence && !hasFlights && !hasTrains && !hasLodgings) {
    return null;
  }

  return (
    <section className="mt-4 w-full min-w-0 overflow-hidden rounded-3xl border border-accent/50 bg-white shadow-[0_8px_30px_rgba(0,0,0,0.06)]">
      <div className="border-b border-accent/50 bg-accent/5 px-5 py-3 sm:px-6 sm:py-1">
        <div className="flex items-center justify-between gap-3">
          <div className="space-y-1 min-w-0">
            <h4 className="text-xl font-semibold tracking-tight text-foreground">
              Bookable Options
            </h4>
          </div>
          {confidence ? (
            <div className="group relative ml-auto shrink-0">
              <div className="w-[85px] px-1.5 py-1 text-center">

                <div className="mt-0.5 flex items-center justify-center">
                  <div className="relative h-9 w-9">
                    <svg viewBox="0 0 48 48" className="h-full w-full -rotate-90">
                      <circle
                        cx="24"
                        cy="24"
                        r={gaugeRadius}
                        stroke="#D6D3D1"
                        strokeWidth="4"
                        fill="none"
                      />
                      <circle
                        cx="24"
                        cy="24"
                        r={gaugeRadius}
                        stroke={scoreStroke(score)}
                        strokeWidth="4"
                        strokeLinecap="round"
                        fill="none"
                        strokeDasharray={gaugeCircumference}
                        strokeDashoffset={gaugeOffset}
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className={cn("text-[11px] font-semibold", toneText(confidence.level))}>
                        {score}
                      </span>
                    </div>
                  </div>
                </div>
                <p className="text-[9px] font-bold leading-tight tracking-[0.04em] text-black">
                  <span className="block">CONFIDENCE</span>
                  <span className="block">SCORE</span>
                </p>
              </div>
              <div className="pointer-events-none absolute right-0 top-full z-20 mt-2 rounded-lg border border-border/60 bg-white px-2.5 py-1.5 text-left opacity-0 shadow-lg transition-all duration-200 group-hover:translate-y-0 group-hover:opacity-100 group-focus-within:translate-y-0 group-focus-within:opacity-100">
                <p className="whitespace-nowrap text-[11px] text-muted-foreground">
                  Confidence combines source quality, cost consistency, and specificity.
                </p>
              </div>
            </div>
          ) : null}
        </div>
      </div>

      <div className="space-y-5 p-4 sm:p-6">
        {showFlightsSection && (
          <section className="space-y-3">
            <div className="flex items-center justify-between gap-2">
              <p className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                <Plane className="h-4 w-4 text-accent" />
                Flights
              </p>
              <span className="text-xs text-muted-foreground">
                {flights.length} options
              </span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {flights.slice(0, 4).map((flight, idx) => {
                const link = isSafeHttpUrl(flight.booking_url)
                  ? flight.booking_url
                  : fallbackFlightLink(flight.route, flight.airline);
                return (
                  <article
                    key={`${flight.route}-${idx}`}
                    className="group min-w-0 rounded-2xl border border-border/60 bg-white p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:border-foreground/20 hover:shadow-md"
                  >
                    <p className="break-words text-sm font-semibold leading-snug text-foreground/80">
                      {flight.route}
                    </p>
                    <p className="mt-1 text-xl font-semibold text-foreground">
                      {flight.price}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground/90">
                      {flight.airline || "Multiple airlines"}{" "}
                      {flight.duration ? `· ${flight.duration}` : ""}
                    </p>
                    <a
                      href={link}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-3 inline-flex w-full items-center justify-center gap-1 rounded-full border border-foreground/15 bg-foreground/[0.03] px-3 py-2 text-xs font-semibold text-foreground transition-colors hover:border-accent/35 hover:bg-accent/10 hover:text-accent sm:w-auto"
                    >
                      Search live fares
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  </article>
                );
              })}
            </div>
          </section>
        )}

        {showTrainsSection && (
          <section className="space-y-3">
            <div className="flex items-center justify-between gap-2">
              <p className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                <TrainFront className="h-4 w-4 text-accent" />
                Trains
              </p>
              <span className="text-xs text-muted-foreground">
                {trains.length} options
              </span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {trains.slice(0, 4).map((train, idx) => {
                const link = isSafeHttpUrl(train.booking_url)
                  ? train.booking_url
                  : fallbackTrainLink(train.route, train.train_name);
                return (
                  <article
                    key={`${train.route}-${idx}`}
                    className="group min-w-0 rounded-2xl border border-border/60 bg-white p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:border-foreground/20 hover:shadow-md"
                  >
                    <p className="break-words text-sm font-semibold leading-snug text-foreground/80">
                      {train.route}
                    </p>
                    <p className="mt-1 text-xl font-semibold text-foreground">
                      {train.price}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground/90">
                      {train.train_name || "Indian Railways"}
                      {train.train_class ? ` · ${train.train_class}` : ""}
                      {train.duration ? ` · ${train.duration}` : ""}
                    </p>
                    <a
                      href={link}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-3 inline-flex w-full items-center justify-center gap-1 rounded-full border border-foreground/15 bg-foreground/[0.03] px-3 py-2 text-xs font-semibold text-foreground transition-colors hover:border-accent/35 hover:bg-accent/10 hover:text-accent sm:w-auto"
                    >
                      Search trains
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  </article>
                );
              })}
            </div>
          </section>
        )}

        {hasLodgings && (
          <section className="space-y-3">
            <div className="flex items-center justify-between gap-2">
              <p className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                <Hotel className="h-4 w-4 text-accent" />
                Stays
              </p>
              <span className="text-xs text-muted-foreground">
                {lodgings.length} options
              </span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {lodgings.slice(0, 4).map((stay, idx) => {
                const link = isSafeHttpUrl(stay.booking_url)
                  ? stay.booking_url
                  : fallbackStayLink(stay.name, stay.location);
                return (
                  <article
                    key={`${stay.name}-${idx}`}
                    className="group min-w-0 rounded-2xl border border-border/60 bg-white p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:border-foreground/20 hover:shadow-md"
                  >
                    <p className="break-words text-sm font-semibold leading-snug text-foreground/80">
                      {stay.name}
                    </p>
                    <p className="mt-1 text-xl font-semibold text-foreground">
                      {stay.price_per_night}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground/90">
                      {stay.location || "Best-rated area"}{" "}
                      {stay.rating ? `· ${stay.rating}` : ""}
                    </p>
                    <a
                      href={link}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-3 inline-flex w-full items-center justify-center gap-1 rounded-full border border-foreground/15 bg-foreground/[0.03] px-3 py-2 text-xs font-semibold text-foreground transition-colors hover:border-accent/35 hover:bg-accent/10 hover:text-accent sm:w-auto"
                    >
                      Search live rooms
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  </article>
                );
              })}
            </div>
          </section>
        )}

      </div>
    </section>
  );
}
