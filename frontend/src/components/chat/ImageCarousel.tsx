"use client";

import { useRef, useState, useEffect } from "react";
import { ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import type { DestinationImage } from "@/lib/api";

interface ImageCarouselProps {
  images: DestinationImage[];
  className?: string;
}

export function ImageCarousel({ images, className }: ImageCarouselProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);

  const checkScroll = () => {
    if (scrollContainerRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollContainerRef.current;
      setCanScrollLeft(scrollLeft > 0);
      setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 5);
    }
  };

  useEffect(() => {
    checkScroll();
    const container = scrollContainerRef.current;
    if (container) {
      container.addEventListener("scroll", checkScroll);
      window.addEventListener("resize", checkScroll);
    }
    return () => {
      if (container) {
        container.removeEventListener("scroll", checkScroll);
      }
      window.removeEventListener("resize", checkScroll);
    };
  }, [images]);

  const scroll = (direction: "left" | "right") => {
    if (scrollContainerRef.current) {
      const { clientWidth } = scrollContainerRef.current;
      const scrollAmount = direction === "left" ? -clientWidth / 1.5 : clientWidth / 1.5;
      scrollContainerRef.current.scrollBy({ left: scrollAmount, behavior: "smooth" });
    }
  };

  if (!images || images.length === 0) return null;

  return (
    <div className={cn("relative group mb-6 mt-4 w-full max-w-3xl mx-auto", className)}>
      <h3 className="text-sm uppercase tracking-wider font-medium text-muted-foreground mb-3 px-1 ml-1">
        Famous Landmarks
      </h3>
      
      {/* Left Arrow */}
      {canScrollLeft && (
        <Button
          variant="secondary"
          size="icon"
          className="absolute left-0 top-1/2 -translate-y-1/2 z-20 h-8 w-8 rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 -ml-3"
          onClick={() => scroll("left")}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
      )}

      {/* Right Arrow */}
      {canScrollRight && (
        <Button
          variant="secondary"
          size="icon"
          className="absolute right-0 top-1/2 -translate-y-1/2 z-20 h-8 w-8 rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 -mr-3"
          onClick={() => scroll("right")}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      )}

      {/* Scroll Container */}
      <div
        ref={scrollContainerRef}
        className="flex gap-3 overflow-x-auto pb-4 snap-x snap-mandatory scrollbar-hide px-1"
        style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        {images.map((img, idx) => (
          <div
            key={idx}
            className="flex-none w-[220px] sm:w-[260px] snap-center"
          >
            <div className="group/card relative aspect-[4/3] rounded-lg overflow-hidden bg-muted border border-border/50 shadow-sm transition-all hover:shadow-md hover:border-border">
              {/* Image */}
              <img
                src={img.thumbnail_url || img.image_url}
                alt={img.title}
                className="w-full h-full object-cover transition-transform duration-700 group-hover/card:scale-105"
                loading="lazy"
              />
              
              {/* No Overlay or Link as requested */}

              {/* No link */}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
