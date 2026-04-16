"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, AlertTriangle, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SceneWrapper } from "./SceneWrapper";
import { useScenario } from "@/components/ScenarioContext";

const RAW_ADF_CLEAN = `<?xml version="1.0" encoding="UTF-8"?>
<adf>
  <prospect>
    <requestdate>2024-04-16T09:42:00-07:00</requestdate>
    <vehicle interest="buy" status="used">
      <year>2020</year>
      <make>Honda</make>
      <model>Accord</model>
      <trim>Sport 1.5T</trim>
      <vin>1HGCV1F34LA012345</vin>
      <stock>FN-24-0112</stock>
      <price type="asking" currency="CAD">26995</price>
    </vehicle>
    <customer>
      <contact primarycontact="1">
        <name part="full">Priya Singh</name>
        <email>priya.singh@example.com</email>
        <phone type="voice">403-555-0199</phone>
      </contact>
      <comments>Hi, is this Accord still available? I'd like to
know if there's any wiggle room on price and whether
you offer financing...</comments>
    </customer>
    <vendor>
      <vendorname>AutoTrader</vendorname>
    </vendor>
  </prospect>
</adf>`;

const RAW_ADF_VAGUE = `<?xml version="1.0" encoding="UTF-8"?>
<!-- PARSE DEGRADED: regex fallback used -->
<adf>
  <prospect>
    <requestdate>2024-04-16T09:42:00-07:00</requestdate>
    <vehicle interest="buy" status="used">
      <!-- No vehicle data extracted -->
    </vehicle>
    <customer>
      <contact primarycontact="1">
        <!-- name: NOT FOUND -->
        <email>buyer99@example.com</email>
        <!-- phone: NOT FOUND -->
      </contact>
      <comments>is this still for sale thx</comments>
    </customer>
  </prospect>
</adf>`;

const RAW_ADF_HOSTILE = `<?xml version="1.0" encoding="UTF-8"?>
<adf>
  <prospect>
    <requestdate>2024-04-16T09:42:00-07:00</requestdate>
    <vehicle interest="buy" status="used">
      <year>2019</year>
      <make>BMW</make>
      <model>330i</model>
      <trim>xDrive</trim>
      <vin>WBA8E9G55KNU12345</vin>
      <stock>FN-24-0155</stock>
      <price type="asking" currency="CAD">38990</price>
    </vehicle>
    <customer>
      <contact primarycontact="1">
        <name part="full">Jordan</name>
        <email>jordan.escalation@example.com</email>
        <phone type="voice">403-555-0888</phone>
      </contact>
      <comments>3rd time I've emailed. If I don't hear back in
24h I am reporting you to AMVIC and filing a complaint
with the BBB. My lawyer is aware.</comments>
    </customer>
  </prospect>
</adf>`;

function getRaw(scenario: string) {
  if (scenario === "vague") return RAW_ADF_VAGUE;
  if (scenario === "hostile") return RAW_ADF_HOSTILE;
  return RAW_ADF_CLEAN;
}

export function Scene02Parsed() {
  const { data, scenario } = useScenario();
  const [showRaw, setShowRaw] = useState(false);

  const c = data.customer;
  const v = data.vehicle;
  const inv = data.inventoryMatch;

  return (
    <SceneWrapper id="scene-2" sceneNumber={2} title="Lead Parsed" fr="FR-2 · ADF Parse + Inventory Match">
      {data.parseDegraded && (
        <div className="mb-4 flex items-start gap-2 p-3 rounded-xl bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm">
          <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0 text-yellow-600" />
          <div>
            <span className="font-semibold">Parse degraded</span> — XML structure incomplete. Regex fallback extracted email only. Manual review recommended.
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Raw ADF */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Raw ADF/XML Payload</CardTitle>
              <button
                onClick={() => setShowRaw(!showRaw)}
                className="flex items-center gap-1 text-xs text-fornest-orange font-medium hover:underline"
              >
                {showRaw ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                {showRaw ? "Hide raw" : "Show raw"}
              </button>
            </div>
          </CardHeader>
          <CardContent>
            {showRaw ? (
              <pre className="text-[11px] bg-slate-900 text-green-400 p-4 rounded-xl overflow-x-auto leading-relaxed">
                {getRaw(scenario)}
              </pre>
            ) : (
              <div className="flex items-center justify-center h-24 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                <p className="text-xs text-slate-400">Click "Show raw" to view the ADF/XML payload</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Parsed fields */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Parsed Fields</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
                <div>
                  <dt className="text-xs text-slate-500 mb-0.5">Name</dt>
                  <dd className="font-medium text-slate-900">{c.name ?? <span className="text-slate-400 italic">not found</span>}</dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500 mb-0.5">Email</dt>
                  <dd className="font-medium text-slate-900 text-xs break-all">{c.email}</dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500 mb-0.5">Phone</dt>
                  <dd className="font-medium text-slate-900">{c.phone ?? <span className="text-slate-400 italic">not found</span>}</dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500 mb-0.5">Source</dt>
                  <dd><Badge variant="orange" className="text-[10px]">AutoTrader</Badge></dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500 mb-0.5">Vehicle</dt>
                  <dd className="font-medium text-slate-900">
                    {v.year && v.make && v.model
                      ? `${v.year} ${v.make} ${v.model} ${v.trim ?? ""}`
                      : <span className="text-slate-400 italic">unclear</span>}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500 mb-0.5">VIN</dt>
                  <dd className="font-medium text-slate-900 text-xs font-mono">{v.vin ?? <span className="text-slate-400 italic">—</span>}</dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500 mb-0.5">Stock</dt>
                  <dd className="font-medium text-slate-900 font-mono text-xs">{v.stock ?? <span className="text-slate-400 italic">—</span>}</dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500 mb-0.5">Listed Price</dt>
                  <dd className="font-medium text-slate-900">
                    {v.price ? `$${v.price.toLocaleString()} CAD` : <span className="text-slate-400 italic">—</span>}
                  </dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-xs text-slate-500 mb-0.5">Customer Message</dt>
                  <dd className="text-slate-700 text-xs leading-relaxed bg-slate-50 p-2 rounded-lg">"{data.message}"</dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          {/* Inventory match */}
          {inv ? (
            <Card className="border-green-200">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  <CardTitle className="text-base text-green-800">Inventory Match</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="font-bold text-slate-900">{inv.year} {inv.make} {inv.model}</p>
                    <p className="text-sm text-slate-600">{inv.trim}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-fornest-orange">{inv.price}</p>
                    <p className="text-xs text-slate-500">Stock {inv.stock}</p>
                  </div>
                </div>
                <div className="flex gap-4 text-xs text-slate-600 mb-3">
                  <span>{inv.mileage}</span>
                  <span>·</span>
                  <span>{inv.color}</span>
                </div>
                <ul className="text-xs text-slate-700 space-y-1">
                  {inv.highlights.map((h) => (
                    <li key={h} className="flex items-center gap-1.5">
                      <span className="text-green-500">✓</span> {h}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ) : (
            <Card className="border-yellow-200 bg-yellow-50">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-yellow-800">
                  <AlertTriangle className="h-4 w-4" />
                  <p className="text-sm font-medium">No inventory match — vehicle not specified</p>
                </div>
                <p className="text-xs text-yellow-700 mt-1">Clarification required before matching stock.</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </SceneWrapper>
  );
}
