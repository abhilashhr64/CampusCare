"use client";

import React, { useState } from "react";
import {
  QrCode,
  Camera,
  Scan,
  Printer,
  CheckCircle2,
  AlertTriangle,
  Building2,
  Tag,
  ArrowRight,
  Sparkles,
  Layers,
  Cpu,
  Wifi,
  X,
} from "lucide-react";

export interface CampusFacility {
  code: string;
  name: string;
  building: string;
  floor: string;
  category: "LAB" | "CLASSROOM" | "HOSTEL" | "LIBRARY" | "AMENITY";
  equipment: string[];
  healthScore: number;
  openTickets: number;
  lastInspected: string;
}

export const PRESET_FACILITIES: CampusFacility[] = [
  {
    code: "QR:LAB-4-401",
    name: "Advanced AI & GPU Computing Laboratory",
    building: "Alan Turing Center",
    floor: "4th Floor (West Wing)",
    category: "LAB",
    equipment: ["4x NVIDIA RTX A6000 Racks", "Dual 4K Laser Projectors", "Cisco Catalyst WiFi 6 AP"],
    healthScore: 94,
    openTickets: 1,
    lastInspected: "Today, 08:30 AM",
  },
  {
    code: "QR:HOSTEL-BLOCK-B",
    name: "North Hostel Residency - Block B",
    building: "North Residential Complex",
    floor: "2nd Floor Geyser Utility",
    category: "HOSTEL",
    equipment: ["Industrial Heat-Pump Geyser", "Emergency Backup Line", "Water Pressure Regulator"],
    healthScore: 82,
    openTickets: 1,
    lastInspected: "Yesterday, 04:15 PM",
  },
  {
    code: "QR:LIBRARY-2F",
    name: "Dr. Kalam Digital Research Commons",
    building: "Central Knowledge Hub",
    floor: "2nd Floor (Quiet Pods)",
    category: "LIBRARY",
    equipment: ["Networked High-Speed Laser Printer", "Soundproof Acoustic Glazing", "UPS Power Circuit"],
    healthScore: 99,
    openTickets: 0,
    lastInspected: "Today, 09:00 AM",
  },
  {
    code: "QR:AUDITORIUM-MAIN",
    name: "Sir C.V. Raman Grand Auditorium",
    building: "Main Academic Complex",
    floor: "Ground Floor",
    category: "AMENITY",
    equipment: ["Bose Array Sound Reinforcement", "Stage Lighting Truss", "Motorized 300-inch Screen"],
    healthScore: 96,
    openTickets: 0,
    lastInspected: "3 days ago",
  },
];

interface FacilityQrSuiteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectFacilityForGrievance: (facilityCode: string, category: string) => void;
}

