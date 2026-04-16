"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { SceneWrapper } from "./SceneWrapper";
import { useScenario } from "@/components/ScenarioContext";

export function Scene03Drafting() {
  const { replayKey, data } = useScenario();
  const [phase, setPhase] = useState<"loading" | "done">("loading");

  useEffect(() => {
    setPhase("loading");
    const t = setTimeout(() => setPhase("done"), 1600);
    return () => clearTimeout(t);
  }, [replayKey]);

  return (
    <SceneWrapper id="scene-3" sceneNumber={3} title="Lyra is Drafting" fr="FR-3 · Claude Draft Generation">
      <div className="flex justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="p-8">
            <AnimatePresence mode="wait">
              {phase === "loading" ? (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center gap-4"
                >
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                  >
                    <Sparkles className="h-10 w-10 text-fornest-orange" />
                  </motion.div>
                  <div className="text-center">
                    <p className="font-semibold text-slate-900 mb-1">Lyra · claude-haiku-4-5</p>
                    <p className="text-sm text-slate-500 animate-pulse">drafting reply…</p>
                  </div>
                  <div className="w-full space-y-2">
                    <Skeleton className="h-3 w-full" />
                    <Skeleton className="h-3 w-5/6" />
                    <Skeleton className="h-3 w-4/5" />
                    <Skeleton className="h-3 w-full" />
                    <Skeleton className="h-3 w-3/4" />
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="done"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex flex-col items-center gap-3"
                >
                  <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                    <Sparkles className="h-6 w-6 text-green-600" />
                  </div>
                  <p className="font-semibold text-slate-900">
                    {data.escalate ? "Escalation triggered" : "Draft ready"}
                  </p>
                  <p className="text-sm text-slate-500 text-center">
                    {data.escalate
                      ? "Legal threat detected — routing to human rep"
                      : "Scroll to Scene 4 to review the draft →"}
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </CardContent>
        </Card>
      </div>
    </SceneWrapper>
  );
}
