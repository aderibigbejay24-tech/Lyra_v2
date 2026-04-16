"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Mail, Tag } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { SceneWrapper } from "./SceneWrapper";
import { useScenario } from "@/components/ScenarioContext";
import { INBOX_THREADS } from "@/data/history";
import { cn } from "@/lib/utils";

export function Scene01Inbox() {
  const { replayKey, data } = useScenario();

  const threads = INBOX_THREADS.map((t) => {
    if (t.isNew) {
      const veh = data.vehicle;
      const vehicleLabel = veh.year && veh.make && veh.model
        ? `${veh.year} ${veh.make} ${veh.model}`
        : "Vehicle Inquiry";
      return {
        ...t,
        sender: data.customer.name ?? data.customer.email,
        subject: `New Lead: ${vehicleLabel}`,
        preview: data.message.slice(0, 60) + "…",
      };
    }
    return t;
  });

  return (
    <SceneWrapper id="scene-1" sceneNumber={1} title="Inbox" fr="FR-1 · Lead Ingestion">
      <Card className="max-w-3xl">
        <CardContent className="p-0">
          {/* Gmail-style header */}
          <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-100 bg-slate-50 rounded-t-2xl">
            <Mail className="h-4 w-4 text-slate-400" />
            <span className="text-sm font-semibold text-slate-700">Inbox</span>
            <span className="ml-auto text-xs text-slate-400">Fornest Automotive · leads@fornest.ca</span>
          </div>

          <AnimatePresence mode="wait" key={replayKey}>
            {threads.map((thread, i) => (
              <motion.div
                key={`${replayKey}-${thread.id}`}
                initial={thread.isNew ? { y: -24, opacity: 0 } : { opacity: 1 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: thread.isNew ? 0.1 : i * 0.05, duration: 0.35 }}
                className={cn(
                  "flex items-start gap-3 px-4 py-3 border-b border-slate-100 last:border-0 cursor-pointer hover:bg-slate-50 transition-colors",
                  thread.isNew && "bg-blue-50/40"
                )}
              >
                {/* Avatar dot */}
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5",
                  thread.isNew ? "bg-fornest-orange text-white" : "bg-slate-200 text-slate-600"
                )}>
                  {thread.isNew ? data.customer.initials : thread.sender.slice(0, 2).toUpperCase()}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={cn(
                      "text-sm",
                      thread.isUnread ? "font-bold text-slate-900" : "font-medium text-slate-600"
                    )}>
                      {thread.sender}
                    </span>
                    {thread.chip && (
                      <span className="text-[10px] px-1.5 py-0.5 bg-fornest-orange text-white rounded font-semibold">
                        {thread.chip}
                      </span>
                    )}
                    {thread.isNew && (
                      <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 bg-green-100 text-green-700 rounded-full font-semibold">
                        <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse inline-block" />
                        New
                      </span>
                    )}
                  </div>
                  <p className={cn(
                    "text-sm truncate",
                    thread.isUnread ? "text-slate-800" : "text-slate-500"
                  )}>
                    {thread.subject}
                  </p>
                  <p className="text-xs text-slate-400 truncate">{thread.preview}</p>
                </div>

                <span className="text-xs text-slate-400 whitespace-nowrap">{thread.time}</span>
              </motion.div>
            ))}
          </AnimatePresence>
        </CardContent>
      </Card>
    </SceneWrapper>
  );
}
