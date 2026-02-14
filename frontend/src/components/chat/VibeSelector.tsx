
"use client";

import { 
  Zap, 
  Camera, 
  Sparkles, 
  Tent, 
  Activity, 
  Scroll, 
  MapPin, 
  Check
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export const VIBES = [
  {
    id: "Cyberpunk",
    label: "Cyberpunk",
    mobileLabel: "Cyberpunk",
    description: "Experience the neon-lit future with high-tech districts and underground culture.",
    icon: Zap,
    color: "text-pink-500",
    bg: "bg-pink-500/10",
    border: "border-pink-500/20",
  },
  {
    id: "Quiet Luxury",
    label: "Quiet Luxury",
    mobileLabel: "Luxury",
    description: "Indulge in private tours, elegant stays, and refined, crowd-free experiences.",
    icon: Sparkles,
    color: "text-slate-500",
    bg: "bg-slate-500/10",
    border: "border-slate-500/20",
  },
  {
    id: "Nature & Solitude",
    label: "Nature & Solitude",
    mobileLabel: "Nature",
    description: "Escape the city noise and recharge in peaceful, scenic natural landscapes.",
    icon: Tent,
    color: "text-green-500",
    bg: "bg-green-500/10",
    border: "border-green-500/20",
  },
  {
    id: "High Energy",
    label: "High Energy",
    mobileLabel: "Energy",
    description: "Dive into bustling nightlife, street food markets, and adrenaline-pumping fun.",
    icon: Activity,
    color: "text-orange-500",
    bg: "bg-orange-500/10",
    border: "border-orange-500/20",
  },
  {
    id: "History Buff",
    label: "History Buff",
    mobileLabel: "History",
    description: "Travel back in time through ancient ruins, museums, and cultural heritage sites.",
    icon: Scroll,
    color: "text-sepia-500", // Tailwind might not have sepia, using amber-700
    bg: "bg-amber-700/10",
    border: "border-amber-700/20",
  },
  {
    id: "Local Immersion",
    label: "Local Immersion",
    mobileLabel: "Local",
    description: "Live like a local with authentic neighborhood gems and community experiences.",
    icon: MapPin,
    color: "text-blue-500",
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
  },
];

interface VibeSelectorProps {
  selectedVibe: string | null;
  onSelect: (vibe: string | null) => void;
  disabled?: boolean;
}

export function VibeSelector({ selectedVibe, onSelect, disabled }: VibeSelectorProps) {
  return (
    <div className="w-full">
      <div className="flex items-center justify-center gap-2 mb-3">
        <Sparkles className="w-4 h-4 text-accent" />
        <span className="text-sm font-semibold text-foreground/80">
          Choose a Vibe
        </span>
      </div>
      
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {VIBES.map((vibe) => {
          const isSelected = selectedVibe === vibe.id;
          const Icon = vibe.icon;
          
          return (
            <Tooltip key={vibe.id}>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  disabled={disabled}
                  onClick={() => onSelect(isSelected ? null : vibe.id)}
                  className={cn(
                    "group relative flex items-center gap-2 px-3 py-2 rounded-xl border transition-all duration-200 w-full",
                    "hover:scale-[1.02] active:scale-[0.98]",
                    isSelected 
                      ? `${vibe.bg} ${vibe.border} ring-1 ring-inset ${vibe.color.replace('text-', 'ring-')}` 
                      : "bg-white border-border/40 hover:border-border/80 hover:bg-muted/30",
                    disabled && "opacity-50 cursor-not-allowed hover:scale-100"
                  )}
                >
                  <div className={cn(
                    "w-6 h-6 rounded-lg flex items-center justify-center transition-colors shrink-0",
                    isSelected ? "bg-white/80" : "bg-muted/50 group-hover:bg-muted"
                  )}>
                    <Icon className={cn("w-3.5 h-3.5", vibe.color)} />
                  </div>
                  
                  <div className="text-left min-w-0">
                    <div className={cn(
                      "text-xs font-semibold leading-tight truncate",
                      isSelected ? "text-foreground" : "text-muted-foreground group-hover:text-foreground"
                    )}>
                      <span className="sm:hidden">{vibe.mobileLabel}</span>
                      <span className="hidden sm:inline">{vibe.label}</span>
                    </div>
                  </div>

                  {isSelected && (
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-accent rounded-full border-2 border-white flex items-center justify-center">
                      <Check className="w-2 h-2 text-white" strokeWidth={4} />
                    </div>
                  )}
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[200px] text-center">
                <p>{vibe.description}</p>
              </TooltipContent>
            </Tooltip>
          );
        })}
      </div>
    </div>
  );
}
