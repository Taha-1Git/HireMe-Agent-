/**
 * Demo Mode Controller
 * 
 * Allows manual triggering of:
 * 1. Multiple faces detection event
 * 2. Canned generic/contradictory answer through real AuthenticityAgent
 * 
 * Only available in development mode (env gate)
 */

"use client";

import { useState, useRef } from "react";
import { AlertCircle, Play, RotateCcw } from "lucide-react";

interface DemoModeProps {
  sessionId: string;
  candidateName?: string;
  websocketSend?: (message: any) => void; // New prop for sending messages to WebSocket
  enabled?: boolean; // Controlled by env var NEXT_PUBLIC_DEMO_MODE
}

const CANNED_ANSWERS = [
  {
    label: "Generic CV Claim",
    description: "A textbook answer that doesn't prove project ownership",
    answer:
      "I learned about REST APIs and used Python with Flask framework to create HTTP endpoints. I also worked with databases using SQL and implemented proper error handling.",
  },
  {
    label: "CV Contradiction",
    description: "Answer contradicts claimed technical skills",
    answer:
      "I primarily focused on the UI design and color schemes. I used some CSS frameworks to make things look good. For the backend, I just used some templates that were already available.",
  },
  {
    label: "Overly Technical Nonsense",
    description: "Sounds impressive but reveals lack of real experience",
    answer:
      "We utilized quantum-entangled microservices with blockchain-distributed cache layers running on edge computing nodes for real-time vector database optimization.",
  },
];