export function FacilityQrSuiteModal({
  isOpen,
  onClose,
  onSelectFacilityForGrievance,
}: FacilityQrSuiteModalProps) {
  const [activeTab, setActiveTab] = useState<"SCANNER" | "GENERATOR">("SCANNER");
  const [scannedFacility, setScannedFacility] = useState<CampusFacility | null>(PRESET_FACILITIES[0]);
  const [isScanning, setIsScanning] = useState<boolean>(true);

  // Generator State
  const [customTag, setCustomTag] = useState<string>("QR:TURING-305");
  const [customName, setCustomName] = useState<string>("Robotics & Embedded Systems Lab");
  const [customBuilding, setCustomBuilding] = useState<string>("Alan Turing Center");
  const [customEquipment, setCustomEquipment] = useState<string>("Kuka Robotic Arms, 3D Printers, Soldering Stations");

  if (!isOpen) return null;

  const handlePrintLabel = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-fadeIn">
      <div className="glass-panel w-full max-w-2xl rounded-2xl border border-slate-800 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-800/80 bg-slate-900/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-md shadow-sky-500/20">
              <QrCode className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                Facility QR Code Suite
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-500/15 text-sky-300 border border-sky-500/30">
                  Geo-Tag & Service Link
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Instant classroom & facility incident dispatch via hardware-anchored QR markers
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-slate-800/80 bg-slate-950/40 px-5 pt-3 gap-2">
          <button
            onClick={() => setActiveTab("SCANNER")}
            className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-t-xl transition-all border-b-2 ${
              activeTab === "SCANNER"
                ? "border-sky-500 text-sky-400 bg-slate-900/80"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Camera className="w-3.5 h-3.5" />
            Interactive QR Scanner
          </button>

          <button
            onClick={() => setActiveTab("GENERATOR")}
            className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-t-xl transition-all border-b-2 ${
              activeTab === "GENERATOR"
                ? "border-indigo-500 text-indigo-400 bg-slate-900/80"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Printer className="w-3.5 h-3.5" />
            Facility QR Label Generator
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-5 text-xs">
          {activeTab === "SCANNER" ? (
            <div className="space-y-4">
              {/* Simulated Camera Viewfinder */}
              <div className="relative rounded-2xl bg-slate-950 border border-slate-800 h-56 overflow-hidden flex flex-col items-center justify-center">
                {/* Background optical grid */}
                <div className="absolute inset-0 bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:16px_16px] opacity-15" />

                {/* Reticle HUD Frame */}
                <div className="relative w-40 h-40 border-2 border-dashed border-sky-400/60 rounded-xl flex items-center justify-center shadow-inner">
                  {/* Corner Targets */}
                  <div className="absolute top-0 left-0 w-3 h-3 border-t-2 border-l-2 border-sky-400" />
                  <div className="absolute top-0 right-0 w-3 h-3 border-t-2 border-r-2 border-sky-400" />
                  <div className="absolute bottom-0 left-0 w-3 h-3 border-b-2 border-l-2 border-sky-400" />
                  <div className="absolute bottom-0 right-0 w-3 h-3 border-b-2 border-r-2 border-sky-400" />

                  {/* Laser Scan Beam */}
                  {isScanning && (
                    <div className="absolute inset-x-1 top-2 h-0.5 bg-gradient-to-r from-transparent via-sky-400 to-transparent shadow-[0_0_12px_#38bdf8] animate-pulse" />
                  )}

                  <QrCode className="w-16 h-16 text-sky-400/30" />
                </div>

                {/* Viewfinder Status Overlay */}
                <div className="absolute bottom-3 inset-x-4 flex items-center justify-between text-[11px] bg-slate-900/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-800/80 text-slate-300">
                  <span className="flex items-center gap-1.5 font-mono text-emerald-400">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                    OPTICAL RETICLE ACTIVE
                  </span>
                  <span className="text-slate-400">Point at any campus QR placard</span>
                </div>
              </div>

              {/* Quick Preset Selector */}
              <div>
                <label className="block text-slate-400 font-semibold mb-2">
                  Select Institutional QR Badge to Scan:
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {PRESET_FACILITIES.map((f) => (
                    <button
                      key={f.code}
                      onClick={() => setScannedFacility(f)}
                      className={`p-2.5 rounded-xl text-left border transition-all flex items-start gap-2.5 ${
                        scannedFacility?.code === f.code
                          ? "bg-sky-950/60 border-sky-500 shadow-md shadow-sky-500/10 text-white"
                          : "bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700"
                      }`}
                    >
                      <Tag className="w-3.5 h-3.5 text-sky-400 mt-0.5 shrink-0" />
                      <div className="min-w-0">
                        <div className="font-mono font-bold text-sky-300 text-[11px] truncate">{f.code}</div>
                        <div className="font-semibold text-slate-200 text-xs truncate">{f.name}</div>
                        <div className="text-[10px] text-slate-400 truncate">{f.building} • {f.floor}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Decoded Facility Card */}
              {scannedFacility && (
                <div className="p-4 rounded-xl bg-slate-900/90 border border-sky-900/60 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-2.5">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-sky-400 text-xs">{scannedFacility.code}</span>
                        <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 font-bold text-[10px]">
                          Health: {scannedFacility.healthScore}%
                        </span>
                        {scannedFacility.openTickets > 0 ? (
                          <span className="px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 font-bold text-[10px]">
                            {scannedFacility.openTickets} Open Work Order
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px]">
                            Zero Pending Tickets
                          </span>
                        )}
                      </div>
                      <h4 className="font-bold text-white text-sm mt-0.5">{scannedFacility.name}</h4>
                      <p className="text-slate-400 text-[11px]">{scannedFacility.building} — {scannedFacility.floor}</p>
                    </div>

                    <button
                      onClick={() => {
                        onSelectFacilityForGrievance(
                          scannedFacility.code,
                          scannedFacility.category === "HOSTEL" ? "HOSTEL" : "FACILITY"
                        );
                        onClose();
                      }}
                      className="px-3.5 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-white font-semibold flex items-center justify-center gap-1.5 shadow-md shadow-sky-500/20 transition-all shrink-0"
                    >
                      <span>Report Grievance for Location</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div>
                    <span className="text-slate-400 text-[11px] font-semibold block mb-1">
                      Assigned Facility Infrastructure & Hardware:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {scannedFacility.equipment.map((eq, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 rounded-lg bg-slate-800/80 border border-slate-700/80 text-slate-300 text-[10px] font-medium flex items-center gap-1"
                        >
                          <Cpu className="w-3 h-3 text-sky-400" />
                          {eq}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* QR Label Generator for Campus Ops */
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <div>
                    <label className="block text-slate-400 font-semibold mb-1">Facility Code / Anchor Tag</label>
                    <input
                      type="text"
                      value={customTag}
                      onChange={(e) => setCustomTag(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-400 font-semibold mb-1">Facility / Room Name</label>
                    <input
                      type="text"
                      value={customName}
                      onChange={(e) => setCustomName(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-400 font-semibold mb-1">Building & Wing</label>
                    <input
                      type="text"
                      value={customBuilding}
                      onChange={(e) => setCustomBuilding(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-400 font-semibold mb-1">Monitored Assets (Comma Separated)</label>
                    <textarea
                      rows={2}
                      value={customEquipment}
                      onChange={(e) => setCustomEquipment(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500 resize-none"
                    />
                  </div>
                </div>

                {/* Printable Institutional Placard Card */}
                <div className="flex flex-col items-center justify-center p-5 rounded-2xl bg-white text-slate-900 border-2 border-slate-300 shadow-xl space-y-2.5 text-center">
                  <div className="text-[10px] font-bold tracking-wider uppercase text-slate-600">
                    Apex Institute of Technology
                  </div>
                  <div className="text-xs font-black uppercase text-indigo-900">
                    CampusCare Facility Asset Label
                  </div>

                  {/* High-Contrast SVG QR Mockup */}
                  <div className="p-3 bg-white rounded-lg border-2 border-slate-900 shadow-md">
                    <svg className="w-28 h-28" viewBox="0 0 100 100" fill="currentColor">
                      {/* Outer Position Corners */}
                      <rect x="5" y="5" width="25" height="25" fill="#0f172a" />
                      <rect x="9" y="9" width="17" height="17" fill="#ffffff" />
                      <rect x="13" y="13" width="9" height="9" fill="#0f172a" />

                      <rect x="70" y="5" width="25" height="25" fill="#0f172a" />
                      <rect x="74" y="9" width="17" height="17" fill="#ffffff" />
                      <rect x="78" y="13" width="9" height="9" fill="#0f172a" />

                      <rect x="5" y="70" width="25" height="25" fill="#0f172a" />
                      <rect x="9" y="74" width="17" height="17" fill="#ffffff" />
                      <rect x="13" y="78" width="9" height="9" fill="#0f172a" />

                      {/* Random Data Dots */}
                      <rect x="35" y="10" width="5" height="15" fill="#0f172a" />
                      <rect x="45" y="5" width="15" height="5" fill="#0f172a" />
                      <rect x="45" y="20" width="10" height="10" fill="#0f172a" />
                      <rect x="60" y="35" width="15" height="5" fill="#0f172a" />
                      <rect x="10" y="45" width="20" height="8" fill="#0f172a" />
                      <rect x="35" y="45" width="30" height="15" fill="#4338ca" />
                      <rect x="70" y="55" width="20" height="10" fill="#0f172a" />
                      <rect x="40" y="70" width="15" height="20" fill="#0f172a" />
                      <rect x="60" y="75" width="25" height="10" fill="#0f172a" />
                    </svg>
                  </div>

                  <div className="font-mono font-black text-xs text-slate-900 tracking-wider">
                    {customTag}
                  </div>
                  <div className="font-bold text-xs text-slate-800 line-clamp-1">
                    {customName}
                  </div>
                  <div className="text-[10px] text-slate-600 font-medium">
                    Scan with any smartphone or CampusCare portal to dispatch service
                  </div>
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="button"
                  onClick={handlePrintLabel}
                  className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/25 transition-all text-xs"
                >
                  <Printer className="w-4 h-4" />
                  Print Asset Placard Badge
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
