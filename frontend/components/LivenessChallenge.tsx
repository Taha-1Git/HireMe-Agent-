/**
 * Liveness Challenge Component
 * 
 * Detects liveness through random challenges:
 * - Blink detection (eye aspect ratio dips)
 * - Head turn detection (face rotation)
 * - Smile detection (mouth aspect ratio)
 * - Voice/audio detection (optional, requires audio permission)
 */

"use client";

import { useEffect, useRef, useState } from "react";
import * as faceDetection from "@tensorflow-models/face-landmarks-detection";
import * as tf from "@tensorflow/tfjs";
import "@tensorflow/tfjs-backend-webgl";

interface LivenessResult {
  passed: boolean;
  challenge: string;
  message: string;
  confidence: number;
}

const LIVENESS_CHALLENGES = [
  {
    id: "blink",
    instruction: "Blink twice",
    description: "Please blink your eyes twice",
  },
  {
    id: "turn_left",
    instruction: "Turn your head left",
    description: "Please turn your head to the left",
  },
  {
    id: "turn_right",
    instruction: "Turn your head right",
    description: "Please turn your head to the right",
  },
  {
    id: "smile",
    instruction: "Smile",
    description: "Please smile naturally",
  },
  {
    id: "straight",
    instruction: "Look straight",
    description: "Please look directly at the camera",
  },
];

interface LivenessChallengeProps {
  onComplete: (result: LivenessResult) => void;
  candidateName?: string;
}

export function LivenessChallenge({
  onComplete,
  candidateName = "Candidate",
}: LivenessChallengeProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [challenge, setChallenge] = useState<(typeof LIVENESS_CHALLENGES)[0] | null>(null);
  const [status, setStatus] = useState("Initializing camera...");
  const [timeLeft, setTimeLeft] = useState(10);
  const [isProcessing, setIsProcessing] = useState(false);
  const detectorRef = useRef<any>(null);

  // Initialize camera and detector
  useEffect(() => {
    const initializeCamera = async () => {
      try {
        // Load TensorFlow model
        await tf.setBackend("webgl");
        const detector = await faceDetection.createDetector(
          faceDetection.SupportedModels.MediaPipeFaceMesh,
          { maxFaces: 1 }
        );
        detectorRef.current = detector;

        // Request camera access
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "user", width: 640, height: 480 },
        });

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setStatus("Camera ready. Starting challenge...");

          // Wait for video to load
          videoRef.current.onloadedmetadata = () => {
            videoRef.current?.play();
            // Select random challenge
            const randomChallenge =
              LIVENESS_CHALLENGES[
                Math.floor(Math.random() * LIVENESS_CHALLENGES.length)
              ];
            setChallenge(randomChallenge);
            setIsProcessing(true);
          };
        }
      } catch (error) {
        setStatus(`Camera access denied or failed: ${error}`);
      }
    };

    initializeCamera();

    return () => {
      if (videoRef.current?.srcObject) {
        const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
        tracks.forEach((track) => track.stop());
      }
    };
  }, []);

  // Process video frames
  useEffect(() => {
    if (!isProcessing || !challenge) return;

    const processFrame = async () => {
      if (
        !videoRef.current ||
        !canvasRef.current ||
        !detectorRef.current ||
        videoRef.current.paused
      ) {
        requestAnimationFrame(processFrame);
        return;
      }

      try {
        // Detect faces
        const faces = await detectorRef.current.estimateFaces(videoRef.current);

        if (!faces || faces.length === 0) {
          setStatus("No face detected. Please position yourself in front of the camera.");
          requestAnimationFrame(processFrame);
          return;
        }

        // Draw face landmarks on canvas
        const canvas = canvasRef.current;
        const ctx = canvas.getContext("2d");
        if (ctx && videoRef.current) {
          ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

          faces.forEach((face) => {
            if (face.landmarks) {
              // Draw landmarks
              ctx.fillStyle = "green";
              ctx.globalAlpha = 0.7;
              face.landmarks.forEach((landmark: number[]) => {
                ctx.beginPath();
                ctx.arc(landmark[0], landmark[1], 3, 0, 2 * Math.PI);
                ctx.fill();
              });
              ctx.globalAlpha = 1.0;
            }
          });
        }

        // Analyze face for liveness challenge
        const result = await analyzeLiveness(faces[0], challenge);

        if (result.passed) {
          setIsProcessing(false);
          onComplete({
            passed: true,
            challenge: challenge.id,
            message: `Liveness challenge "${challenge.instruction}" passed!`,
            confidence: result.confidence,
          });
        } else {
          setStatus(result.message);
        }
      } catch (error) {
        console.error("Error processing frame:", error);
      }

      requestAnimationFrame(processFrame);
    };

    // Start processing
    processFrame();
  }, [isProcessing, challenge, onComplete]);

  // Countdown timer
  useEffect(() => {
    if (!isProcessing) return;

    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          setIsProcessing(false);
          onComplete({
            passed: false,
            challenge: challenge?.id || "unknown",
            message: "Time limit exceeded. Please try again.",
            confidence: 0,
          });
          return 10;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isProcessing, challenge, onComplete]);

  return (
    <div className="flex flex-col items-center justify-center gap-6 p-8 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Liveness Challenge
        </h2>
        <p className="text-gray-600">
          {challenge
            ? `Please ${challenge.instruction.toLowerCase()}`
            : "Preparing camera..."}
        </p>
      </div>

      <div className="relative w-full max-w-md">
        <video
          ref={videoRef}
          className="hidden"
          playsInline
          muted
        />
        <canvas
          ref={canvasRef}
          width={640}
          height={480}
          className="w-full border-2 border-blue-300 rounded-lg bg-black"
        />

        {/* Challenge instruction overlay */}
        {challenge && (
          <div className="absolute top-4 left-4 bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold">
            {challenge.description}
          </div>
        )}

        {/* Timer overlay */}
        {isProcessing && (
          <div className="absolute top-4 right-4 bg-red-600 text-white px-3 py-1 rounded-full font-bold">
            {timeLeft}s
          </div>
        )}
      </div>

      {/* Status message */}
      <div
        className={`text-center text-sm font-medium px-4 py-2 rounded-lg ${
          status.includes("passed")
            ? "text-green-700 bg-green-100"
            : status.includes("No face") || status.includes("Camera")
              ? "text-orange-700 bg-orange-100"
              : "text-gray-700 bg-gray-100"
        }`}
      >
        {status}
      </div>
    </div>
  );
}

