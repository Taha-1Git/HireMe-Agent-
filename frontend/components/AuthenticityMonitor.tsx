/**
 * Real-time Authenticity Monitoring Component
 * 
 * Runs continuously during interview:
 * - Detects multiple faces (flag for external assistance)
 * - Tracks off-screen gaze (candidate looking away)
 * - Combines with backend authenticity flags
 * - Maintains running suspicion score (0-100)
 * - Pushes events to WebSocket
 */

"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import * as faceDetection from "@tensorflow-models/face-landmarks-detection";
import * as tf from "@tensorflow/tfjs";
import "@tensorflow/tfjs-backend-webgl";
import { AlertCircle, Eye, Users } from "lucide-react";

interface AuthenticityFlag {
  timestamp: string;
  type: "multiple_faces" | "off_screen_gaze" | "cv_contradiction" | "generic_answer";
  agent: string;
  severity: "low" | "medium" | "high";
  message: string;
}

interface MonitoringState {
  facesDetected: number;
  offScreenGazeRatio: number;
  suspicionScore: number; // 0-100
  flags: AuthenticityFlag[];
  lastFrameTime: number;
}

interface AuthenticityMonitorProps {
  sessionId: string;
  onFlagDetected?: (flag: AuthenticityFlag) => void;
  onSuspicionScoreUpdate?: (score: number) => void;
  websocketSend?: (message: any) => void;
  demoMode?: boolean;
  onDemoMultipleFaces?: () => void;
  className?: string;
}

const GAZE_THRESHOLD = 0.35; // If looking away >35% of time, flag it
const GAZE_SAMPLE_WINDOW = 5000; // 5 second rolling window
const MONITOR_INTERVAL = 500; // Sample every 500ms

