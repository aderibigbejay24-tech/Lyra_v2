"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Send, MessageCircle, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SceneWrapper } from "./SceneWrapper";
import { useScenario } from "@/components/ScenarioContext";

export function Scene10RepNotified() {
  const { data, replayKey } = useScenario();
  const [show, setShow] = useState(false);

  useEffect(() => {
    setShow(false);
    const t = setTimeout(() => setShow(true), 300);
    return () => clearTimeout(t);
  }, [replayKey]);

  if (data.escalate) {
    return (
      <SceneWrapper id="scene-10" sceneNumber={10} title="Rep Notification" fr="FR-7 · Rep Booking Ping">
        <div className="flex justify-center">
          <Card className="max-w-lg w-full border-yellow-200 bg-yellow-50">
            <CardContent className="p-6 flex flex-col items-center gap-3 text-center">
              <AlertTriangle className="h-8 w-8 text-yellow-500" />
              <p className="font-semibold text-yellow-800">Human Taking Over</p>
              <p className="text-sm text-yellow-700">No rep notification. Escalation path active.</p>
            </CardContent>
          </Card>
        </div>
      </SceneWrapper>
    );
  }

  const booking = data.bookingRep;
  const customer = data.customer;
  const vehicle = data.vehicle;
  const notifText = `New booking · ${booking.date} ${booking.time} · ${customer.name ?? customer.email} · ${vehicle.year} ${vehicle.make} ${vehicle.model} (stock ${vehicle.stock ?? "N/A"})`;

  return (
    <SceneWrapper id="scene-10" sceneNumber={10} title="Rep Notification" fr="FR-7 · Rep Booking Ping">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Telegram to Ben */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: show ? 1 : 0, y: show ? 0 : 20 }}
          transition={{ delay: 0.1, duration: 0.4 }}
        >
          <Card className="bg-[#17212b] border-0 text-white">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-[#2ea6dd] flex items-center justify-center">
                  <Send className="h-3.5 w-3.5 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-sm">Telegram</p>
                  <p className="text-[10px] text-[#6d8a9e]">Lyra Guardian → {booking.name}</p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="bg-[#232e3c] rounded-xl p-3">
                <p className="text-[11px] text-[#2ea6dd] font-semibold mb-1">📅 New Booking</p>
                <p className="text-xs text-[#e4e6eb] leading-relaxed">{notifText}</p>
              </div>
              <p className="text-[10px] text-[#6d8a9e] mt-2">Delivered · now ✓✓</p>
            </CardContent>
          </Card>
        </motion.div>

        {/* WhatsApp to Ben */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: show ? 1 : 0, y: show ? 0 : 20 }}
          transition={{ delay: 0.15, duration: 0.4 }}
        >
          <Card className="border-0 overflow-hidden">
            <div className="bg-[#075e54] px-4 py-3 flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-[#25d366] flex items-center justify-center">
                <MessageCircle className="h-3.5 w-3.5 text-white" />
              </div>
              <div>
                <p className="font-semibold text-sm text-white">WhatsApp</p>
                <p className="text-[10px] text-green-200">Lyra Guardian → {booking.name}</p>
              </div>
            </div>
            <CardContent className="bg-[#ece5dd] p-4">
              <div className="bg-white rounded-xl rounded-tl-none p-3 shadow-sm">
                <p className="text-[11px] text-[#075e54] font-semibold mb-1">📅 New Booking</p>
                <p className="text-xs text-slate-800 leading-relaxed">{notifText}</p>
                <p className="text-[10px] text-slate-400 mt-1.5 text-right">now ✓✓</p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <p className="text-xs text-slate-400 text-center mt-3">
        Delivered in 18s from lead ingestion · Both channels notified simultaneously
      </p>
    </SceneWrapper>
  );
}
