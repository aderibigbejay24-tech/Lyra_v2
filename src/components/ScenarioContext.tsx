"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { Scenario, SCENARIOS, LeadScenario } from "@/data/scenarios";

interface ScenarioContextValue {
  scenario: Scenario;
  setScenario: (s: Scenario) => void;
  data: LeadScenario;
  replayKey: number;
  replay: () => void;
  approvedChannel: "telegram" | "whatsapp" | null;
  setApprovedChannel: (ch: "telegram" | "whatsapp") => void;
}

const ScenarioContext = createContext<ScenarioContextValue | null>(null);

export function ScenarioProvider({ children }: { children: React.ReactNode }) {
  const [scenario, setScenarioState] = useState<Scenario>("clean");
  const [replayKey, setReplayKey] = useState(0);
  const [approvedChannel, setApprovedChannelState] = useState<"telegram" | "whatsapp" | null>(null);

  const setScenario = useCallback((s: Scenario) => {
    setScenarioState(s);
    setReplayKey((k) => k + 1);
    setApprovedChannelState(null);
  }, []);

  const replay = useCallback(() => {
    setReplayKey((k) => k + 1);
    setApprovedChannelState(null);
  }, []);

  const setApprovedChannel = useCallback((ch: "telegram" | "whatsapp") => {
    setApprovedChannelState(ch);
  }, []);

  return (
    <ScenarioContext.Provider
      value={{
        scenario,
        setScenario,
        data: SCENARIOS[scenario],
        replayKey,
        replay,
        approvedChannel,
        setApprovedChannel,
      }}
    >
      {children}
    </ScenarioContext.Provider>
  );
}

export function useScenario() {
  const ctx = useContext(ScenarioContext);
  if (!ctx) throw new Error("useScenario must be used within ScenarioProvider");
  return ctx;
}
