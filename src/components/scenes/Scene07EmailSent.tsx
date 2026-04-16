"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, CheckCircle2, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SceneWrapper } from "./SceneWrapper";
import { useScenario } from "@/components/ScenarioContext";

export function Scene07EmailSent() {
  const { data, replayKey } = useScenario();
  const [phase, setPhase] = useState<"composer" | "sending" | "sent">("composer");

  useEffect(() => {
    setPhase("composer");
  }, [replayKey]);

  const handleSend = () => {
    setPhase("sending");
    setTimeout(() => setPhase("sent"), 800);
  };

  if (data.escalate) {
    return (
      <SceneWrapper id="scene-7" sceneNumber={7} title="Email Sent" fr="FR-6 · Threaded Gmail Send">
        <div className="flex justify-center">
          <Card className="max-w-lg w-full border-yellow-200 bg-yellow-50">
            <CardContent className="p-6 flex flex-col items-center gap-3 text-center">
              <AlertTriangle className="h-8 w-8 text-yellow-500" />
              <p className="font-semibold text-yellow-800">Human Taking Over</p>
              <p className="text-sm text-yellow-700">No automated email sent. Escalation path active.</p>
            </CardContent>
          </Card>
        </div>
      </SceneWrapper>
    );
  }

  const draft = data.draft!;
  const customerEmail = data.customer.email;

  return (
    <SceneWrapper id="scene-7" sceneNumber={7} title="Email Sent" fr="FR-6 · Threaded Gmail Send">
      <div className="max-w-2xl mx-auto space-y-4">
        {/* Composer */}
        <AnimatePresence mode="wait">
          {phase !== "sent" && (
            <motion.div
              key="composer"
              initial={{ y: 40, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 40, opacity: 0 }}
              transition={{ duration: 0.35 }}
            >
              <Card className="border-slate-300 shadow-lg">
                <div className="bg-slate-100 px-4 py-2 rounded-t-2xl flex items-center justify-between">
                  <span className="text-sm font-semibold text-slate-700">New Message</span>
                </div>
                <CardContent className="p-4 space-y-2">
                  <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
                    <span className="text-xs text-slate-500 w-10">To</span>
                    <span className="text-sm text-slate-800">{customerEmail}</span>
                  </div>
                  <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
                    <span className="text-xs text-slate-500 w-10">Re</span>
                    <span className="text-sm text-slate-800 font-medium">Your inquiry about the {data.vehicle.year} {data.vehicle.make} {data.vehicle.model}</span>
                  </div>
                  <div className="pt-2">
                    <pre className="text-xs text-slate-600 whitespace-pre-wrap font-sans leading-relaxed max-h-48 overflow-y-auto">
                      {draft.body}
                    </pre>
                  </div>
                  <div className="pt-3 flex items-center justify-between">
                    <Button
                      onClick={handleSend}
                      disabled={phase === "sending"}
                      className="bg-fornest-orange hover:bg-fornest-orange-dark text-white gap-2 animate-pulse"
                    >
                      <Send className="h-4 w-4" />
                      {phase === "sending" ? "Sending…" : "Send"}
                    </Button>
                    <span className="text-xs text-slate-400">via Gmail · Fornest Automotive</span>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Sent toast */}
        <AnimatePresence>
          {phase === "sent" && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-xl px-4 py-3"
            >
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span className="text-sm font-medium text-green-700">Sent ✓ — email delivered to {customerEmail}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Thread view */}
        <Card>
          <CardHeader className="pb-2">
            <p className="font-semibold text-slate-900 text-sm">{draft.subject}</p>
            <p className="text-xs text-slate-500">2 messages</p>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Customer original */}
            <div className="border-l-2 border-slate-200 pl-3">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-5 h-5 rounded-full bg-slate-400 text-white text-[10px] font-bold flex items-center justify-center">
                  {data.customer.initials}
                </div>
                <span className="text-xs font-semibold text-slate-700">{data.customer.name ?? data.customer.email}</span>
                <span className="text-xs text-slate-400">9:42 AM</span>
              </div>
              <p className="text-xs text-slate-600">"{data.message}"</p>
            </div>

            {/* Fornest reply */}
            <div className={`border-l-2 pl-3 ${phase === "sent" ? "border-fornest-orange" : "border-slate-200 opacity-50"}`}>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-5 h-5 rounded-full bg-fornest-orange text-white text-[10px] font-bold flex items-center justify-center">
                  F
                </div>
                <span className="text-xs font-semibold text-slate-700">Fornest Automotive (via Lyra)</span>
                <span className="text-xs text-slate-400">{phase === "sent" ? "9:43 AM" : "pending…"}</span>
              </div>
              <pre className="text-xs text-slate-600 whitespace-pre-wrap font-sans leading-relaxed">
                {phase === "sent" ? draft.body : "Awaiting send…"}
              </pre>
            </div>
          </CardContent>
        </Card>
      </div>
    </SceneWrapper>
  );
}
