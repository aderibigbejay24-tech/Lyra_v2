"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Table2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SceneWrapper } from "./SceneWrapper";
import { useScenario } from "@/components/ScenarioContext";
import { AUDIT_HISTORY } from "@/data/history";

export function Scene11SheetLog() {
  const { data, approvedChannel, replayKey } = useScenario();
  const [flash, setFlash] = useState(false);

  useEffect(() => {
    setFlash(false);
    const t = setTimeout(() => setFlash(true), 400);
    return () => clearTimeout(t);
  }, [replayKey]);

  const newRow = {
    lead_id: "LG-2024-0405",
    source: "AutoTrader",
    channel_used: approvedChannel
      ? approvedChannel === "telegram" ? "Telegram" : "WhatsApp"
      : data.escalate ? "—" : "Telegram",
    approver: data.draft?.repName?.split(" ")[0] ?? "—",
    decision: data.escalate ? "escalated" : "approved",
    latency_s: data.escalate ? 0 : 18,
    claude_cost_usd: data.draft?.costEstimate ?? "$0.0000",
    outcome: data.auditOutcome,
  };

  const outcomeColor = (o: string) => {
    if (o === "booked") return "bg-green-100 text-green-700";
    if (o === "escalated") return "bg-red-100 text-red-700";
    if (o === "walk_in") return "bg-blue-100 text-blue-700";
    return "bg-yellow-100 text-yellow-700";
  };

  return (
    <SceneWrapper id="scene-11" sceneNumber={11} title="Google Sheet Audit Log" fr="FR-8 · Audit Trail">
      <Card className="overflow-hidden">
        <CardHeader className="pb-3 bg-slate-50 border-b border-slate-200 rounded-t-2xl">
          <div className="flex items-center gap-2">
            <Table2 className="h-4 w-4 text-green-600" />
            <CardTitle className="text-sm font-semibold text-slate-700">
              Lyra Lead Guardian · Audit Log — Sheet1
            </CardTitle>
            <span className="ml-auto text-xs text-slate-400">{AUDIT_HISTORY.length + 1} rows</span>
          </div>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                {["lead_id", "source", "channel_used", "approver", "decision", "latency_s", "claude_cost_usd", "outcome"].map((col) => (
                  <th key={col} className="text-left px-3 py-2 text-slate-500 font-semibold whitespace-nowrap">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* Historical rows */}
              {AUDIT_HISTORY.map((row) => (
                <tr key={row.lead_id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-3 py-2 font-mono text-slate-500">{row.lead_id}</td>
                  <td className="px-3 py-2 text-slate-600">{row.source}</td>
                  <td className="px-3 py-2 text-slate-600">{row.channel_used}</td>
                  <td className="px-3 py-2 text-slate-600">{row.approver}</td>
                  <td className="px-3 py-2">
                    <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">{row.decision}</span>
                  </td>
                  <td className="px-3 py-2 text-slate-600">{row.latency_s}s</td>
                  <td className="px-3 py-2 font-mono text-slate-600">{row.claude_cost_usd}</td>
                  <td className="px-3 py-2">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${outcomeColor(row.outcome)}`}>
                      {row.outcome}
                    </span>
                  </td>
                </tr>
              ))}

              {/* New row with flash */}
              <motion.tr
                className={`border-b border-slate-100 transition-colors ${flash ? "" : "opacity-0"}`}
                animate={{ opacity: flash ? 1 : 0 }}
                transition={{ duration: 0.3 }}
                style={{
                  backgroundColor: flash ? "#fef9c3" : "transparent",
                  transition: "background-color 2s ease-out",
                }}
              >
                <td className="px-3 py-2 font-mono font-bold text-slate-900">{newRow.lead_id}</td>
                <td className="px-3 py-2 font-semibold text-slate-800">{newRow.source}</td>
                <td className="px-3 py-2 font-semibold text-slate-800">{newRow.channel_used}</td>
                <td className="px-3 py-2 font-semibold text-slate-800">{newRow.approver}</td>
                <td className="px-3 py-2">
                  <span className={`px-1.5 py-0.5 rounded font-semibold ${newRow.decision === "escalated" ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"}`}>
                    {newRow.decision}
                  </span>
                </td>
                <td className="px-3 py-2 font-semibold text-slate-800">{newRow.latency_s}s</td>
                <td className="px-3 py-2 font-mono font-semibold text-slate-800">{newRow.claude_cost_usd}</td>
                <td className="px-3 py-2">
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${outcomeColor(newRow.outcome)}`}>
                    {newRow.outcome}
                  </span>
                </td>
              </motion.tr>
            </tbody>
          </table>
        </CardContent>
      </Card>
    </SceneWrapper>
  );
}
