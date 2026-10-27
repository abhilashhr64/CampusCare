"use client";

import React from "react";
import { AlertCircle, ShieldAlert, WifiOff, Inbox, Loader2 } from "lucide-react";

export function LoadingState({ message = "Loading secure records..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center glass-panel rounded-2xl">
      <Loader2 className="w-10 h-10 text-sky-400 animate-spin mb-4" />
      <p className="text-slate-300 font-medium text-sm">{message}</p>
      <span className="text-xs text-slate-500 mt-1">Verifying tenant session & RLS scope</span>
    </div>
  );
}

export function EmptyState({
  title = "No records found",
  description = "No items match your query or assigned cohort scope.",
  actionLabel,
  onAction,
}: {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center glass-panel rounded-2xl border border-dashed border-slate-700/60">
      <div className="w-12 h-12 rounded-xl bg-slate-800/80 flex items-center justify-center text-slate-400 mb-4">
        <Inbox className="w-6 h-6" />
      </div>
      <h4 className="text-slate-200 font-semibold text-base mb-1">{title}</h4>
      <p className="text-slate-400 text-sm max-w-sm mb-4">{description}</p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 text-xs font-semibold rounded-lg bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-500/30 transition-colors"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}

export function ErrorState({
  title = "Action Failed",
  message,
  onRetry,
}: {
  title?: string;
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center glass-panel rounded-2xl border border-rose-500/30 bg-rose-950/20">
      <div className="w-12 h-12 rounded-xl bg-rose-500/10 flex items-center justify-center text-rose-400 mb-3">
        <AlertCircle className="w-6 h-6" />
      </div>
      <h4 className="text-rose-200 font-semibold text-base mb-1">{title}</h4>
      <p className="text-rose-300/80 text-xs max-w-md mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 text-xs font-semibold rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 transition-colors"
        >
          Retry Request
        </button>
      )}
    </div>
  );
}

export function PermissionDeniedState({
  reason = "DENY_INSUFFICIENT_ROLE",
  description = "Server-side policy denied access. Verified email alone never grants elevated privileges (Rule NR-3, NR-5).",
}: {
  reason?: string;
  description?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center glass-panel rounded-2xl border border-amber-500/30 bg-amber-950/20">
      <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400 mb-3">
        <ShieldAlert className="w-6 h-6" />
      </div>
      <h4 className="text-amber-200 font-semibold text-base mb-1">Authorization Denied</h4>
      <code className="text-xs font-mono text-amber-400/90 bg-amber-950/40 px-2 py-0.5 rounded mb-2">
        {reason}
      </code>
      <p className="text-slate-400 text-xs max-w-md">{description}</p>
    </div>
  );
}

export function OfflineIndicator({ isOnline }: { isOnline: boolean }) {
  if (isOnline) {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        Live Synced
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
      <WifiOff className="w-3 h-3 text-amber-400" />
      Offline Drafts (IndexedDB)
    </div>
  );
}
