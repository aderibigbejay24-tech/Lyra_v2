"use client";

import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const SCENES = [
  { id: "scene-1", label: "Inbox" },
  { id: "scene-2", label: "Parsed" },
  { id: "scene-3", label: "Drafting" },
  { id: "scene-4", label: "Draft" },
  { id: "scene-5", label: "Fan-out" },
  { id: "scene-6", label: "Approver" },
  { id: "scene-7", label: "Email Sent" },
  { id: "scene-8", label: "Customer" },
  { id: "scene-9", label: "Booking" },
  { id: "scene-10", label: "Rep Ping" },
  { id: "scene-11", label: "Audit Log" },
  { id: "scene-12", label: "Metrics" },
];

export function Stepper() {
  const [activeScene, setActiveScene] = useState(0);

  useEffect(() => {
    const observers: IntersectionObserver[] = [];
    SCENES.forEach((scene, index) => {
      const el = document.getElementById(scene.id);
      if (!el) return;
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) setActiveScene(index);
        },
        { threshold: 0.3, rootMargin: "-80px 0px -60% 0px" }
      );
      observer.observe(el);
      observers.push(observer);
    });
    return () => observers.forEach((o) => o.disconnect());
  }, []);

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const prev = () => {
    const target = Math.max(0, activeScene - 1);
    scrollTo(SCENES[target].id);
  };

  const next = () => {
    const target = Math.min(SCENES.length - 1, activeScene + 1);
    scrollTo(SCENES[target].id);
  };

  return (
    <nav
      className="sticky top-14 z-40 bg-slate-50 border-b border-slate-200"
      aria-label="Scene navigation"
    >
      {/* Desktop */}
      <div className="hidden md:flex max-w-7xl mx-auto px-4 sm:px-6 py-2 gap-0.5 overflow-x-auto">
        {SCENES.map((scene, i) => (
          <button
            key={scene.id}
            onClick={() => scrollTo(scene.id)}
            className={cn(
              "flex flex-col items-center px-2 py-1.5 rounded-lg text-xs transition-all min-w-fit",
              activeScene === i
                ? "bg-fornest-orange text-white font-semibold"
                : "text-slate-500 hover:text-slate-800 hover:bg-slate-100"
            )}
          >
            <span className="text-[10px] mb-0.5 opacity-60">{i + 1}</span>
            <span>{scene.label}</span>
          </button>
        ))}
      </div>

      {/* Mobile */}
      <div className="flex md:hidden items-center justify-between px-4 py-2">
        <Button variant="ghost" size="icon" onClick={prev} disabled={activeScene === 0} className="h-8 w-8">
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <span className="text-xs font-medium text-slate-600">
          Scene {activeScene + 1} of {SCENES.length} ·{" "}
          <span className="text-slate-900">{SCENES[activeScene].label}</span>
        </span>
        <Button
          variant="ghost"
          size="icon"
          onClick={next}
          disabled={activeScene === SCENES.length - 1}
          className="h-8 w-8"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </nav>
  );
}
