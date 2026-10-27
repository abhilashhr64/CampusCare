"use client";

import React, { useState } from "react";
import {
  Building2,
  MapPin,
  Wifi,
  Zap,
  Thermometer,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  QrCode,
  ArrowRight,
  Sparkles,
  Layers,
  Search,
} from "lucide-react";

export interface CampusBuilding {
  id: string;
  name: string;
  code: string;
  type: "ACADEMIC" | "LABORATORY" | "LIBRARY" | "RESIDENTIAL" | "ADMINISTRATION";
  healthScore: number;
  floorsCount: number;
  activeTickets: number;
  wifiLoad: string;
  powerStatus: "NORMAL" | "BACKUP" | "MAINTENANCE";
  tempC: number;
  floors: Array<{
    floorNumber: number;
    name: string;
    rooms: Array<{
      tag: string;
      name: string;
      status: "OPERATIONAL" | "WARNING" | "ATTENTION_REQUIRED";
      issuesCount: number;
      primaryEquipment: string;
    }>;
  }>;
}

export const CAMPUS_BUILDINGS: CampusBuilding[] = [
  {
    id: "b-turing",
    name: "Alan Turing Advanced Computing Center",
    code: "TURING",
    type: "LABORATORY",
    healthScore: 94,
    floorsCount: 4,
    activeTickets: 1,
    wifiLoad: "64% Capacity (Cisco Wi-Fi 6)",
    powerStatus: "NORMAL",
    tempC: 21.5,
    floors: [
      {
        floorNumber: 4,
        name: "4th Floor — AI Research & High-Performance Compute",
        rooms: [
          {
            tag: "QR:LAB-4-401",
            name: "CSE GPU Lab 401",
            status: "WARNING",
            issuesCount: 1,
            primaryEquipment: "4x NVIDIA RTX A6000 & 4K Laser Projector",
          },
          {
            tag: "QR:TURING-402",
            name: "Computer Vision Cluster 402",
            status: "OPERATIONAL",
            issuesCount: 0,
            primaryEquipment: "GigE Machine Vision Cameras",
          },
          {
            tag: "QR:TURING-403",
            name: "Cloud Systems Sandbox 403",
            status: "OPERATIONAL",
            issuesCount: 0,
            primaryEquipment: "Dedicated 10Gbps Uplink Switch",
          },
        ],
      },
      {
        floorNumber: 3,
        name: "3rd Floor — Software Engineering & Systems Labs",
        rooms: [
          {
            tag: "QR:TURING-301",
            name: "Operating Systems Lab 301",
            status: "OPERATIONAL",
            issuesCount: 0,
            primaryEquipment: "60x Linux Workstations",
          },
          {
            tag: "QR:TURING-302",
            name: "Networks & Cybersecurity Lab 302",
            status: "OPERATIONAL",
            issuesCount: 0,
            primaryEquipment: "Modular Packet Sniffing Racks",
          },
        ],
      },
    ],
  },
  {
    id: "b-kalam",
    name: "Dr. APJ Abdul Kalam Central Library",
    code: "LIBRARY",
    type: "LIBRARY",
    healthScore: 99,
    floorsCount: 3,
    activeTickets: 0,
    wifiLoad: "48% Capacity (Silent Zone Mesh)",
    powerStatus: "NORMAL",
    tempC: 22.0,
    floors: [
      {
        floorNumber: 2,
        name: "2nd Floor — Silent Research Pods & Digital Commons",
        rooms: [
          {
            tag: "QR:LIBRARY-2F",
            name: "Digital Commons Pod 12",
            status: "OPERATIONAL",
            issuesCount: 0,
            primaryEquipment: "Laser Multi-Function Print Station",
          },
          {
            tag: "QR:LIBRARY-204",
            name: "Graduate Thesis Study Suite",
            status: "OPERATIONAL",
            issuesCount: 0,
            primaryEquipment: "Acoustic Noise-Canceling Glazing",
          },
        ],
      },
    ],
  },
  {
    id: "b-raman",
    name: "Sir C.V. Raman Academic Complex",
    code: "RAMAN",
    type: "ACADEMIC",
    healthScore: 97,
    floorsCount: 5,
    activeTickets: 0,
    wifiLoad: "78% Capacity (Lecture Hall APs)",
    powerStatus: "NORMAL",
    tempC: 23.2,
    floors: [
      {
        floorNumber: 1,
        name: "1st Floor — Foundation Engineering Halls",
        rooms: [
          {
            tag: "QR:RAMAN-101",
            name: "Smart Lecture Theater 101",
            status: "OPERATIONAL",
            issuesCount: 0,
            primaryEquipment: "Interactive Touch Podium & Dual Displays",
          },
          {
            tag: "QR:RAMAN-102",
            name: "Colloquium Hall 102",
            status: "OPERATIONAL",
            issuesCount: 0,
            primaryEquipment: "Ceiling Array Microphones",
          },
        ],
      },
    ],
  },
  {
    id: "b-hostel",
    name: "North Student Residential Complex (Block B)",
    code: "HOSTEL",
    type: "RESIDENTIAL",
    healthScore: 84,
    floorsCount: 4,
    activeTickets: 1,
    wifiLoad: "88% Peak Load",
    powerStatus: "NORMAL",
    tempC: 24.5,
    floors: [
      {
        floorNumber: 2,
        name: "2nd Floor — North Wing Living Quarters",
        rooms: [
          {
            tag: "QR:HOSTEL-BLOCK-B",
            name: "Wing B Utility & Geyser Bay",
            status: "WARNING",
            issuesCount: 1,
            primaryEquipment: "Commercial Heat-Pump Geyser",
          },
          {
            tag: "QR:HOSTEL-B-STUDY",
            name: "Floor 2 Common Study Lounge",
            status: "OPERATIONAL",
            issuesCount: 0,
            primaryEquipment: "High-Capacity Air Purifier",
          },
        ],
      },
    ],
  },
];

