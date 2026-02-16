"use client";

import {
  ExternalLink,
  Globe2,
  Hotel,
  Plane,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import type { PlanMetaPayload } from "@/lib/api";

interface PlanInsightsPanelProps {
  meta: PlanMetaPayload;
}

const BAD_URL_TOKENS = ["example.com", "localhost", "...", "<", ">", "{", "}"];

function badgeClasses(level: string): string {
  if (level === "HIGH") return "bg-emerald-500/10 text-emerald-700 border-emerald-500/30";
  if (level === "MEDIUM") return "bg-amber-500/10 text-amber-700 border-amber-500/30";
  return "bg-rose-500/10 text-rose-700 border-rose-500/30";
}

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

function metricColor(value: number): string {
  if (value >= 80) return "bg-emerald-500";
  if (value >= 60) return "bg-amber-500";
  return "bg-rose-500";
}

export function PlanInsightsPanel({ meta }: PlanInsightsPanelProps) {
  const hasFlights = meta.flights.length > 0;
  const hasLodgings = meta.lodgings.length > 0;
  const hasSources = meta.sources.length > 0;
  const confidence = meta.confidence;

  if (!confidence && !hasFlights && !hasLodgings && !hasSources) {
    return null;
  }

  return (
    <section className="mt-4 w-full min-w-0 overflow-hidden rounded-2xl border border-border/50 bg-gradient-to-b from-white to-[#FCFBF7] shadow-sm">
      <div className="border-b border-border/50 bg-[radial-gradient(circle_at_top_right,_rgba(244,180,62,0.18),_transparent_45%)] p-4 sm:p-5">
        <div className="flex flex-col items-start gap-3 sm:flex-row sm:justify-between">
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Plan Intelligence
            </p>
            <h4 className="text-base font-semibold text-foreground">
              Trusted Sources and Live Booking
            </h4>
          </div>
          <div className="inline-flex self-start items-center gap-1 rounded-full border border-accent/25 bg-accent/10 px-2.5 py-1 text-xs font-semibold text-accent sm:self-auto">
            <Sparkles className="h-3.5 w-3.5" />
            Live
          </div>
        </div>
      </div>

      <div className="space-y-4 p-4 sm:p-5">
        {confidence && (
          <article className="min-w-0 rounded-xl border border-border/50 bg-white p-4">
            <div className="flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-accent" />
                <p className="text-sm font-semibold text-foreground">
                  Confidence Score
                </p>
              </div>
              <span
                className={`whitespace-nowrap rounded-full border px-2.5 py-1 text-xs font-semibold ${badgeClasses(confidence.level)}`}
              >
                {confidence.level} {confidence.score}/100
              </span>
            </div>

            <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-muted/70">
              <div
                className={`h-full rounded-full ${metricColor(confidence.score)}`}
                style={{ width: `${clamp(confidence.score)}%` }}
              />
            </div>
            <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
              {confidence.summary}
            </p>

            <div className="mt-3 grid gap-2 sm:grid-cols-3">
              <div className="rounded-lg bg-muted/35 px-3 py-2">
                <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  Sources
                </p>
                <p className="text-sm font-semibold text-foreground">
                  {confidence.breakdown.source_coverage}
                </p>
              </div>
              <div className="rounded-lg bg-muted/35 px-3 py-2">
                <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  Costs
                </p>
                <p className="text-sm font-semibold text-foreground">
                  {confidence.breakdown.cost_completeness}
                </p>
              </div>
              <div className="rounded-lg bg-muted/35 px-3 py-2">
                <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  Specificity
                </p>
                <p className="text-sm font-semibold text-foreground">
                  {confidence.breakdown.itinerary_specificity}
                </p>
              </div>
            </div>
          </article>
        )}

        {hasFlights && (
          <section className="space-y-2">
            <div className="flex items-center gap-2">
              <Plane className="h-4 w-4 text-accent" />
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                Flights
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {meta.flights.slice(0, 4).map((flight, idx) => {
                const link = isSafeHttpUrl(flight.booking_url)
                  ? flight.booking_url
                  : fallbackFlightLink(flight.route, flight.airline);
                return (
                  <article
                    key={`${flight.route}-${idx}`}
                    className="group min-w-0 rounded-xl border border-border/60 bg-white p-4 transition-all hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-md"
                  >
                    <p className="break-words text-[15px] font-semibold leading-snug text-foreground">
                      {flight.route}
                    </p>
                    <p className="mt-1 text-sm font-medium text-foreground/80">
                      {flight.price}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {flight.airline || "Multiple airlines"}{" "}
                      {flight.duration ? `· ${flight.duration}` : ""}
                    </p>
                    <a
                      href={link}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-3 inline-flex w-full items-center justify-center gap-1 rounded-full border border-accent/25 bg-accent/10 px-3 py-1.5 text-xs font-semibold text-accent transition-colors hover:bg-accent hover:text-white sm:w-auto"
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

        {hasLodgings && (
          <section className="space-y-2">
            <div className="flex items-center gap-2">
              <Hotel className="h-4 w-4 text-accent" />
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                Stays
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {meta.lodgings.slice(0, 4).map((stay, idx) => {
                const link = isSafeHttpUrl(stay.booking_url)
                  ? stay.booking_url
                  : fallbackStayLink(stay.name, stay.location);
                return (
                  <article
                    key={`${stay.name}-${idx}`}
                    className="group min-w-0 rounded-xl border border-border/60 bg-white p-4 transition-all hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-md"
                  >
                    <p className="break-words text-[15px] font-semibold leading-snug text-foreground">
                      {stay.name}
                    </p>
                    <p className="mt-1 text-sm font-medium text-foreground/80">
                      {stay.price_per_night}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {stay.location || "Best-rated area"}{" "}
                      {stay.rating ? `· ${stay.rating}` : ""}
                    </p>
                    <a
                      href={link}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-3 inline-flex w-full items-center justify-center gap-1 rounded-full border border-accent/25 bg-accent/10 px-3 py-1.5 text-xs font-semibold text-accent transition-colors hover:bg-accent hover:text-white sm:w-auto"
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

        {hasSources && (
          <section className="min-w-0 rounded-xl border border-border/60 bg-white p-4">
            <div className="mb-2 flex items-center gap-2">
              <Globe2 className="h-4 w-4 text-accent" />
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                Sources
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {meta.sources.slice(0, 8).map((source, idx) => {
                const sourceLink = isSafeHttpUrl(source.url)
                  ? source.url
                  : `https://www.google.com/search?q=${encodeURIComponent(source.domain)}`;
                return (
                  <a
                    key={`${source.url}-${idx}`}
                    href={sourceLink}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex min-w-0 max-w-full items-center gap-1 overflow-hidden rounded-full border border-border/70 bg-muted/20 px-3 py-1.5 text-xs font-medium text-foreground transition-all hover:border-accent/40 hover:text-accent"
                  >
                    <span className="truncate">{source.domain}</span>
                    <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                  </a>
                );
              })}
            </div>
          </section>
        )}
      </div>
    </section>
  );
}
