"use client";

import { useState, useEffect } from "react";
import { ArrowRight, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { VibeSelector, VIBES } from "@/components/chat/VibeSelector";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

export function TripForm() {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const [selectedVibe, setSelectedVibe] = useState<string | null>(null);
  const [isVibeSelectorOpen, setIsVibeSelectorOpen] = useState(false);

  // Typewriter effect
  const [placeholder, setPlaceholder] = useState("");

  useEffect(() => {
    const texts = [
      "Plan a trip to Chicago from NYC for a week with a $1,500 budget...",
      "A 10-day hiking adventure in Switzerland starting from Zurich...",
      "Romantic getaway to Kyoto in autumn with traditional stays...",
    ];
    let loopNum = 0;
    let isDeleting = false;
    let txt = "";

    let timer: NodeJS.Timeout;

    const tick = () => {
      const i = loopNum % texts.length;
      const fullText = texts[i];
      let nextDelta = 100;

      if (isDeleting) {
        txt = fullText.substring(0, txt.length - 1);
        nextDelta = 30;
      } else {
        txt = fullText.substring(0, txt.length + 1);
        nextDelta = 50 + Math.random() * 50;
      }

      setPlaceholder(txt);

      if (!isDeleting && txt === fullText) {
        isDeleting = true;
        nextDelta = 2000;
      } else if (isDeleting && txt === "") {
        isDeleting = false;
        loopNum++;
        nextDelta = 500;
      }

      timer = setTimeout(tick, nextDelta);
    };

    timer = setTimeout(tick, 100);
    return () => clearTimeout(timer);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    const encodedPrompt = encodeURIComponent(prompt.trim());
    let url = `/trip?prompt=${encodedPrompt}`;
    if (selectedVibe) {
      url += `&vibe=${encodeURIComponent(selectedVibe)}`;
    }
    router.push(url);
  };

  const handleAutoStart = () => {
    if (!prompt.trim()) return;
    const encodedPrompt = encodeURIComponent(prompt.trim());
    let url = `/trip?prompt=${encodedPrompt}`;
    if (selectedVibe) {
      url += `&vibe=${encodeURIComponent(selectedVibe)}`;
    }
    router.push(url);
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="rounded-2xl border-2 border-border bg-card shadow-lg p-4">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleAutoStart();
            }
          }}
          placeholder={placeholder}
          aria-label="Describe your trip"
          className="w-full h-24 resize-none text-base bg-transparent text-foreground placeholder:text-muted-foreground/60 focus:outline-none font-body"
        />
        <div className="flex justify-between items-center pt-2">
          <Popover open={isVibeSelectorOpen} onOpenChange={setIsVibeSelectorOpen}>
            <PopoverTrigger asChild>
              <Button
                type="button"
                variant="outline"
                className={`rounded-full h-10 px-4 gap-2 border-border/50 bg-background/50 hover:bg-background ${selectedVibe ? 'text-accent border-accent/30 bg-accent/5' : 'text-muted-foreground'}`}
              >
                <Sparkles className={`w-4 h-4 ${selectedVibe ? 'fill-accent/20' : ''}`} />
                <span className="text-sm font-medium">
                  {selectedVibe ? (
                    <>
                      <span className="sm:hidden">
                        {VIBES.find(v => v.id === selectedVibe)?.mobileLabel || selectedVibe}
                      </span>
                      <span className="hidden sm:inline">
                        {VIBES.find(v => v.id === selectedVibe)?.label || selectedVibe}
                      </span>
                    </>
                  ) : "Vibe"}
                </span>
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[90vw] sm:w-[500px] p-4 rounded-2xl" align="start">
              <VibeSelector
                selectedVibe={selectedVibe}
                onSelect={(v) => {
                  setSelectedVibe(v);
                  setIsVibeSelectorOpen(false);
                }}
              />
            </PopoverContent>
          </Popover>

          <button
            type="submit"
            className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-6 py-2.5 rounded-full text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer"
          >
            Start planning
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </form>
  );
}
