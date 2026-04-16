"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";
import { Clock, Calendar, Footprints, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SceneWrapper } from "./SceneWrapper";
import { useScenario } from "@/components/ScenarioContext";
import { CHART_DATA, AUDIT_HISTORY } from "@/data/history";

const ORANGE = "#F56E24";
const SLATE = "#64748b";
const TELEGRAM_BLUE = "#2ea6dd";
const WHATSAPP_GREEN = "#25d366";

function StatCard({ icon: Icon, label, value, sub }: { icon: React.ElementType; label: string; value: string; sub: string }) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs text-slate-500 mb-1">{label}</p>
            <p className="text-2xl font-bold text-slate-900">{value}</p>
            <p className="text-xs text-slate-400 mt-1">{sub}</p>
          </div>
          <div className="w-9 h-9 rounded-xl bg-fornest-orange-light flex items-center justify-center">
            <Icon className="h-5 w-5 text-fornest-orange" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function Scene12Dashboard() {
  const { approvedChannel } = useScenario();

  // Build pie data from history + current session
  const telegramCount =
    AUDIT_HISTORY.filter((r) => r.channel_used === "Telegram").length +
    (approvedChannel === "telegram" ? 1 : 0);
  const whatsappCount =
    AUDIT_HISTORY.filter((r) => r.channel_used === "WhatsApp").length +
    (approvedChannel === "whatsapp" ? 1 : 0);

  const pieData = [
    { name: "Telegram", value: telegramCount },
    { name: "WhatsApp", value: whatsappCount },
  ];

  return (
    <SceneWrapper id="scene-12" sceneNumber={12} title="Metrics Dashboard" fr="Bonus · Retainer Story">
      <div className="space-y-6">
        {/* Stat cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard icon={Clock} label="Median first-touch" value="19s" sub="Last 14 days" />
          <StatCard icon={Calendar} label="Bookings this week" value="8" sub="+3 vs last week" />
          <StatCard icon={Footprints} label="Walk-ins traced" value="3" sub="From Lyra leads" />
          <StatCard icon={TrendingUp} label="Approval rate" value="94%" sub="All channels combined" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Bar chart */}
          <Card className="lg:col-span-2">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold text-slate-700">Response Latency · Last 14 Days (seconds)</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={CHART_DATA} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <XAxis dataKey="day" tick={{ fontSize: 10, fill: SLATE }} />
                  <YAxis tick={{ fontSize: 10, fill: SLATE }} />
                  <Tooltip
                    contentStyle={{ fontSize: 11, borderRadius: 8 }}
                    formatter={(v) => [`${v}s`, "Latency"]}
                  />
                  <Bar dataKey="latency" fill={ORANGE} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Pie chart */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold text-slate-700">Approvals by Channel</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={75}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    <Cell fill={TELEGRAM_BLUE} />
                    <Cell fill={WHATSAPP_GREEN} />
                  </Pie>
                  <Legend
                    iconSize={10}
                    iconType="circle"
                    formatter={(v) => <span style={{ fontSize: 11 }}>{v}</span>}
                  />
                  <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* CTA */}
        <Card className="bg-slate-900 border-0 text-white">
          <CardContent className="p-8 flex flex-col md:flex-row items-center justify-between gap-4">
            <div>
              <p className="text-2xl font-bold mb-1">Ready to go live?</p>
              <p className="text-slate-400">
                This prototype proves the flow. Swiftly Build Inc. wires the real integrations — Make.com, FastAPI, Evolution API — in 2 sprints.
              </p>
            </div>
            <a
              href="mailto:hello@swiftlybuild.com"
              className="shrink-0 px-6 py-3 bg-fornest-orange hover:bg-fornest-orange-dark text-white rounded-xl font-semibold transition-colors text-sm whitespace-nowrap"
            >
              Contact Swiftly Build Inc. →
            </a>
          </CardContent>
        </Card>
      </div>
    </SceneWrapper>
  );
}
