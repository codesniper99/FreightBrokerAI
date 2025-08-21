// src/assets/NegotiationChat.tsx
import { useMemo, useState, useEffect, type JSX, useRef } from "react";
import type { Load } from "./LoadCard";

export type NegotiateResponse = {
  ai_negotiated_price: number;
  ai_negotiation_reason: string;
};

function toNum(v: number | string | null | undefined): number | undefined {
  if (v === null || v === undefined) return undefined;
  const n = typeof v === "string" ? parseFloat(v) : v;
  return Number.isFinite(n) ? n : undefined;
}

export default function NegotiationChat({
  token,
  defaultLoad,
  endpoint = "/negotiate/start",
}: {
  token: string;
  defaultLoad?: Load | null;
  endpoint?: string;
}) {
  // seed fields from the first load (if provided)
  // console.log("load is " + defaultLoad)

  const seedPrice = useMemo(() => toNum(defaultLoad?.loadboard_rate), [defaultLoad]);
  const [price, setPrice] = useState<number | undefined>(seedPrice);
  const [miles, setMiles] = useState<number | undefined>(defaultLoad?.miles ?? undefined);
  const [equipment, setEquipment] = useState<string>(defaultLoad?.equipment_type ?? "");
  const [origin, setOrigin] = useState<string>(defaultLoad?.origin ?? "");
  const [destination, setDestination] = useState<string>(defaultLoad?.destination ?? "");
  const [curRound, setRound] = useState(0);
  const [userMsg, setUserMsg] = useState<string>("Can you do a better price?");
  const [userRequested, setUserRequested] = useState<number | undefined>(undefined);
  const [maxRounds, _setMaxRounds] = useState<number>(3);
  const [pollForNegotiationResult, setPollForNegotiationResult] = useState(false);
  const [sending, setSending] = useState(false);
  const [history, setHistory] = useState<Array<{ role: "user" | "assistant"; text: string }>>([]);
  const [_lastResp, setLastResp] = useState<NegotiateResponse | null>(null);
  const [sessionId, setSessionId] = useState<string>(() => {
    // generate only once when component mounts
    return crypto.randomUUID();
  });
  const msgRef = useRef<HTMLInputElement>(null);
  const priceRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (defaultLoad) {
      setPrice(toNum(defaultLoad.loadboard_rate));
      setMiles(defaultLoad.miles ?? undefined);
      setEquipment(defaultLoad.equipment_type ?? "");
      setOrigin(defaultLoad.origin ?? "");
      setDestination(defaultLoad.destination ?? "");
    }
  }, [defaultLoad]);

  useEffect(() => {
    if (defaultLoad) {
      // Reset state
      setHistory([]);
      setLastResp(null);
      setRound(0);
      setUserMsg("Can you do a better price?");
      setUserRequested(undefined);
      setPollForNegotiationResult(false);

      // New session ID for fresh negotiation
      setSessionId(crypto.randomUUID());

      // Sync new load details
      setPrice(toNum(defaultLoad.loadboard_rate));
      setMiles(defaultLoad.miles ?? undefined);
      setEquipment(defaultLoad.equipment_type ?? "");
      setOrigin(defaultLoad.origin ?? "");
      setDestination(defaultLoad.destination ?? "");
    }
  }, [defaultLoad]);

  // Kick off negotiation
  const send = async () => {
    setSending(true);
    setPollForNegotiationResult(true);
    setRound(curRound + 1);

    // append user message locally
    setHistory((h) => [...h, { role: "user", text: userMsg }]);

    try {
      const payload = {
        session_id: sessionId,
        load: {
          load_id: defaultLoad?.load_id,
          price,
          miles,
          equipment_type: equipment || undefined,
          origin: origin || undefined,
          destination: destination || undefined,
        },
        user_message: msgRef.current?.value ?? userMsg,
        user_requested_price: priceRef.current ? Number(priceRef.current.value) : userRequested,
        cur_round: curRound,
        max_rounds: Math.min(3, Math.max(1, maxRounds)),
      };

      const r = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`, // should later fix so it comes from backend
        },
        body: JSON.stringify(payload),
      });
      console.log(JSON.stringify(payload));

      const data = await r.json();
      console.log("data" + JSON.stringify(data));
      if (data.session_id) {
        setSessionId(data.session_id);
      } else {
        setHistory((h) => [...h, { role: "assistant", text: "No session_id returned." }]);
      }
    } catch (e: any) {
      setHistory((h) => [
        ...h,
        { role: "assistant", text: `Failed to start negotiation: ${e?.message ?? String(e)}` },
      ]);
    } finally {
      setSending(false);
    }
  };

  // Poll for result
  useEffect(() => {
    if (!sessionId) return;

    const interval = setInterval(async () => {
      try {
        const r = await fetch(`/negotiate/result/${sessionId}`);
        const data = await r.json();

        console.log("result is " + JSON.stringify(data, null, 2));
        if (pollForNegotiationResult) {
          if (data.ok && data.status === "complete") {
            if (data.result) {
              const result: NegotiateResponse = data.result;
              setLastResp(result);
              setHistory((h) => [
                ...h,
                {
                  role: "assistant",
                  text: `AI offers $${result.ai_negotiated_price}. Reason: ${result.ai_negotiation_reason}`,
                },
              ]);
            }

            if (data.status !== "pending") {
              setPollForNegotiationResult(false);
              clearInterval(interval); // stop polling if complete
            }
          }
        }

      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [pollForNegotiationResult]);

  const field = (label: string, node: JSX.Element) => (
    <label style={{ display: "grid", gap: 6, fontSize: 13 }}>
      <span style={{ color: "#9ca3af" }}>{label}</span>
      {node}
    </label>
  );

  return (
    <div
      style={{
        marginTop: 18,
        background: "#111827",
        border: "1px solid #1f2937",
        borderRadius: 12,
        padding: 14,
        color: "#e5e7eb",
        display: "flex",
        flexDirection: "column",
        height: "80vh", // optional: fixed height for scroll
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: 10 }}>
        Chat to Negotiate and Accept Load!
      </div>

      {/* Transcript */}
      {/* Transcript */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 8,
          paddingBottom: 10,
        }}
      >
        {history.map((m, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              justifyContent: m.role === "user" ? "flex-end" : "flex-start",
            }}
          >
            <div
              style={{
                background: m.role === "user" ? "#2563eb" : "#374151",
                color: "white",
                padding: "10px 14px",
                borderRadius: 16,
                maxWidth: "70%",
                wordWrap: "break-word",
                fontSize: 14,
                lineHeight: 1.4,
              }}
            >
              <b style={{ fontSize: 12, opacity: 0.8 }}>
                {m.role === "user" ? "You" : "AI"}
              </b>
              <div>{m.text}</div>
            </div>
          </div>
        ))}

        {/* Spinner bubble while waiting */}
        {pollForNegotiationResult && (
          <div
            style={{
              display: "flex",
              justifyContent: "flex-start",
            }}
          >
            <div
              style={{
                background: "#374151",
                color: "white",
                padding: "10px 14px",
                borderRadius: 16,
                maxWidth: "70%",
                fontSize: 14,
                lineHeight: 1.4,
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <b style={{ fontSize: 12, opacity: 0.8 }}>AI</b>
              <div className="spinner" style={{ display: "flex", gap: 4 }}>
                <div
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: "white",
                    animation: "blink 1.4s infinite both",
                  }}
                />
                <div
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: "white",
                    animation: "blink 1.4s infinite both",
                    animationDelay: "0.2s",
                  }}
                />
                <div
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: "white",
                    animation: "blink 1.4s infinite both",
                    animationDelay: "0.4s",
                  }}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Inputs at bottom */}
      <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
        {field(
          "Enter a message to talk to AI",
          <input
            ref={msgRef}
            value={userMsg}
            onChange={(e) => setUserMsg(e.target.value)}
            placeholder="e.g., Can you do $800?"
            style={{
              padding: 10,
              borderRadius: 10,
              border: "1px solid #374151",
              background: "#0b1220",
              color: "white",
            }}
          />
        )}

        {field(
          "Your Proposed price ($)",
          <input
            ref={priceRef}
            type="number"
            value={userRequested ?? ""}
            onChange={(e) =>
              setUserRequested(e.target.value ? Number(e.target.value) : undefined)
            }
            style={{
              padding: 8,
              borderRadius: 8,
              border: "1px solid #374151",
              background: "#0b1220",
              color: "white",
            }}
          />
        )}

        {/* other fields like Origin, Destination, Equipment, Miles, Current price */}
        {/* ... */}

        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>

          <button onClick={send} disabled={sending} style={{ padding: "8px 14px" }}>
            {sending ? "Negotiating…" : "Send"}
          </button>

          {/* New Accept button */}
          <button
            style={{
              backgroundColor: "green",
              color: "white",
              padding: "0 12px",
              border: "none",
              borderRadius: 6,
              cursor: "pointer",
            }}
            onClick={() => {
              alert("Accepted! Transferring to sales representative…");
              // later you can call fetch("/handoff", { method: "POST", ... })
            }}
          >
            Accept Offer and talk to sales Rep! 
          </button>
        </div>

      </div>
    </div>
  );
}
