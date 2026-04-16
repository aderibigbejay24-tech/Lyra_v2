"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, AlertTriangle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SceneWrapper } from "./SceneWrapper";
import { useScenario } from "@/components/ScenarioContext";

function PhoneFrame({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative mx-auto w-[280px]">
      <div className="bg-slate-900 rounded-[2.5rem] p-2 shadow-2xl">
        <div className="bg-white rounded-[2rem] overflow-hidden h-[500px] relative">
          {/* Status bar */}
          <div className="bg-slate-50 flex items-center justify-between px-4 py-2">
            <span className="text-[10px] font-semibold text-slate-700">9:43</span>
            <div className="w-20 h-3 bg-slate-900 rounded-full absolute top-2 left-1/2 -translate-x-1/2" />
            <span className="text-[10px] text-slate-500">●●●●</span>
          </div>
          <div className="overflow-hidden h-full">{children}</div>
        </div>
      </div>
    </div>
  );
}

export function Scene08CustomerView() {
  const { data } = useScenario();
  const [screen, setScreen] = useState<"inbox" | "booking">("inbox");

  if (data.escalate) {
    return (
      <SceneWrapper id="scene-8" sceneNumber={8} title="Customer View" fr="Interstitial — Story Flow">
        <div className="flex justify-center">
          <Card className="max-w-lg w-full border-yellow-200 bg-yellow-50">
            <CardContent className="p-6 flex flex-col items-center gap-3 text-center">
              <AlertTriangle className="h-8 w-8 text-yellow-500" />
              <p className="font-semibold text-yellow-800">Human Taking Over</p>
              <p className="text-sm text-yellow-700">No automated booking flow. Escalation path active.</p>
            </CardContent>
          </Card>
        </div>
      </SceneWrapper>
    );
  }

  const draft = data.draft!;

  return (
    <SceneWrapper id="scene-8" sceneNumber={8} title="Customer View" fr="Interstitial — Story Flow">
      <div className="flex flex-col items-center gap-6">
        <p className="text-sm text-slate-500">
          {data.customer.name ?? "The customer"} receives the reply and taps the booking link.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-8">
          <PhoneFrame>
            <AnimatePresence mode="wait">
              {screen === "inbox" ? (
                <motion.div
                  key="inbox"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="p-3 h-full"
                >
                  {/* Email app header */}
                  <div className="text-sm font-semibold text-slate-800 mb-3">Mail · Inbox</div>
                  <div className="bg-fornest-orange/10 border border-fornest-orange/30 rounded-xl p-3 mb-2 cursor-pointer"
                    onClick={() => setScreen("booking")}>
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-5 h-5 rounded-full bg-fornest-orange text-white text-[9px] font-bold flex items-center justify-center">F</div>
                      <span className="text-[11px] font-bold text-slate-900">Fornest Automotive</span>
                      <span className="ml-auto text-[9px] text-slate-400">now</span>
                    </div>
                    <p className="text-[10px] font-semibold text-slate-800 mb-0.5">Re: Your inquiry about the {data.vehicle.year} {data.vehicle.make}</p>
                    <p className="text-[9px] text-slate-500 line-clamp-2">Hi {data.customer.name?.split(" ")[0]}, Great news — it's still available! On pricing...</p>
                    <div className="mt-2 flex items-center gap-1 text-[9px] text-fornest-orange font-semibold">
                      📅 Book your test drive →
                    </div>
                  </div>
                  <p className="text-[9px] text-center text-slate-400 mt-2">Tap the email to see the booking link</p>
                </motion.div>
              ) : (
                <motion.div
                  key="booking"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="p-3 h-full"
                >
                  <button onClick={() => setScreen("inbox")} className="text-[10px] text-fornest-orange mb-2 flex items-center gap-1">
                    ← Back
                  </button>
                  <div className="bg-white rounded-xl border border-slate-100 p-3">
                    <p className="text-[10px] font-bold text-slate-900 mb-0.5">Fornest Automotive</p>
                    <p className="text-[9px] text-slate-600 mb-2 leading-relaxed">
                      Hi {data.customer.name?.split(" ")[0] ?? "there"},<br />
                      It's still available! Click below to book your Saturday test drive.
                    </p>
                    <button className="w-full bg-fornest-orange text-white text-[10px] font-semibold py-2 rounded-lg">
                      📅 Book Test Drive
                    </button>
                  </div>
                  <div className="mt-3 bg-slate-50 rounded-xl p-3 border border-slate-200">
                    <p className="text-[9px] text-slate-500 mb-1 font-semibold uppercase tracking-wide">Booking confirmed</p>
                    <p className="text-[10px] font-semibold text-slate-900">Saturday, Apr 18 · 1:00 PM</p>
                    <p className="text-[9px] text-slate-600">{data.vehicle.year} {data.vehicle.make} {data.vehicle.model}</p>
                    <p className="text-[9px] text-green-600 mt-1">✓ Confirmation sent to {data.customer.email}</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </PhoneFrame>

          <div className="text-slate-400 text-2xl hidden sm:block">→</div>
          <div className="text-sm text-slate-500 max-w-[200px] text-center space-y-2">
            <p>Customer opens the email on their phone</p>
            <p>Taps <span className="font-semibold text-fornest-orange">Book Test Drive</span></p>
            <p>Booking confirmed in TidyCal</p>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setScreen(screen === "inbox" ? "booking" : "inbox")}
          className="gap-1"
        >
          Switch screen <ChevronRight className="h-3 w-3" />
        </Button>
      </div>
    </SceneWrapper>
  );
}
