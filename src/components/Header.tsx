"use client";

import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useScenario } from "@/components/ScenarioContext";
import type { Scenario } from "@/data/scenarios";

export function Header() {
  const { scenario, setScenario, replay } = useScenario();

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
        <div className="flex items-center gap-2">
          <span className="text-xl font-bold text-slate-900 tracking-tight">
            Ly<span className="text-fornest-orange">ra</span>
          </span>
          <span className="hidden sm:block text-xs text-slate-400 font-medium border-l border-slate-200 pl-2 ml-1">
            Lead Guardian
          </span>
          <span className="hidden md:flex items-center gap-1 ml-3 px-2 py-0.5 bg-fornest-orange-light text-fornest-orange text-xs font-semibold rounded-full">
            DEMO
          </span>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-500 font-medium hidden sm:block">Scenario</label>
          <Select value={scenario} onValueChange={(v) => setScenario(v as Scenario)}>
            <SelectTrigger className="w-[200px] sm:w-[220px] h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="clean">A — Clean ADF (default)</SelectItem>
              <SelectItem value="vague">B — Vague Edge Case</SelectItem>
              <SelectItem value="hostile">C — Hostile Escalation</SelectItem>
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            size="sm"
            onClick={replay}
            className="h-8 gap-1.5 text-xs"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span className="hidden sm:block">Replay</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
