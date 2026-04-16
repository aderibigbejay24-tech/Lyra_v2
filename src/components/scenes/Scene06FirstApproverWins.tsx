"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, MessageCircle, CheckCircle2, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SceneWrapper } from "./SceneWrapper";
import { useScenario } from "@/components/ScenarioContext";

export function Scene06FirstApproverWins() {
  const { data, approvedChannel, setApprovedChannel } = useScenario();

  const handleApprove = (channel: "telegram" | "whatsapp") => {
    setApprovedChannel(channel);
  };

  const repName = data.draft?.repName ?? "Foster Kielce";

  if (data.escalate) {
    return (
      <SceneWrapper id="scene-6" sceneNumber={6} title="First-Approver-Wins" fr="FR-5 · Race Condition Resolved">
        <div className="flex justify-center">
          <Card className="max-w-lg w-full border-red-200 bg-red-50">
            <CardContent className="p-6 flex flex-col items-center gap-3 text-center">
              <AlertTriangle className="h-10 w-10 text-red-500" />
              <p className="font-semibold text-red-800 text-lg">Human Taking Over</p>
              <p className="text-sm text-red-600">
                Escalation path active. Both channels show 🚨 alert — no Approve button available.
                A senior rep has been paged directly.
              </p>
              <div className="bg-red-100 rounded-xl p-3 text-xs text-red-700 w-full">
                <strong>FR-10 · Escalation path:</strong> No automated reply will be sent. Lead flagged for Sam Nakamura (GM).
              </div>
            </CardContent>
          </Card>
        </div>
      </SceneWrapper>
    );
  }

  return (
    <SceneWrapper id="scene-6" sceneNumber={6} title="First-Approver-Wins" fr="FR-5 · Race Condition Resolved">
      {!approvedChannel && (
        <p className="text-sm text-slate-500 mb-4 text-center">
          Click <strong>Approve</strong> on either card to simulate {repName} responding.
        </p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Telegram card */}
        <motion.div
          animate={{
            opacity: approvedChannel === "whatsapp" ? 0.4 : 1,
            scale: approvedChannel === "whatsapp" ? 0.98 : 1,
          }}
          transition={{ duration: 0.5 }}
        >
          <Card
            className={`bg-[#17212b] border-0 text-white relative overflow-hidden transition-all ${
              approvedChannel === "telegram" ? "ring-2 ring-green-400 shadow-lg shadow-green-500/20" : ""
            }`}
          >
            {approvedChannel === "whatsapp" && (
              <div className="absolute inset-0 bg-slate-900/60 z-10 flex items-center justify-center rounded-2xl">
                <div className="bg-slate-700 rounded-xl px-4 py-2 text-sm font-medium text-slate-300">
                  ✅ Handled on WhatsApp
                </div>
              </div>
            )}
            {approvedChannel === "telegram" && (
              <motion.div
                initial={{ scale: 0.5, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="absolute top-3 right-3 z-10"
              >
                <div className="bg-green-500 text-white text-xs font-bold px-3 py-1.5 rounded-full flex items-center gap-1.5 shadow-lg">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Approved by {repName}
                </div>
              </motion.div>
            )}
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-[#2ea6dd] flex items-center justify-center">
                  <Send className="h-3.5 w-3.5 text-white" />
                </div>
                <span className="font-semibold text-sm">Telegram</span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="bg-[#232e3c] rounded-xl p-3 mb-3 text-xs text-[#e4e6eb] leading-relaxed">
                {data.draft?.body?.slice(0, 120)}…
              </div>
              {!approvedChannel && (
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => handleApprove("telegram")}
                    className="flex-1 bg-green-600 hover:bg-green-700 text-white text-xs h-8"
                  >
                    ✅ Approve
                  </Button>
                  <Button size="sm" variant="ghost" className="flex-1 text-slate-300 text-xs h-8 border border-slate-600">
                    ✏️ Edit
                  </Button>
                  <Button size="sm" variant="ghost" className="flex-1 text-slate-300 text-xs h-8 border border-slate-600">
                    ❌ Deny
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* WhatsApp card */}
        <motion.div
          animate={{
            opacity: approvedChannel === "telegram" ? 0.4 : 1,
            scale: approvedChannel === "telegram" ? 0.98 : 1,
          }}
          transition={{ duration: 0.5 }}
        >
          <Card className={`border-0 overflow-hidden relative ${
            approvedChannel === "whatsapp" ? "ring-2 ring-green-400 shadow-lg shadow-green-500/20" : ""
          }`}>
            {approvedChannel === "telegram" && (
              <div className="absolute inset-0 bg-white/70 z-10 flex items-center justify-center rounded-2xl">
                <div className="bg-slate-200 rounded-xl px-4 py-2 text-sm font-medium text-slate-600">
                  ✅ Handled on Telegram
                </div>
              </div>
            )}
            {approvedChannel === "whatsapp" && (
              <motion.div
                initial={{ scale: 0.5, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="absolute top-3 right-3 z-10"
              >
                <div className="bg-green-500 text-white text-xs font-bold px-3 py-1.5 rounded-full flex items-center gap-1.5 shadow-lg">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Approved by {repName}
                </div>
              </motion.div>
            )}
            <div className="bg-[#075e54] px-4 py-3 flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-[#25d366] flex items-center justify-center">
                <MessageCircle className="h-3.5 w-3.5 text-white" />
              </div>
              <span className="font-semibold text-sm text-white">WhatsApp</span>
            </div>
            <CardContent className="bg-[#ece5dd] p-4">
              <div className="bg-white rounded-xl rounded-tl-none p-3 shadow-sm mb-3">
                <p className="text-xs text-[#075e54] font-semibold mb-1">Lyra Guardian</p>
                <p className="text-xs text-slate-700 leading-relaxed">
                  {data.draft?.body?.slice(0, 120)}…
                </p>
              </div>
              {!approvedChannel && (
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => handleApprove("whatsapp")}
                    className="flex-1 bg-green-600 hover:bg-green-700 text-white text-xs h-8"
                  >
                    ✅ Approve
                  </Button>
                  <Button size="sm" variant="outline" className="flex-1 text-xs h-8">
                    ✏️ Edit
                  </Button>
                  <Button size="sm" variant="outline" className="flex-1 text-xs h-8">
                    ❌ Deny
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {approvedChannel && (
        <motion.p
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center text-sm text-green-700 font-medium mt-4"
        >
          ✅ {repName} approved via {approvedChannel === "telegram" ? "Telegram" : "WhatsApp"} · Duplicate suppressed on the other channel
        </motion.p>
      )}
    </SceneWrapper>
  );
}
