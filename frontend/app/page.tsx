'use client';

import { useHealthStatus } from '@/hooks/useHealthStatus';
import { motion } from 'framer-motion';
import { CheckCircle, AlertCircle, Loader } from 'lucide-react';

export default function Home() {
  const { isConnected, message, isLoading } = useHealthStatus();

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center"
      >
        <motion.h1
          className="text-4xl font-bold text-slate-900 mb-8"
          initial={{ scale: 0.9 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, duration: 0.3 }}
        >
          TrueHire AI
        </motion.h1>

        <motion.div
          className="flex justify-center mb-6"
          animate={{ rotate: isLoading ? 360 : 0 }}
          transition={{ repeat: isLoading ? Infinity : 0, duration: 1 }}
        >
          {isLoading && (
            <Loader className="w-12 h-12 text-blue-500" />
          )}
          {!isLoading && isConnected && (
            <CheckCircle className="w-12 h-12 text-green-500" />
          )}
          {!isLoading && !isConnected && (
            <AlertCircle className="w-12 h-12 text-red-500" />
          )}
        </motion.div>

        <motion.p
          className={`text-lg font-semibold ${
            isConnected ? 'text-green-600' : 'text-red-600'
          }`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          {message}
        </motion.p>

        <motion.p
          className="text-sm text-slate-500 mt-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
        >
          AI-powered reverse-interview platform
        </motion.p>
      </motion.div>
    </main>
  );
}