export function DemoModeController({
  sessionId,
  candidateName = "Candidate",
  websocketSend,
  enabled = false,
}: DemoModeProps) {
  const [activeTab, setActiveTab] = useState<"multiple_faces" | "generic_answer">(
    "multiple_faces"
  );
  const [selectedAnswer, setSelectedAnswer] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const multipleFacesTriggeredRef = useRef(false);

  if (!enabled) {
    return null;
  }

  const triggerMultipleFaces = async () => {
    if (multipleFacesTriggeredRef.current) return;

    setIsProcessing(true);
    multipleFacesTriggeredRef.current = true;

    try {
      // Send to WebSocket or backend log
      const event = {
        type: "demo_event",
        event_type: "multiple_faces",
        timestamp: new Date().toISOString(),
        message: "[DEMO] Multiple faces detected. Possible external assistance.",
        session_id: sessionId,
      };

      // Send to WebSocket via prop
      if (websocketSend) {
        websocketSend(event);
      } else {
        // Fallback to fetch if websocketSend not provided (e.g., for testing)
        await fetch(`http://localhost:8000/api/demo/log-event`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(event),
        }).catch(() => {});
      }

      setResult({
        success: true,
        message: "✓ Multiple faces event triggered and logged",
        eventType: "multiple_faces",
      });

      // Reset after 3 seconds
      setTimeout(() => {
        multipleFacesTriggeredRef.current = false;
        setResult(null);
      }, 3000);
    } catch (error) {
      setResult({
        success: false,
        message: `Failed to trigger event: ${error}`,
        eventType: "multiple_faces",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const triggerGenericAnswer = async () => {
    setIsProcessing(true);

    try {
      const answer = CANNED_ANSWERS[selectedAnswer].answer;

      // Call real AuthenticityAgent through backend
      const response = await fetch(
        `http://localhost:8000/api/demo/test-authenticity`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: sessionId,
            candidate_answer: answer,
            test_label: CANNED_ANSWERS[selectedAnswer].label,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      setResult({
        success: true,
        message: `✓ Generic answer processed through real AuthenticityAgent`,
        eventType: "generic_answer",
        details: data,
      });

      // Reset after 5 seconds
      setTimeout(() => {
        setResult(null);
      }, 5000);
    } catch (error) {
      setResult({
        success: false,
        message: `Failed to process generic answer: ${error}`,
        eventType: "generic_answer",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-sm">
      {/* Floating toggle/panel */}
      <div className="bg-white rounded-lg shadow-lg border-2 border-purple-300">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-4 py-3 rounded-t-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle size={20} />
            <span className="font-bold">🧪 Demo Mode</span>
          </div>
          <button
            onClick={() => setActiveTab(activeTab === "multiple_faces" ? "generic_answer" : "multiple_faces")}
            className="text-xs bg-white/20 hover:bg-white/30 px-2 py-1 rounded"
          >
            {activeTab === "multiple_faces" ? "→ Generic Answer" : "→ Multiple Faces"}
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {activeTab === "multiple_faces" && (
            <div className="space-y-3">
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">
                  Trigger: Multiple Faces Detection
                </h3>
                <p className="text-sm text-gray-600 mb-3">
                  Simulate detection of multiple people in frame. This should:
                </p>
                <ul className="text-xs text-gray-600 space-y-1 ml-4 mb-3">
                  <li>✓ Set faces_detected = 2</li>
                  <li>✓ Push warning to WebSocket log</li>
                  <li>✓ Increase suspicion_score</li>
                </ul>
              </div>

              <button
                onClick={triggerMultipleFaces}
                disabled={isProcessing}
                className="w-full bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white font-semibold py-2 px-3 rounded flex items-center justify-center gap-2"
              >
                <Play size={16} />
                {isProcessing ? "Triggering..." : "Trigger Now (Shift+M)"}
              </button>
            </div>
          )}

          {activeTab === "generic_answer" && (
            <div className="space-y-3">
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">
                  Trigger: Generic Answer Detection
                </h3>
                <p className="text-sm text-gray-600 mb-3">
                  Send canned answer through real AuthenticityAgent. This should:
                </p>
                <ul className="text-xs text-gray-600 space-y-1 ml-4 mb-3">
                  <li>✓ Use REAL AuthenticityAgent (not mocked)</li>
                  <li>✓ Detect generic/CV contradiction</li>
                  <li>✓ Return authenticity concern flag</li>
                </ul>
              </div>

              {/* Answer selector */}
              <div className="space-y-2">
                <label className="block text-xs font-semibold text-gray-700">
                  Select canned answer:
                </label>
                <select
                  value={selectedAnswer}
                  onChange={(e) => setSelectedAnswer(Number(e.target.value))}
                  disabled={isProcessing}
                  className="w-full px-2 py-2 border border-gray-300 rounded text-xs bg-white"
                >
                  {CANNED_ANSWERS.map((ans, i) => (
                    <option key={i} value={i}>
                      {ans.label}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 italic">
                  {CANNED_ANSWERS[selectedAnswer].description}
                </p>
              </div>

              <button
                onClick={triggerGenericAnswer}
                disabled={isProcessing}
                className="w-full bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-400 text-white font-semibold py-2 px-3 rounded flex items-center justify-center gap-2"
              >
                <Play size={16} />
                {isProcessing ? "Processing..." : "Process Answer"}
              </button>
            </div>
          )}
        </div>

        {/* Result message */}
        {result && (
          <div
            className={`px-4 py-3 rounded-b-lg text-sm font-semibold flex items-start gap-2 ${
              result.success
                ? "bg-green-50 text-green-800 border-t border-green-200"
                : "bg-red-50 text-red-800 border-t border-red-200"
            }`}
          >
            <div className="mt-1">{result.success ? "✓" : "✗"}</div>
            <div>
              <div>{result.message}</div>
              {result.details && (
                <details className="text-xs mt-1 text-gray-600">
                  <summary className="cursor-pointer font-mono">Details</summary>
                  <pre className="mt-1 p-2 bg-white rounded border text-xs overflow-auto max-h-32">
                    {JSON.stringify(result.details, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Demo mode note */}
      <div className="text-xs text-gray-500 mt-2 text-right">
        Demo Mode {enabled ? "✓ enabled" : "✗ disabled"} (NEXT_PUBLIC_DEMO_MODE)
      </div>
    </div>
  );
}
