import { useState, useRef, useEffect } from "react";
import type { Load } from "./assets/LoadCard";
import LoadCard from "./assets/LoadCard";
import NegotiationChat from "./assets/NegotiationChat";
import './index.css'

type WebhookResponse = {
  ok: boolean;
  echo?: Record<string, unknown>;
  suggested_loads: Load[];
};

type VerifyResponse = {
  mc: string;
  legal_name?: string;
  dba_name?: string;
  status?: string;
  eligible?: boolean;
  city?: string;
  state?: string;
};

type StartCleanResponse = {
  ok: boolean;
  job_id: string;
};

type ResultResponse = {
  ok: boolean;
  status: "pending" | "done" | "error";
  suggested_loads?: Load[];
  echo?: Record<string, unknown>;
};

const seedResp: WebhookResponse = {
  ok: true,
  echo: { message: "{\"origin\":\"\",\"rate_min\":300,\"limit\":5}" },
  suggested_loads: [],
};

export default function App() {
  const [step, setStep] = useState(0); // 0=MC, 1=Token, 2=Message, 3=Loads, 4=Negotiation
  const [token, _setToken] = useState("shared_Secret_key");
  const [message, setMessage] = useState("need load for 2kg");
  const [selectedLoad, setSelectedLoad] = useState<Load | null>(null);

  const [mc_key, setMCKey] = useState("");
  const [sending, setSending] = useState(false);
  const [verifying, setVerifying] = useState(false);

  const [resp, setResp] = useState<WebhookResponse>(seedResp);
  const [verifyResp, setVerifyResp] = useState<VerifyResponse | null>(null);

  // polling control
  const [_jobId, setJobId] = useState<string | null>(null);
  const [loadingLoads, setLoadingLoads] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);


  // refs for scroll
  const tokenRef = useRef<HTMLDivElement>(null);
  const messageRef = useRef<HTMLDivElement>(null);
  const loadsRef = useRef<HTMLDivElement>(null);
  const negotiationRef = useRef<HTMLDivElement>(null);

  const scrollTo = (ref: React.RefObject<HTMLDivElement | null>) => {
    ref.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const verify = async () => {
    setVerifying(true);
    setVerifyResp(null);
    try {
      const r = await fetch(`/mc_key/${encodeURIComponent(mc_key)}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });
      const data: VerifyResponse = await r.json();
      setVerifyResp(data);
      setStep(1);
      setTimeout(() => scrollTo(tokenRef), 300);
    } finally {
      setVerifying(false);
    }
  };

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const pollResult = (id: string) => {
    stopPolling(); // clear any previous pollers
    pollRef.current = setInterval(async () => {
      try {
        const r = await fetch(`/result/${id}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data: ResultResponse = await r.json();

        if (data.status === "done") {
          stopPolling();
          setResp({
            ok: true,
            echo: data.echo,
            suggested_loads: data.suggested_loads ?? [],
          });
          setLoadingLoads(false);
        }

        if (data.status === "error") {
          stopPolling();
          setLoadingLoads(false);
          alert("Error processing request");
        }
      } catch (e) {
        stopPolling();
        setLoadingLoads(false);
        alert("Polling error");
      }
    }, 2000); // poll every 2 seconds
  };

  const send = async () => {
    setSending(true);
    setLoadingLoads(true);
    setResp((prev) => ({ ...prev, suggested_loads: [] })); // clear old loads
    setSelectedLoad(null);
    try {
      let payload: unknown;
      try {
        payload = JSON.parse(message);
      } catch {
        payload = { user_message: message }; // match /start_clean backend
      }

      const r = await fetch("/start_clean", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      const data: StartCleanResponse = await r.json();

      if (data.ok && data.job_id) {
        setJobId(data.job_id);
        setStep(3);
        setTimeout(() => scrollTo(loadsRef), 300);

        // begin polling
        pollResult(data.job_id);
      } else {
        setLoadingLoads(false);
      }
    } finally {
      setSending(false);
    }
  };

  const handleSelectLoad = (l: Load) => {
    setSelectedLoad(l);
    setStep(4);
    setTimeout(() => scrollTo(negotiationRef), 300);
  };

  // cleanup polling on unmount
  useEffect(() => {
    return () => stopPolling();
  }, []);

  // return <h1 className="text-4xl font-bold text-red-500">Hello Tailwind</h1>
  return (
  <div className="flex items-center justify-center min-h-screen bg-gray-100 px-4">
    <div className="w-full max-w-2xl bg-white rounded-xl shadow-md ring-1 ring-gray-200 p-8">
      
      {/* Header */}
      <header className="border-b border-gray-200 pb-6 mb-6">
        <h1 className="text-center text-2xl font-bold text-blue-600">
          🚚 HappyRobot Freight Broker
        </h1>
        <p className="mt-2 text-center text-sm text-gray-500">
          Verify your MC Key and request suggested loads
        </p>
      </header>

      {/* Step 0 - MC Key */}
      <section className="mb-8" ref={tokenRef}> 
        <h2 className="text-lg font-semibold text-gray-800 mb-2">
          MC Key Verification
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          Enter your MC Key (verified against FMCSA API).
        </p>

        <textarea
          value={mc_key}
          onChange={(e) => setMCKey(e.target.value)}
          className="w-full h-20 p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-none"
        />

        <button
          onClick={verify}
          disabled={verifying || !mc_key.trim()}
          className={`mt-4 w-full py-3 rounded-md font-semibold text-white transition
            ${verifying || !mc_key.trim()
              ? "bg-green-400 cursor-not-allowed"
              : "bg-green-500 hover:bg-green-600"}
          `}
        >
          {verifying ? "Verifying..." : "Verify Key"}
        </button>

        {verifyResp && (
          verifyResp.eligible ? (
            <div className="mt-4 p-4 border border-green-300 rounded-md bg-green-50 text-gray-800">
              <p className="font-medium">✅ Verified MC {verifyResp.mc}</p>
              <ul className="list-disc list-inside text-sm mt-2">
                <li>Name: {verifyResp.legal_name}</li>
                <li>City: {verifyResp.city}</li>
                <li>State: {verifyResp.state}</li>
                <li>DBA Name: {verifyResp.dba_name}</li>
                <li>Eligible: Yes</li>
              </ul>
            </div>
          ) : (
            <div className="mt-4 p-4 border border-red-400 rounded-md bg-red-50 text-red-700 font-medium">
              ❌ Not eligible – MC {verifyResp.mc}. Enter correct MC key
              <ul className="list-disc list-inside text-sm mt-2">
                <li>Eligible: No</li>
              </ul>
            </div>
          )
        )}
      </section>



      

      {/* Step 2 - Message */}
      {verifyResp?.eligible && step >= 1 && (
        <section className="mb-8" ref={messageRef}>
          <h2 className="text-lg font-semibold text-gray-800 mb-2">
            What kind of loads would you want to browse?
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            Input the type of load you are looking for.Add keywords related to origin, max rate you want to pay and limit of results to see
            
          </p>
          <h2 className="text-sm italic text-gray-800 mb-2">
            eg: :
            <li>"Give me maximum of 15 loads"
              </li>
              <li>"Loads that start from San Jose"
                </li>
                <li>"Limit of 6 loads, with max rate of $800"</li> 
          </h2>

          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="w-full h-24 p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />

          <button
            onClick={send}
            disabled={sending}
            className={`mt-4 w-full py-3 rounded-md font-semibold text-white transition
              ${sending
                ? "bg-blue-400 cursor-not-allowed"
                : "bg-blue-500 hover:bg-blue-600"}
            `}
          >
            {sending ? "Sending…" : "Request Suggested Loads"}
          </button>
        </section>
      )}

      {/* Step 3 - Loads */}
      {verifyResp?.eligible && step >= 3 && (
        <section className="mb-8" ref={loadsRef}>
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Suggested Loads</h2>

          {loadingLoads && (
            <div className="w-8 h-8 border-4 border-gray-300 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
          )}

          <div className="grid gap-4 grid-cols-1 sm:grid-cols-2">
            {resp.suggested_loads.map((l) => {
              const isSelected = selectedLoad?.load_id === l.load_id;
              return (
                <div
                  key={l.load_id}
                  onClick={() => handleSelectLoad(l)}
                  className={`p-4 rounded-md cursor-pointer transition
                    ${isSelected
                      ? "border-2 border-green-500 bg-green-50"
                      : "border border-gray-300 bg-white hover:shadow"}
                  `}
                >
                  <LoadCard load={l} />
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Step 4 - Negotiation */}
      {verifyResp?.eligible && step >= 4 && selectedLoad && (
        <section ref={negotiationRef}>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Negotiating for:</h3>
          <LoadCard load={selectedLoad} />
          <NegotiationChat token={token} defaultLoad={selectedLoad} />
        </section>
      )}
    </div>
  </div>
);


}
