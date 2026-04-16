"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, Calendar, Clock, Car, Hash, AlertTriangle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { SceneWrapper } from "./SceneWrapper";
import { useScenario } from "@/components/ScenarioContext";

export function Scene09BookingConfirmed() {
  const { data, replayKey } = useScenario();
  const [show, setShow] = useState(false);

  useEffect(() => {
    setShow(false);
    const t = setTimeout(() => setShow(true), 300);
    return () => clearTimeout(t);
  }, [replayKey]);

  if (data.escalate) {
    return (
      <SceneWrapper id="scene-9" sceneNumber={9} title="Booking Confirmed" fr="FR-7 · TidyCal Booking">
        <div className="flex justify-center">
          <Card className="max-w-lg w-full border-yellow-200 bg-yellow-50">
            <CardContent className="p-6 flex flex-col items-center gap-3 text-center">
              <AlertTriangle className="h-8 w-8 text-yellow-500" />
              <p className="font-semibold text-yellow-800">Human Taking Over</p>
              <p className="text-sm text-yellow-700">No automated booking. Escalation path active.</p>
            </CardContent>
          </Card>
        </div>
      </SceneWrapper>
    );
  }

  const booking = data.bookingRep;

  return (
    <SceneWrapper id="scene-9" sceneNumber={9} title="Booking Confirmed" fr="FR-7 · TidyCal Booking">
      <div className="flex justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: show ? 1 : 0, scale: show ? 1 : 0.95 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-md"
        >
          <Card className="border-green-200 shadow-lg">
            {/* TidyCal-style header */}
            <div className="bg-gradient-to-br from-green-500 to-green-600 p-6 rounded-t-2xl text-white text-center">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: show ? 1 : 0 }}
                transition={{ delay: 0.3, type: "spring", stiffness: 200 }}
                className="flex justify-center mb-3"
              >
                <CheckCircle2 className="h-14 w-14 text-white drop-shadow" />
              </motion.div>
              <h3 className="text-xl font-bold">Booking Confirmed!</h3>
              <p className="text-green-100 text-sm mt-1">Your test drive is booked</p>
            </div>

            <CardContent className="p-6 space-y-4">
              {/* Rep */}
              <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
                <Avatar className="h-12 w-12 bg-fornest-orange">
                  <AvatarFallback className="bg-fornest-orange text-white font-bold">
                    {booking.initials}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-semibold text-slate-900">{booking.name}</p>
                  <p className="text-sm text-slate-500">{booking.role} · Fornest Automotive</p>
                </div>
              </div>

              {/* Details */}
              <div className="space-y-3">
                <div className="flex items-center gap-3 text-sm">
                  <Calendar className="h-4 w-4 text-fornest-orange shrink-0" />
                  <span className="text-slate-700">{booking.date}</span>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <Clock className="h-4 w-4 text-fornest-orange shrink-0" />
                  <span className="text-slate-700">{booking.time}</span>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <Car className="h-4 w-4 text-fornest-orange shrink-0" />
                  <span className="text-slate-700">{booking.vehicle} — test drive</span>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <Hash className="h-4 w-4 text-fornest-orange shrink-0" />
                  <span className="text-slate-700 font-mono text-xs">{booking.confirmationNumber}</span>
                </div>
              </div>

              <div className="bg-green-50 rounded-xl p-3 text-xs text-green-700 text-center">
                Confirmation email sent · Calendar invite created · Rep notified
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </SceneWrapper>
  );
}