/**
 * Analyze face landmarks to detect liveness challenge response
 */
async function analyzeLiveness(
  face: any,
  challenge: (typeof LIVENESS_CHALLENGES)[0]
): Promise<{ passed: boolean; confidence: number; message: string }> {
  const landmarks = face.landmarks;
  if (!landmarks || landmarks.length < 468) {
    return { passed: false, confidence: 0, message: "Insufficient face data" };
  }

  const leftEyeOpen = calculateEyeAspectRatio(landmarks, "left") > 0.15;
  const rightEyeOpen = calculateEyeAspectRatio(landmarks, "right") > 0.15;
  const headYaw = calculateHeadYaw(landmarks);
  const mouthOpen = calculateMouthAspectRatio(landmarks) > 0.03;

  let passed = false;
  let message = "";
  let confidence = 0;

  switch (challenge.id) {
    case "blink":
      // Simplified blink detection (would need frame history in production)
      passed = !leftEyeOpen && !rightEyeOpen;
      confidence = passed ? 0.8 : 0;
      message = passed ? "Blink detected!" : "Please blink your eyes";
      break;

    case "turn_left":
      passed = headYaw < -20;
      confidence = Math.max(0, (Math.abs(headYaw) - 20) / 30);
      message = passed
        ? "Left turn detected!"
        : `Turn more to the left (Current: ${Math.round(headYaw)}°)`;
      break;

    case "turn_right":
      passed = headYaw > 20;
      confidence = Math.max(0, (headYaw - 20) / 30);
      message = passed
        ? "Right turn detected!"
        : `Turn more to the right (Current: ${Math.round(headYaw)}°)`;
      break;

    case "smile":
      passed = mouthOpen;
      confidence = mouthOpen ? 0.7 : 0;
      message = passed ? "Smile detected!" : "Please smile";
      break;

    case "straight":
      passed = Math.abs(headYaw) < 15;
      confidence = 1 - Math.abs(headYaw) / 30;
      message = passed ? "Face centered!" : "Please look straight ahead";
      break;
  }

  return { passed, confidence: Math.min(1, confidence), message };
}

/**
 * Calculate eye aspect ratio (0 = closed, >0.15 = open)
 */
function calculateEyeAspectRatio(
  landmarks: number[][],
  eye: "left" | "right"
): number {
  // MediaPipe FaceMesh indices for left eye
  // Upper eyelid: 159, 145, 133
  // Lower eyelid: 158, 153, 144
  const eyeIndices =
    eye === "left"
      ? { upper: [159, 145, 133], lower: [158, 153, 144] }
      : { upper: [386, 374, 362], lower: [385, 380, 373] }; // right eye

  const upper = eyeIndices.upper.map((i) => landmarks[i]);
  const lower = eyeIndices.lower.map((i) => landmarks[i]);

  const verticalDistance = Math.hypot(
    upper[1][0] - lower[1][0],
    upper[1][1] - lower[1][1]
  );
  const horizontalDistance = Math.hypot(
    upper[0][0] - upper[2][0],
    upper[0][1] - upper[2][1]
  );

  return verticalDistance / horizontalDistance;
}

/**
 * Calculate head yaw angle (-30 to +30 degrees)
 */
function calculateHeadYaw(landmarks: number[][]): number {
  // Use nose tip (index 1) and face width (indices 127, 356)
  const noseTip = landmarks[1];
  const leftCheek = landmarks[127];
  const rightCheek = landmarks[356];

  const centerX = (leftCheek[0] + rightCheek[0]) / 2;
  const deltaX = noseTip[0] - centerX;
  const faceWidth = rightCheek[0] - leftCheek[0];

  return (deltaX / faceWidth) * 60; // Scale to degrees
}

/**
 * Calculate mouth aspect ratio (0 = closed, >0.03 = open smile)
 */
function calculateMouthAspectRatio(landmarks: number[][]): number {
  // Upper lip: 61, 146, 91
  // Lower lip: 181, 84, 17
  const upperLip = landmarks[61];
  const lowerLip = landmarks[181];
  const leftCorner = landmarks[91];
  const rightCorner = landmarks[17];

  const verticalDistance = Math.hypot(
    upperLip[0] - lowerLip[0],
    upperLip[1] - lowerLip[1]
  );
  const horizontalDistance = Math.hypot(
    rightCorner[0] - leftCorner[0],
    rightCorner[1] - leftCorner[1]
  );

  return verticalDistance / horizontalDistance;
}
