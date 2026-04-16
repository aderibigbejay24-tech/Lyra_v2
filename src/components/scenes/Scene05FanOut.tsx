"use client";

import { Send, MessageCircle, Clock } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SceneWrapper } from "./SceneWrapper";
import { useScenario } from "@/components/ScenarioContext";

function TelegramCard({ body, repName, isEscalation }: { body: string; repName: string; isEscalation: boolean }) {
  return (
    <Card className="bg-[#17212b] border-0 text-white">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-[#2ea6dd] flex items-center justify-center">
            <Send className="h-4 w-4 text-white" />
          </div>
          <div>
            <p className="font-semibold text-sm">Telegram</p>
            <p className="text-[10px] text-[#6d8a9e]">Lyra Guardian Bot → {repName}</p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isEscalation ? (
          <div className="bg-red-900/40 border border-red-500/50 rounded-xl p-4 text-center">
            <p className="text-2xl mb-2">🚨</p>
            <p className="font-semibold text-red-300 text-sm">Escalation alert posted</p>
            <p className="text-xs text-red-400 mt-1">No draft to approve — human intervention required</p>
          </div>
        ) : (
          <>
            <div className="bg-[#232e3c] rounded-xl p-3 mb-3 text-sm text-[#e4e6eb] leading-relaxed text-xs">
              {body.slice(0, 180)}…
            </div>
            <p className="text-[10px] text-[#6d8a9e] mb-3">
              <Clock className="h-3 w-3 inline mr-1" />
              sent 9:43 AM · 30-min timeout → secondary approver
            </p>
            <div className="flex gap-2">
              {["✅ Approve", "✏️ Edit", "❌ Deny"].map((label) => (
                <button
                  key={label}
                  className="flex-1 py-1.5 rounded-lg bg-[#2ea6dd]/20 text-[#2ea6dd] text-xs font-medium border border-[#2ea6dd]/30 hover:bg-[#2ea6dd]/30 transition-colors"
                >
                  {label}
                </button>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function WhatsAppCard({ body, repName, isEscalation }: { body: string; repName: string; isEscalation: boolean }) {
  return (
    <Card className="border-0 overflow-hidden">
      <div className="bg-[#075e54] px-4 py-3 flex items-center gap-2">
        <div className="w-8 h-8 rounded-full bg-[#25d366] flex items-center justify-center">
          <MessageCircle className="h-4 w-4 text-white" />
        </div>
        <div>
          <p className="font-semibold text-sm text-white">WhatsApp</p>
          <p className="text-[10px] text-green-200">Lyra Guardian → {repName}</p>
        </div>
      </div>
      <CardContent className="bg-[#ece5dd] p-4">
        {isEscalation ? (
          <div className="bg-red-100 border border-red-300 rounded-xl p-4 text-center">
            <p className="text-2xl mb-2">🚨</p>
            <p className="font-semibold text-red-700 text-sm">Escalation alert posted</p>
            <p className="text-xs text-red-500 mt-1">No draft to approve — human intervention required</p>
          </div>
        ) : (
          <>
            <div className="bg-white rounded-xl rounded-tl-none p-3 shadow-sm mb-3">
              <p className="text-xs text-[#075e54] font-semibold mb-1">Lyra Guardian</p>
              <p className="text-sm text-slate-800 leading-relaxed text-xs">
                {body.slice(0, 180)}…
              </p>
              <p className="text-[10px] text-slate-400 mt-1.5 text-right">
                <Clock className="h-3 w-3 inline mr-0.5" />
                9:43 AM ✓✓
              </p>
            </div>
            <p className="text-[10px] text-slate-500 mb-3">30-min timeout escalates to secondary approver</p>
            <div className="flex gap-2 flex-wrap">
              {["✅ Approve", "✏️ Edit", "❌ Deny"].map((label) => (
                <button
                  key={label}
                  className="flex-1 min-w-[80px] py-1.5 rounded-lg bg-white text-[#075e54] text-xs font-semibold border border-[#075e54]/30 hover:bg-green-50 transition-colors shadow-sm"
                >
                  {label}
                </button>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export function Scene05FanOut() {
  const { data } = useScenario();
  const body = data.draft?.body ?? "";
  const repName = data.draft?.repName ?? "Foster Kielce";

  return (
    <SceneWrapper id="scene-5" sceneNumber={5} title="Dual Channel Fan-out" fr="FR-4 · Telegram + WhatsApp Approval">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <TelegramCard body={body} repName={repName} isEscalation={data.escalate} />
        <WhatsAppCard body={body} repName={repName} isEscalation={data.escalate} />
      </div>
      {!data.escalate && (
        <p className="mt-3 text-xs text-slate-400 text-center">
          FR-9 · 30-minute timeout auto-escalates to secondary approver if no response on either channel
        </p>
      )}
    </SceneWrapper>
  );
}
