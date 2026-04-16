"use client";

import { AlertTriangle, User, DollarSign } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SceneWrapper } from "./SceneWrapper";
import { useScenario } from "@/components/ScenarioContext";

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = value >= 0.7 ? "bg-green-500" : value >= 0.4 ? "bg-yellow-400" : "bg-red-400";
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-slate-600">{value.toFixed(2)}</span>
    </div>
  );
}

export function Scene04Draft() {
  const { data } = useScenario();

  if (data.escalate) {
    return (
      <SceneWrapper id="scene-4" sceneNumber={4} title="Draft Card" fr="FR-3 · Claude Output">
        <div className="flex justify-center">
          <Card className="w-full max-w-xl border-red-300 bg-red-50">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-600" />
                <CardTitle className="text-red-800 text-lg">⚠ Escalation Only</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge className="bg-red-600 text-white border-0">escalate_to_human=true</Badge>
                  <Badge variant="outline" className="text-red-700 border-red-300">no_draft_generated</Badge>
                </div>
                <div className="bg-red-100 rounded-xl p-4">
                  <p className="text-xs font-semibold text-red-700 mb-1">Escalation reason:</p>
                  <p className="text-sm text-red-800">{data.escalationReason}</p>
                </div>
                <p className="text-xs text-red-600">
                  Lyra will not generate or send an automated reply. A human rep must handle this lead directly.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </SceneWrapper>
    );
  }

  const draft = data.draft!;

  return (
    <SceneWrapper id="scene-4" sceneNumber={4} title="Draft Card" fr="FR-3 · Claude Output">
      <div className="flex justify-center">
        <Card className="w-full max-w-2xl">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs text-slate-500 mb-1">Subject</p>
                <CardTitle className="text-base font-semibold text-slate-900 leading-snug">
                  {draft.subject}
                </CardTitle>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Body */}
              <div className="bg-slate-50 rounded-xl p-4">
                <pre className="text-sm text-slate-700 whitespace-pre-wrap font-sans leading-relaxed">
                  {draft.body}
                </pre>
              </div>

              {/* Chips row */}
              <div className="flex flex-wrap gap-2 items-center">
                <div className="flex items-center gap-1.5 bg-fornest-orange-light text-fornest-orange rounded-full px-3 py-1 text-xs font-semibold">
                  <User className="h-3 w-3" />
                  {draft.repName}
                </div>
                <Badge variant="green" className="text-xs">{draft.financingAngle}</Badge>
                <Badge variant="secondary" className="text-xs">{draft.toneCheck}</Badge>
              </div>

              {/* Confidence */}
              <div>
                <p className="text-xs text-slate-500 mb-1.5">Confidence score</p>
                <ConfidenceBar value={draft.confidence} />
              </div>

              {/* Footer */}
              <div className="flex items-center gap-1.5 pt-2 border-t border-slate-100">
                <DollarSign className="h-3 w-3 text-slate-400" />
                <span className="text-xs text-slate-400">Cost estimate: {draft.costEstimate} · claude-haiku-4-5</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </SceneWrapper>
  );
}
