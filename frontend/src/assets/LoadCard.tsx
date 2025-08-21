// src/components/LoadCard.tsx
export type Dimensions = {
  unit?: string;
  width?: number;
  height?: number;
  length?: number;
};

export type Load = {
  load_id: string;
  origin: string;
  destination: string;
  pickup_datetime?: string;
  delivery_datetime?: string;
  equipment_type?: string;
  loadboard_rate?: number | string | null;
  notes?: string | null;
  weight?: number | null;
  commodity_type?: string | null;
  num_of_pieces?: number | null;
  miles?: number | null;
  dimensions?: Dimensions | null;
};

const fmtMoney = (v: number | string | null | undefined) => {
  if (v === null || v === undefined) return "—";
  const n = typeof v === "string" ? parseFloat(v) : v;
  if (Number.isFinite(n)) {
    return new Intl.NumberFormat(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n as number);
  }
  return String(v);
};

const fmtDateTime = (iso?: string) => {
  if (!iso) return "—";
  const d = new Date(iso);
  return isNaN(d.valueOf()) ? iso : d.toLocaleString();
};

export default function LoadCard({ load }: { load: Load }) {
  return (
    <div
      style={{
        border: "1px solid #1f2937",
        background: "#111827",
        color: "#e5e7eb",
        borderRadius: 12,
        padding: 12,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
        <div style={{ fontWeight: 700 }}>
          {load.origin} → {load.destination}
        </div>
        <div>{fmtMoney(load.loadboard_rate)}</div>
      </div>

      <div style={{ marginTop: 6, fontSize: 13, color: "#9ca3af" }}>
        {load.equipment_type || "—"} · {load.weight ?? "—"} kg · {load.miles ?? "—"} mi
      </div>

      <div style={{ marginTop: 6, fontSize: 12, color: "#9ca3af" }}>
        PU: {fmtDateTime(load.pickup_datetime)} · DEL: {fmtDateTime(load.delivery_datetime)}
      </div>

      {load.commodity_type && (
        <div style={{ marginTop: 6, fontSize: 12, color: "#9ca3af" }}>
          Commodity: {load.commodity_type}
        </div>
      )}
      {load.notes && (
        <div style={{ marginTop: 6, fontSize: 12, color: "#9ca3af" }}>
          Notes: {load.notes}
        </div>
      )}
    </div>
  );
}