interface CampusFacilityMapProps {
  onOpenGrievanceWithTag: (locationTag: string, category: string) => void;
  onOpenQrSuite: () => void;
}

export function CampusFacilityMap({
  onOpenGrievanceWithTag,
  onOpenQrSuite,
}: CampusFacilityMapProps) {
  const [selectedBuildingId, setSelectedBuildingId] = useState<string>("b-turing");
  const [selectedFloorNumber, setSelectedFloorNumber] = useState<number>(4);
  const [searchQuery, setSearchQuery] = useState<string>("");

  const currentBuilding =
    CAMPUS_BUILDINGS.find((b) => b.id === selectedBuildingId) || CAMPUS_BUILDINGS[0];

  const currentFloor =
    currentBuilding.floors.find((f) => f.floorNumber === selectedFloorNumber) ||
    currentBuilding.floors[0];

  return (
    <div className="space-y-6">
      {/* Overview Banner */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Building2 className="w-5 h-5 text-sky-400" />
                Campus Facilities & Real-Time Infrastructure Map
              </h3>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                Live Telemetry Active
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Visual floor breakdown, environmental sensors, Wi-Fi load, and instant QR-anchored service reporting
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onOpenQrSuite}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white shadow-lg shadow-sky-500/20 flex items-center gap-2 transition-all shrink-0"
            >
              <QrCode className="w-4 h-4" />
              <span>Launch QR Scanner & Placards</span>
            </button>
          </div>
        </div>

        {/* Building Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-6">
          {CAMPUS_BUILDINGS.map((b) => (
            <button
              key={b.id}
              onClick={() => {
                setSelectedBuildingId(b.id);
                setSelectedFloorNumber(b.floors[0]?.floorNumber || 1);
              }}
              className={`p-4 rounded-xl text-left border transition-all relative overflow-hidden ${
                selectedBuildingId === b.id
                  ? "bg-slate-900 border-sky-500 shadow-lg shadow-sky-500/10 ring-1 ring-sky-500/30"
                  : "bg-slate-900/60 border-slate-800/80 hover:border-slate-700 text-slate-300"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                  {b.code}
                </span>
                <span
                  className={`text-[10px] font-bold font-mono px-2 py-0.5 rounded ${
                    b.healthScore >= 95
                      ? "bg-emerald-500/15 text-emerald-300"
                      : "bg-amber-500/15 text-amber-300"
                  }`}
                >
                  {b.healthScore}% Health
                </span>
              </div>

              <h4 className="font-bold text-white text-xs mt-2 line-clamp-1">{b.name}</h4>

              <div className="flex items-center gap-3 mt-3 text-[10px] text-slate-400">
                <span className="flex items-center gap-1">
                  <Thermometer className="w-3 h-3 text-sky-400" />
                  {b.tempC}°C
                </span>
                <span className="flex items-center gap-1">
                  <Wifi className="w-3 h-3 text-indigo-400" />
                  Wi-Fi 6
                </span>
                {b.activeTickets > 0 ? (
                  <span className="text-amber-400 font-bold ml-auto">
                    {b.activeTickets} Ticket
                  </span>
                ) : (
                  <span className="text-emerald-400 font-medium ml-auto">All Normal</span>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Selected Building Floor Inspector */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-sky-400">{currentBuilding.code}</span>
              <h3 className="text-base font-bold text-white">{currentBuilding.name}</h3>
            </div>
            <div className="flex flex-wrap items-center gap-4 mt-1 text-xs text-slate-400">
              <span className="flex items-center gap-1">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                Power Grid: <strong className="text-slate-200">{currentBuilding.powerStatus}</strong>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Wifi className="w-3.5 h-3.5 text-sky-400" />
                Network: <strong className="text-slate-200">{currentBuilding.wifiLoad}</strong>
              </span>
            </div>
          </div>

          {/* Floor Level Tabs */}
          <div className="flex items-center gap-1.5 bg-slate-900 p-1 rounded-xl border border-slate-800 shrink-0">
            {currentBuilding.floors.map((fl) => (
              <button
                key={fl.floorNumber}
                onClick={() => setSelectedFloorNumber(fl.floorNumber)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  selectedFloorNumber === fl.floorNumber
                    ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Floor {fl.floorNumber}
              </button>
            ))}
          </div>
        </div>

        {/* Rooms & Facilities on Current Floor */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-semibold text-slate-300">
              {currentFloor?.name || "Floor Facilities"}
            </span>
            <span>{currentFloor?.rooms.length || 0} Monitored Facilities</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {currentFloor?.rooms.map((room) => (
              <div
                key={room.tag}
                className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/90 flex flex-col justify-between hover:border-slate-700 transition-colors space-y-3"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] font-bold text-sky-400 flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      {room.tag}
                    </span>
                    <span
                      className={`text-[9px] font-bold px-2 py-0.5 rounded uppercase ${
                        room.status === "OPERATIONAL"
                          ? "bg-emerald-500/15 text-emerald-300"
                          : "bg-amber-500/15 text-amber-300"
                      }`}
                    >
                      {room.status}
                    </span>
                  </div>

                  <h4 className="font-bold text-white text-xs mt-1.5">{room.name}</h4>
                  <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                    {room.primaryEquipment}
                  </p>
                </div>

                <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between gap-2">
                  <span className="text-[10px] text-slate-400">
                    {room.issuesCount > 0 ? (
                      <span className="text-amber-400 font-semibold">{room.issuesCount} Active Ticket</span>
                    ) : (
                      <span className="text-emerald-400">Zero Open Issues</span>
                    )}
                  </span>

                  <button
                    onClick={() =>
                      onOpenGrievanceWithTag(
                        room.tag,
                        currentBuilding.type === "RESIDENTIAL" ? "HOSTEL" : "FACILITY"
                      )
                    }
                    className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-800 hover:bg-slate-750 text-sky-400 hover:text-sky-300 border border-slate-700/80 transition-colors flex items-center gap-1"
                  >
                    <span>Report Issue</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
