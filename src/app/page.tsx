"use client";

import { ScenarioProvider } from "@/components/ScenarioContext";
import { Header } from "@/components/Header";
import { Stepper } from "@/components/Stepper";
import { Scene01Inbox } from "@/components/scenes/Scene01Inbox";
import { Scene02Parsed } from "@/components/scenes/Scene02Parsed";
import { Scene03Drafting } from "@/components/scenes/Scene03Drafting";
import { Scene04Draft } from "@/components/scenes/Scene04Draft";
import { Scene05FanOut } from "@/components/scenes/Scene05FanOut";
import { Scene06FirstApproverWins } from "@/components/scenes/Scene06FirstApproverWins";
import { Scene07EmailSent } from "@/components/scenes/Scene07EmailSent";
import { Scene08CustomerView } from "@/components/scenes/Scene08CustomerView";
import { Scene09BookingConfirmed } from "@/components/scenes/Scene09BookingConfirmed";
import { Scene10RepNotified } from "@/components/scenes/Scene10RepNotified";
import { Scene11SheetLog } from "@/components/scenes/Scene11SheetLog";
import { Scene12Dashboard } from "@/components/scenes/Scene12Dashboard";

export default function Page() {
  return (
    <ScenarioProvider>
      <Header />
      <Stepper />
      <main>
        <Scene01Inbox />
        <Scene02Parsed />
        <Scene03Drafting />
        <Scene04Draft />
        <Scene05FanOut />
        <Scene06FirstApproverWins />
        <Scene07EmailSent />
        <Scene08CustomerView />
        <Scene09BookingConfirmed />
        <Scene10RepNotified />
        <Scene11SheetLog />
        <Scene12Dashboard />
      </main>
      <footer className="py-6 text-center text-xs text-slate-400 border-t border-slate-200">
        Lyra Lead Guardian <span className="text-fornest-orange font-semibold">v3</span> · Built by Swiftly Build Inc. · Zero backend — all data mocked ·{" "}
        <span className="text-fornest-orange">Fornest Automotive</span> · Spec v2.1 · April 2026
      </footer>
    </ScenarioProvider>
  );
}
