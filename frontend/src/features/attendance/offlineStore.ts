import Dexie, { type EntityTable } from "dexie";

export interface AttendanceOutboxOp {
  op_id: string; // UUID (idempotency key)
  session_id: string;
  type: "MARK_SESSION" | "UPDATE_RECORD" | "BULK_MARK";
  payload: {
    class_section_id: string;
    student_records: Array<{
      student_id: string;
      roll_number: string;
      status: "PRESENT" | "ABSENT" | "EXCUSED";
    }>;
  };
  base_version: number;
  device_id: string;
  created_at: string;
  sync_status: "pending" | "synced" | "conflict" | "failed";
  conflict_details?: {
    server_version: number;
    server_records: any[];
  };
}

class CampusCareOfflineDB extends Dexie {
  attendance_outbox!: EntityTable<AttendanceOutboxOp, "op_id">;

  constructor() {
    super("CampusCareAttendanceDB");
    this.version(1).stores({
      attendance_outbox: "op_id, session_id, sync_status, created_at",
    });
  }
}

export const offlineDb = new CampusCareOfflineDB();

// Unique persistent device identifier
export function getOrCreateDeviceId(): string {
  if (typeof window === "undefined") return "server-ssr";
  let deviceId = localStorage.getItem("campuscare_device_id");
  if (!deviceId) {
    deviceId = "dev-" + Math.random().toString(36).substring(2, 12);
    localStorage.setItem("campuscare_device_id", deviceId);
  }
  return deviceId;
}

export async function queueAttendanceOperation(
  sessionId: string,
  classSectionId: string,
  records: Array<{ student_id: string; roll_number: string; status: "PRESENT" | "ABSENT" | "EXCUSED" }>,
  baseVersion: number
): Promise<AttendanceOutboxOp> {
  const op: AttendanceOutboxOp = {
    op_id: crypto.randomUUID ? crypto.randomUUID() : "op-" + Date.now() + "-" + Math.random().toString(36).substring(2, 7),
    session_id: sessionId,
    type: "MARK_SESSION",
    payload: {
      class_section_id: classSectionId,
      student_records: records,
    },
    base_version: baseVersion,
    device_id: getOrCreateDeviceId(),
    created_at: new Date().toISOString(),
    sync_status: "pending",
  };

  await offlineDb.attendance_outbox.put(op);
  return op;
}

export async function getPendingAttendanceOps(): Promise<AttendanceOutboxOp[]> {
  return await offlineDb.attendance_outbox.where("sync_status").equals("pending").toArray();
}

export async function markOpSynced(op_id: string): Promise<void> {
  await offlineDb.attendance_outbox.update(op_id, { sync_status: "synced" });
}

export async function markOpConflict(
  op_id: string,
  server_version: number,
  server_records: any[]
): Promise<void> {
  await offlineDb.attendance_outbox.update(op_id, {
    sync_status: "conflict",
    conflict_details: { server_version, server_records },
  });
}
