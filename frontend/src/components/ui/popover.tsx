import * as React from "react"
import { cn } from "@/lib/utils"

interface PopoverContextValue {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const PopoverContext = React.createContext<PopoverContextValue | undefined>(undefined);

const usePopover = () => {
  const context = React.useContext(PopoverContext);
  if (!context) {
    throw new Error("usePopover must be used within a Popover");
  }
  return context;
};

const Popover = ({ children, open, onOpenChange }: { children: React.ReactNode, open: boolean, onOpenChange: (open: boolean) => void }) => {
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      // Check if click is inside the popover wrapper
      if (ref.current && !ref.current.contains(event.target as Node)) {
        // If click is outside, close it
        if (open) {
          onOpenChange(false);
        }
      }
    };
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [open, onOpenChange]);

  return (
    <PopoverContext.Provider value={{ open, onOpenChange }}>
      <div ref={ref} className="relative inline-block">{children}</div>
    </PopoverContext.Provider>
  );
}

const PopoverTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & { asChild?: boolean }
>(({ className, children, asChild, onClick, ...props }, ref) => {
  const { open, onOpenChange } = usePopover();
  const Comp = asChild ? React.Fragment : "button"
  
  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    onOpenChange(!open);
    if (onClick) onClick(e);
  };

  // If using asChild, we assume the child is a button-like element that can accept onClick
  if (asChild) {
    // Handling asChild is tricky without Slot/composition libs, but for this specific use case
    // we know the child is a Button component.
    // Instead of full Slot implementation, let's just clone the child and inject onClick
    return React.cloneElement(children as React.ReactElement<any>, {
      onClick: handleClick,
      // Merge refs if needed, but for now ignoring
      ...props
    });
  }

  return (
    <button
      ref={ref}
      onClick={handleClick}
      className={cn(className)}
      {...props}
    >
      {children}
    </button>
  )
})
PopoverTrigger.displayName = "PopoverTrigger"

const PopoverContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { align?: "center" | "start" | "end", sideOffset?: number }
>(({ className, align = "center", sideOffset = 4, ...props }, ref) => {
  const { open } = usePopover();
  
  if (!open) return null;

  return (
    <div
      ref={ref}
      className={cn(
        "absolute z-50 w-72 rounded-md border bg-popover p-4 text-popover-foreground shadow-md outline-none animate-in fade-in-0 zoom-in-95",
        "bottom-full mb-2", // Always show above for now to fit the UI
        align === "start" && "left-0",
        align === "end" && "right-0",
        align === "center" && "left-1/2 -translate-x-1/2",
        className
      )}
      {...props}
    />
  )
})
PopoverContent.displayName = "PopoverContent"

export { Popover, PopoverTrigger, PopoverContent }