export function AuthenticityMonitor({
  sessionId,
  onFlagDetected,
  onSuspicionScoreUpdate,
  websocketSend,
  demoMode = false,
  onDemoMultipleFaces,
  className,
}: AuthenticityMonitorProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const detectorRef = useRef<any>(null);
  const monitoringStateRef = useRef<MonitoringState>({
    facesDetected: 0,
    offScreenGazeRatio: 0,
    suspicionScore: 0,
    flags: [],
    lastFrameTime: Date.now(),
  });

  const gazeHistoryRef = useRef<boolean[]>([]);
  const demoTriggeredRef = useRef(false);

  // Initialize detector
  useEffect(() => {
    const initializeDetector = async () => {
      try {
        await tf.setBackend("webgl");
        const detector = await faceDetection.createDetector(
          faceDetection.SupportedModels.MediaPipeFaceMesh,
          { 
            maxFaces: 5,
            runtime: 'tfjs',
            refineLandmarks: true // Required for iris tracking (landmarks 468-477)
          }
        );
        detectorRef.current = detector;
      } catch (error) {
        console.error("Failed to initialize face detector:", error);
      }
    };

    initializeDetector();
  }, []);

  // Process video frames at regular intervals
  useEffect(() => {
    if (!videoRef.current || !detectorRef.current) return;

    const monitorInterval = setInterval(async () => {
      if (!videoRef.current || videoRef.current.paused) return;

      try {
        const faces = await detectorRef.current.estimateFaces(videoRef.current);

        // Update face count
        const previousFaceCount = monitoringStateRef.current.facesDetected;
        monitoringStateRef.current.facesDetected = faces.length;

        // FLAG: Multiple faces detected
        if (faces.length > 1 && previousFaceCount <= 1) {
          const flag: AuthenticityFlag = {
            timestamp: new Date().toISOString(),
            type: "multiple_faces",
            agent: "RealTimeMonitor",
            severity: "high",
            message: "Multiple faces detected. Possible external assistance.",
          };
          addFlag(flag);
        }

        // Analyze gaze for first detected face
        if (faces.length > 0 && faces[0].landmarks) {
          const isLookingAtScreen = isGazingAtScreen(faces[0].landmarks);
          gazeHistoryRef.current.push(isLookingAtScreen);

          // Keep rolling window of last 10 samples (~5 seconds)
          if (gazeHistoryRef.current.length > 10) {
            gazeHistoryRef.current.shift();
          }

          // Calculate off-screen gaze ratio
          if (gazeHistoryRef.current.length > 0) {
            const lookingAwayCount = gazeHistoryRef.current.filter(
              (g) => !g
            ).length;
            const offScreenRatio = lookingAwayCount / gazeHistoryRef.current.length;
            monitoringStateRef.current.offScreenGazeRatio = offScreenRatio;

            // FLAG: High off-screen gaze
            if (offScreenRatio > GAZE_THRESHOLD) {
              const flag: AuthenticityFlag = {
                timestamp: new Date().toISOString(),
                type: "off_screen_gaze",
                agent: "RealTimeMonitor",
                severity: "medium",
                message: "High off-screen gaze detected.",
              };
              addFlag(flag);
            }
          }
        }

        // Draw visualization on canvas
        if (canvasRef.current && videoRef.current) {
          drawVisualization(canvasRef.current, videoRef.current, faces);
        }

        // Update suspicion score
        updateSuspicionScore();
      } catch (error) {
        console.error("Error monitoring authenticity:", error);
      }
    }, MONITOR_INTERVAL);

    return () => clearInterval(monitorInterval);
  }, []);

  // Handle backend authenticity flags from WebSocket
  const addFlag = useCallback(
    (flag: AuthenticityFlag) => {
      monitoringStateRef.current.flags.push(flag);

      // Avoid duplicate flags
      const isDuplicate =
        monitoringStateRef.current.flags.filter(
          (f) =>
            f.type === flag.type &&
            Date.now() - new Date(f.timestamp).getTime() < 2000 // Within 2 seconds
        ).length > 1;

      if (!isDuplicate) {
        onFlagDetected?.(flag); // Still call local handler
        websocketSend?.({
          type: "authenticity_flag",
          agent: flag.agent,
          flag_type: flag.type,
          severity: flag.severity,
          message: flag.message,
          timestamp: flag.timestamp,
        });
      }
    },
    [onFlagDetected, websocketSend]
  );

  const updateSuspicionScore = useCallback(() => {
    const state = monitoringStateRef.current;
    let score = 0;

    // Factor 1: Multiple faces (high weight)
    if (state.facesDetected > 1) {
      score += 30;
    }

    // Factor 2: Off-screen gaze (medium weight)
    if (state.offScreenGazeRatio > GAZE_THRESHOLD) {
      score += 20 * (state.offScreenGazeRatio - GAZE_THRESHOLD) / (1 - GAZE_THRESHOLD);
    }

    // Factor 3: Recent authenticity flags (medium weight)
    // Count flags from last 30 seconds
    const recentFlags = state.flags.filter(
      (f) => Date.now() - new Date(f.timestamp).getTime() < 30000
    );
    const flagScore =
      recentFlags.length > 0
        ? Math.min(50, recentFlags.length * 10)
        : 0;
    score += flagScore;

    // Cap at 100
    score = Math.min(100, score);
    state.suspicionScore = Math.round(score);

    onSuspicionScoreUpdate?.(state.suspicionScore);
  }, [onSuspicionScoreUpdate]);

  // Demo mode trigger for multiple faces
  useEffect(() => {
    if (!demoMode || demoTriggeredRef.current) return;

    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === "m" && e.shiftKey) {
        // Shift+M triggers multiple faces demo
        const flag: AuthenticityFlag = {
          timestamp: new Date().toISOString(),
          type: "multiple_faces",
          agent: "RealTimeMonitor",
          severity: "high",
          message: "[DEMO] Multiple faces detected. Possible external assistance.",
        };
        websocketSend?.({
          type: "authenticity_flag",
          agent: flag.agent,
          flag_type: flag.type,
          severity: flag.severity,
          message: flag.message,
          timestamp: flag.timestamp,
        });
        demoTriggeredRef.current = true;
        onDemoMultipleFaces?.();
        setTimeout(() => {
          demoTriggeredRef.current = false;
        }, 2000);
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [demoMode, addFlag, onDemoMultipleFaces]);

  // Public method to add backend flags
  useEffect(() => {
    (window as any).addAuthenticityFlag = addFlag;
  }, [addFlag]);

  const state = monitoringStateRef.current;
  const suspicionBand =
    state.suspicionScore < 34 ? "Low" : state.suspicionScore < 67 ? "Medium" : "High";
  const suspicionColor =
    suspicionBand === "Low"
      ? "text-green-600"
      : suspicionBand === "Medium"
        ? "text-yellow-600"
        : "text-red-600";

  return (
    <div className={`flex flex-col gap-4 p-4 bg-gray-50 rounded-lg border border-gray-200 ${className ?? ""}`}>
      {/* Hidden canvas and video for processing */}
      <video
        ref={videoRef}
        className="hidden"
        playsInline
        muted
        autoPlay
      />

      {/* Monitoring visualization */}
      <div className="relative w-full bg-black rounded-lg overflow-hidden" style={{ aspectRatio: "16/9" }}>
        <canvas
          ref={canvasRef}
          width={1280}
          height={720}
          className="w-full h-full"
        />

        {/* Stats overlay */}
        <div className="absolute top-4 left-4 bg-black/70 text-white px-3 py-2 rounded text-sm font-mono">
          <div>Faces: {state.facesDetected}</div>
          <div>Gaze Away: {Math.round(state.offScreenGazeRatio * 100)}%</div>
        </div>

        {/* Suspicion score badge */}
        <div
          className={`absolute top-4 right-4 px-4 py-2 rounded-lg font-bold text-white ${
            suspicionBand === "Low"
              ? "bg-green-600"
              : suspicionBand === "Medium"
                ? "bg-yellow-600"
                : "bg-red-600"
          }`}
        >
          Suspicion: {state.suspicionScore} ({suspicionBand})
        </div>

        {/* Warnings overlay */}
        {state.facesDetected > 1 && (
          <div className="absolute bottom-4 left-4 flex items-center gap-2 bg-red-600 text-white px-3 py-2 rounded">
            <Users size={16} />
            <span>Multiple faces detected</span>
          </div>
        )}
        {state.offScreenGazeRatio > GAZE_THRESHOLD && (
          <div className="absolute bottom-4 left-64 flex items-center gap-2 bg-yellow-600 text-white px-3 py-2 rounded">
            <Eye size={16} />
            <span>High off-screen gaze</span>
          </div>
        )}
      </div>

      {/* Flags panel */}
      {state.flags.length > 0 && (
        <div className="max-h-32 overflow-y-auto bg-white border border-red-200 rounded p-3">
          <h4 className="font-semibold text-sm text-red-900 mb-2 flex items-center gap-2">
            <AlertCircle size={16} />
            Authenticity Concerns
          </h4>
          <div className="space-y-1">
            {state.flags.slice(-5).map((flag, i) => (
              <div
                key={i}
                className={`text-xs px-2 py-1 rounded ${
                  flag.severity === "high"
                    ? "bg-red-100 text-red-800"
                    : flag.severity === "medium"
                      ? "bg-yellow-100 text-yellow-800"
                      : "bg-blue-100 text-blue-800"
                }`}
              >
                <span className="font-semibold">{flag.agent}:</span> {flag.message}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Demo mode indicator */}
      {demoMode && (
        <div className="text-xs text-gray-500 bg-blue-50 p-2 rounded border border-blue-200">
          Demo Mode: Press Shift+M to trigger multiple faces detection
        </div>
      )}
    </div>
  );
}

/**
 * Determine if candidate is gazing at screen (roughly centered)
 */
function isGazingAtScreen(landmarks: number[][]): boolean {
  // Use nose tip to estimate gaze direction
  const noseTip = landmarks[1];
  const leftEye = landmarks[468]; // Left iris
  const rightEye = landmarks[473]; // Right iris

  if (!noseTip || !leftEye || !rightEye) return true; // Default to looking

  // Rough heuristic: if nose tip is between eyes, likely looking at screen
  const xRange = rightEye[0] - leftEye[0];
  const noseBetweenEyes =
    noseTip[0] > leftEye[0] - xRange * 0.3 &&
    noseTip[0] < rightEye[0] + xRange * 0.3;

  // If head is rotated too much, flag as looking away
  const headTilt = Math.abs(landmarks[127][1] - landmarks[356][1]);
  const faceTooTilted = headTilt > 50; // 50 pixels = significant tilt

  return noseBetweenEyes && !faceTooTilted;
}

/**
 * Draw face detection visualization on canvas
 */
function drawVisualization(
  canvas: HTMLCanvasElement,
  video: HTMLVideoElement,
  faces: any[]
) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  // Scale canvas to match video
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  // Draw video frame
  ctx.drawImage(video, 0, 0);

  // Draw faces
  faces.forEach((face, faceIndex) => {
    // Draw face bounding box
    const bbox = face.box;
    if (bbox) {
      ctx.strokeStyle = faceIndex === 0 ? "green" : "red";
      ctx.lineWidth = 2;
      ctx.strokeRect(bbox.xMin, bbox.yMin, bbox.width, bbox.height);

      // Label for main face
      if (faceIndex === 0) {
        ctx.fillStyle = "green";
        ctx.font = "bold 16px Arial";
        ctx.fillText("Primary Face", bbox.xMin, bbox.yMin - 10);
      } else {
        ctx.fillStyle = "red";
        ctx.font = "bold 16px Arial";
        ctx.fillText("Face " + (faceIndex + 1), bbox.xMin, bbox.yMin - 10);
      }
    }

    // Draw face landmarks for main face
    if (faceIndex === 0 && face.landmarks) {
      ctx.fillStyle = "cyan";
      ctx.globalAlpha = 0.6;
      face.landmarks.forEach((landmark: number[]) => {
        ctx.beginPath();
        ctx.arc(landmark[0], landmark[1], 2, 0, 2 * Math.PI);
        ctx.fill();
      });
      ctx.globalAlpha = 1.0;
    }
  });
}
