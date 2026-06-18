"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { PulsePerimeter } from "./PulsePerimeter";
import { AuthenticityMonitor } from "./AuthenticityMonitor";
import { Button } from "./ui/button";
import { ShieldCheck, LogOut } from "lucide-react";
import { DemoModeController } from "./DemoModeController";

export function Step4LiveInterview({ 
  sessionId, 
  onComplete 
}: { 
  sessionId: string; 
  profile: any; 
  onComplete: (report: any) => void 
}) {
  const [messages, setMessages] = useState<{ role: string; content: string; agent?: string }[]>([]);
  const [logs, setLogs] = useState<{ timestamp: string; message: string }[]>([]);
  const [suspicionScore, setSuspicionScore] = useState(0);
  const [answer, setAnswer] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/api/interview/ws/${sessionId}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Distinguish between interview messages and log events
      if (data.type === "question" || data.type === "agent_response") {
        setMessages(prev => [...prev, { role: "assistant", content: data.content, agent: data.agent }]);
        setIsThinking(false);
      } else {
        setLogs((prev) => [...prev, data].slice(-50));
      }
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) ws.close();
    };
  }, [sessionId]);

  const sendMessage = useCallback((payload: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
    }
  }, []);

  const handleSendAnswer = () => {
    if (!answer.trim()) return;
    
    setMessages(prev => [...prev, { role: "user", content: answer }]);
    sendMessage({ type: "answer", content: answer });
    setAnswer("");
    setIsThinking(true);
  };

  const handleEndInterview = async () => {
    const res = await fetch(`http://localhost:8000/api/interview/report/${sessionId}`);
    const data = await res.json();
    onComplete(data);
  };

  return (
    <div className="grid grid-cols-12 h-full gap-px bg-brand-slate/20">
      <div className="col-span-12 lg:col-span-7 bg-brand-night p-8 flex flex-col h-[calc(100vh-80px)]">
        <div className="flex-1 overflow-y-auto pr-4 space-y-6 scrollbar-thin scrollbar-thumb-brand-slate">
          {messages.map((msg, i) => (
            <div key={i} className={cn("max-w-[80%]", msg.role === "assistant" ? "mr-auto" : "ml-auto")}>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] font-mono uppercase text-brand-cyan/50">
                  {msg.agent || msg.role}
                </span>
              </div>
              <div className={cn(
                "p-4 rounded-lg text-sm leading-relaxed",
                msg.role === "assistant" ? "bg-brand-slate/50 border border-brand-slate" : "bg-brand-cyan/10 border border-brand-cyan/20"
              )}>
                {msg.content}
              </div>
            </div>
          ))}
          {isThinking && <div className="animate-pulse text-brand-cyan text-xs font-mono">AI is analyzing...</div>}
          <div ref={scrollRef} />
        </div>

        <div className="mt-6 pt-6 border-t border-brand-slate/50">
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            className="w-full bg-brand-slate/30 border border-brand-slate rounded-lg p-4 text-sm focus:ring-1 focus:ring-brand-cyan outline-none resize-none h-24"
            placeholder="Type your answer clearly..."
          />
          <div className="flex justify-between items-center mt-3">
            <Button onClick={handleSendAnswer} size="sm" className="bg-brand-cyan text-brand-night hover:bg-brand-cyan/90 font-display uppercase tracking-widest text-xs h-8">
              Transmit Answer
            </Button>
          </div>
        </div>
      </div>

      <div className="col-span-12 lg:col-span-5 bg-brand-night border-l border-brand-slate/50 flex flex-col h-[calc(100vh-80px)]">
        <div className="p-6">
          <PulsePerimeter score={suspicionScore}>
            <AuthenticityMonitor
              sessionId={sessionId}
              onSuspicionScoreUpdate={setSuspicionScore}
              websocketSend={sendMessage}
              className="aspect-video w-full"
            />
          </PulsePerimeter>
          <div className="mt-4 flex items-center justify-between bg-brand-slate/30 p-3 rounded border border-brand-slate">
            <ShieldCheck className={cn("w-4 h-4", suspicionScore > 66 ? "text-brand-amber" : "text-brand-emerald")} />
            <span className="text-[10px] font-mono text-brand-cyan">{suspicionScore}% Risk Score</span>
          </div>
        </div>

        <div className="flex-1 overflow-hidden flex flex-col p-6 pt-0">
          <div className="flex-1 bg-black/40 border border-brand-slate/50 rounded p-4 font-mono text-[10px] overflow-y-auto space-y-1">
            {logs.map((log, i) => (
              <div key={i} className="flex gap-3">
                <span className="text-brand-white/20">[{new Date(log.timestamp).toLocaleTimeString([], { hour12: false })}]</span>
                <span className="text-brand-cyan/80">{log.message}</span>
              </div>
            ))}
          </div>
        </div>
        <DemoModeController sessionId={sessionId} enabled={true} websocketSend={sendMessage} />
        <div className="p-4 bg-brand-night border-t border-brand-slate/50">
          <Button variant="destructive" className="w-full text-xs uppercase" onClick={handleEndInterview}>
            <LogOut className="w-3 h-3 mr-2" /> End Session
          </Button>
        </div>
      </div>
    </div>
  );
}