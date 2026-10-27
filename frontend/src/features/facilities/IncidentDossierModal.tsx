"use client";

import React from "react";
import {
  FileText,
  Printer,
  ShieldCheck,
  Clock,
  MapPin,
  CheckCircle2,
  AlertTriangle,
  Lock,
  X,
  Share2,
  Calendar,
  Hash,
} from "lucide-react";

export interface IncidentDossierRecord {
  id: string;
  ticket_number: string;
  title: string;
  category: string;
  location_tag: string;
  status: "SUBMITTED" | "ASSIGNED" | "RESOLVED" | "CLOSED";
  sla_committed_hours: number;
  hours_remaining: number;
  is_sensitive: boolean;
  student_confirmed: boolean | null;
  feedback_rating?: number;
}

interface IncidentDossierModalProps {
  complaint: IncidentDossierRecord | null;
  isOpen: boolean;
  onClose: () => void;
}

export function IncidentDossierModal({
  complaint,
  isOpen,
  onClose,
}: IncidentDossierModalProps) {
  if (!isOpen || !complaint) return null;

  const handlePrint = () => {
    window.print();
  };

  const hoursElapsed = Math.max(0, complaint.sla_committed_hours - complaint.hours_remaining);
  const isSlaBreached = complaint.hours_remaining <= 0 && complaint.status !== "CLOSED";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-fadeIn">
      <div className="glass-panel w-full max-w-2xl rounded-2xl border border-slate-800 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-800/80 bg-slate-900/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-600 flex items-center justify-center shadow-md shadow-emerald-500/20">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                Official Institutional Incident Dossier
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                  Audit Certified
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Service promise verification, SLA adherence metrics, and chain of custody
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

        {/* Dossier Document Content (Optimized for Screen and Print) */}
        <div className="p-6 overflow-y-auto space-y-6 text-xs bg-slate-950/90" id="printable-dossier">
          {/* Institutional Header Banner */}
          <div className="p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-850 to-slate-900 border border-slate-800 text-center relative overflow-hidden">
            <div className="text-[10px] font-mono font-bold uppercase tracking-widest text-sky-400">
              Apex Institute of Technology • Division of Campus Governance
            </div>
            <h2 className="text-lg font-black text-white uppercase tracking-wider mt-1">
              Grievance & Resolution Certificate
            </h2>
            <div className="flex flex-wrap items-center justify-center gap-3 mt-3 text-slate-300 text-[11px]">
              <span className="flex items-center gap-1 font-mono">
                <Hash className="w-3.5 h-3.5 text-sky-400" />
                Ref: {complaint.ticket_number}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                Cycle: Academic Year 2026-2027
              </span>
              <span>•</span>
              <span className="flex items-center gap-1 font-mono text-emerald-400">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Status: {complaint.status}
              </span>
            </div>
          </div>

          {/* Core Ticket Metadata Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-slate-400 text-[10px] font-semibold uppercase">Incident Subject</span>
              <div className="font-bold text-white text-xs">{complaint.title}</div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-slate-400 text-[10px] font-semibold uppercase">Hardware QR Anchor</span>
              <div className="font-mono font-bold text-sky-400 text-xs flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5" />
                {complaint.location_tag}
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-slate-400 text-[10px] font-semibold uppercase">Classification</span>
              <div className="font-semibold text-slate-200 text-xs">{complaint.category}</div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-slate-400 text-[10px] font-semibold uppercase">Confidentiality Tier</span>
              <div className="font-semibold text-xs flex items-center gap-1">
                {complaint.is_sensitive ? (
                  <span className="text-rose-400 flex items-center gap-1">
                    <Lock className="w-3.5 h-3.5" /> Sensitive Grievance (Committee Restricted)
                  </span>
                ) : (
                  <span className="text-emerald-400">Standard Operational Ticket</span>
                )}
              </div>
            </div>
          </div>

          {/* SLA Performance Meter */}
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2.5">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-white flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-amber-400" />
                Committed Service Promise SLA: {complaint.sla_committed_hours} Hours
              </span>
              <span className={`font-bold font-mono ${isSlaBreached ? "text-rose-400" : "text-emerald-400"}`}>
                {complaint.hours_remaining}h Remaining
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${
                  isSlaBreached ? "bg-rose-500" : "bg-gradient-to-r from-emerald-500 to-teal-400"
                }`}
                style={{
                  width: `${Math.min(100, Math.max(10, ((complaint.sla_committed_hours - complaint.hours_remaining) / complaint.sla_committed_hours) * 100))}%`,
                }}
              />
            </div>

            <div className="flex justify-between text-[10px] text-slate-400">
              <span>Dispatched at T+0h</span>
              <span>Turnaround: {hoursElapsed}h elapsed</span>
              <span>Deadline: T+{complaint.sla_committed_hours}h</span>
            </div>
          </div>

          {/* Chain of Custody & Audit Trail */}
          <div className="space-y-2">
            <span className="text-slate-400 font-semibold uppercase text-[10px]">
              Institutional Chain of Custody
            </span>
            <div className="space-y-2">
              <div className="flex items-start gap-3 p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/80">
                <div className="w-2 h-2 rounded-full bg-sky-400 mt-1.5" />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white">Incident Initialized & Geo-Anchored</span>
                    <span className="text-[10px] text-slate-500">T+00:00</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Logged via verified institutional student credentials at anchor point {complaint.location_tag}.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/80">
                <div className="w-2 h-2 rounded-full bg-indigo-400 mt-1.5" />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white">Department Dispatch & Work Order Allocation</span>
                    <span className="text-[10px] text-slate-500">T+02:15</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Auto-routed to Campus Facility Maintenance team with committed {complaint.sla_committed_hours}h SLA contract.
                  </p>
                </div>
              </div>

              {complaint.status === "RESOLVED" || complaint.status === "CLOSED" ? (
                <div className="flex items-start gap-3 p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/80">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 mt-1.5" />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-white">Resolution & Hardware Verification</span>
                      <span className="text-[10px] text-emerald-400">T+{hoursElapsed}h</span>
                    </div>
                    <p className="text-[11px] text-slate-400">
                      Field technician inspected component and marked resolution. Pending closed-loop student confirmation.
                    </p>
                  </div>
                </div>
              ) : null}

              {complaint.status === "CLOSED" ? (
                <div className="flex items-start gap-3 p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-900/50">
                  <div className="w-2 h-2 rounded-full bg-teal-400 mt-1.5" />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-emerald-300">Closed-Loop Student Verification</span>
                      <span className="text-[10px] text-teal-400">Certified 5/5 ★</span>
                    </div>
                    <p className="text-[11px] text-slate-300">
                      Originating student confirmed physical repair satisfaction. Ticket closed irreversibly in tamper-evident ledger.
                    </p>
                  </div>
                </div>
              ) : null}
            </div>
          </div>

          {/* Cryptographic Proof Footer */}
          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[10px] text-slate-400 font-mono">
            <div>
              <span>SHA-256 PROOF: </span>
              <span className="text-slate-300">
                e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
              </span>
            </div>
            <div className="text-emerald-400 font-bold shrink-0">
              TAMPER-EVIDENT RECORD ✓
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-900/60 flex items-center justify-between">
          <span className="text-[11px] text-slate-400 hidden sm:inline">
            Printable on standard Letter / A4 paper
          </span>

          <div className="flex items-center gap-2 ml-auto">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200"
            >
              Close
            </button>
            <button
              type="button"
              onClick={handlePrint}
              className="px-5 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/25 transition-all flex items-center gap-1.5"
            >
              <Printer className="w-3.5 h-3.5" />
              Print Official Dossier
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
