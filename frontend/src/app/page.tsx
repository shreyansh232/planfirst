import Image from "next/image";
import { Compass, Shield, Zap, Globe } from "lucide-react";
import { TripForm } from "@/components/home/TripForm";
import { HomeLayout } from "@/components/home/HomeLayout";

export default function Home() {
  return (
    <HomeLayout>
      <main className="flex-1 max-w-6xl mx-auto px-6 w-full">
        {/* Hero */}
        <section className="pt-16 pb-24">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left: Copy + Input */}
            <div className="flex flex-col gap-8">
              <div className="flex flex-col gap-5">
                <span className="text-sm font-medium uppercase tracking-[0.3em] text-accent">
                  AI-Powered Travel
                </span>
                <h1 className="text-4xl sm:text-5xl lg:text-6xl leading-[1.1] text-foreground">
                  Your next journey,{" "}
                  <span className="italic">thoughtfully planned</span>
                </h1>
                <p className="text-lg text-muted-foreground max-w-lg leading-relaxed">
                  Describe your dream trip in a sentence. We&apos;ll craft a
                  complete itinerary — flights, stays, experiences — tailored
                  to your budget and style.
                </p>
              </div>

              <TripForm />

              <div className="flex items-center gap-8 text-sm text-muted-foreground">
                <span className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent" />
                  Personalized
                </span>
                <span className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent" />
                  Budget-aware
                </span>
                <span className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent" />
                  Multilingual
                </span>
              </div>
            </div>

            {/* Right: Hero Image */}
            <div className="relative hidden lg:block">
              <div className="rounded-3xl overflow-hidden shadow-2xl relative w-full h-[520px]">
                <Image
                  src="/hero/hero-travel.jpg"
                  alt="Stunning coastal village at golden hour"
                  fill
                  className="object-cover"
                  priority
                />
              </div>
              <div className="absolute -bottom-6 -left-6 bg-card rounded-2xl shadow-lg border border-border p-4 max-w-[220px] z-10">
                <p className="text-xs text-muted-foreground mb-1">Latest trip planned</p>
                <p className="text-sm font-medium text-foreground">7 days in Cinque Terre</p>
                <p className="text-xs text-accent mt-1">$2,400 · 2 travelers</p>
              </div>
            </div>
          </div>
        </section>

        {/* How it works */}
        <section id="how" className="py-24 border-t border-border">
          <div className="text-center mb-16">
            <span className="text-sm font-medium uppercase tracking-[0.3em] text-accent mb-4 block">
              How it works
            </span>
            <h2 className="text-3xl sm:text-4xl mb-4 text-foreground">
              Travel planning, reimagined
            </h2>
            <p className="text-muted-foreground text-lg max-w-xl mx-auto">
              From idea to itinerary — simple, fast, and personalized.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="group bg-card border border-border rounded-2xl p-5 hover:shadow-lg hover:border-accent/20 transition-all duration-500">
              <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mb-6 group-hover:bg-accent/20 transition-colors">
                <Compass className="w-6 h-6 text-accent" />
              </div>
              <h3 className="text-lg font-medium mb-3 text-foreground group-hover:text-accent transition-colors">Describe your trip</h3>
              <p className="text-muted-foreground text-sm leading-tighter">Share where, when, and your budget.</p>
            </div>
            <div className="group bg-card border border-border rounded-2xl p-5 hover:shadow-lg hover:border-accent/20 transition-all duration-500">
              <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mb-6 group-hover:bg-accent/20 transition-colors">
                <Zap className="w-6 h-6 text-accent" />
              </div>
              <h3 className="text-lg font-medium mb-3 text-foreground group-hover:text-accent transition-colors">We build your plan</h3>
              <p className="text-muted-foreground text-sm leading-tighter">AI researches and creates your trip plan.</p>
            </div>
            <div className="group bg-card border border-border rounded-2xl p-5 hover:shadow-lg hover:border-accent/20 transition-all duration-500">
              <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mb-6 group-hover:bg-accent/20 transition-colors">
                <Shield className="w-6 h-6 text-accent" />
              </div>
              <h3 className="text-lg font-medium mb-3 text-foreground group-hover:text-accent transition-colors">Refine and go</h3>
              <p className="text-muted-foreground text-sm leading-tighter">Swap, add, or change anything instantly.</p>
            </div>
            <div className="group bg-card border border-border rounded-2xl p-5 hover:shadow-lg hover:border-accent/20 transition-all duration-500">
              <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mb-6 group-hover:bg-accent/20 transition-colors">
                <Globe className="w-6 h-6 text-accent" />
              </div>
              <h3 className="text-lg font-medium mb-3 text-foreground group-hover:text-accent transition-colors">Chat in any language</h3>
              <p className="text-muted-foreground text-sm leading-tighter">Talk naturally — we understand any language.</p>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="py-12 border-t border-border flex items-center justify-between text-sm text-muted-foreground">
          <span className="font-medium text-black">Planfirst</span>
          <span>© {new Date().getFullYear()} Planfirst. All rights reserved.</span>
        </footer>
      </main>
    </HomeLayout>
  );
}
