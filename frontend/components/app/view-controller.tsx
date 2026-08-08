'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { MoneyBuddySessionView } from '@/components/moneybuddy/session-view';
import { CallEndedView } from '@/components/moneybuddy/call-ended-view';
import { MicPermission } from '@/components/moneybuddy/mic-permission';
import { WelcomeView } from '@/components/app/welcome-view';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(MoneyBuddySessionView);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: { opacity: 1 },
    hidden: { opacity: 0 },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: { duration: 0.5, ease: 'linear' },
};

type ViewState = 'welcome' | 'session' | 'ended' | 'mic-denied';

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, start } = useSessionContext();
  const { resolvedTheme } = useTheme();
  const [viewState, setViewState] = useState<ViewState>('welcome');
  const [micDenied, setMicDenied] = useState(false);
  const [messageCount, setMessageCount] = useState(0);
  const wasConnectedRef = useRef(false);
  const messageCountRef = useRef(0);

  // Track connection state changes
  useEffect(() => {
    if (isConnected) {
      wasConnectedRef.current = true;
      setViewState('session');
      setMicDenied(false);
    } else if (wasConnectedRef.current) {
      // Was connected, now disconnected → call ended
      setViewState('ended');
      setMessageCount(messageCountRef.current);
    }
  }, [isConnected]);

  // Handle mic permission check + start
  const handleStart = useCallback(async () => {
    try {
      // Check microphone permission first
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
      setMicDenied(false);
      start();
      setViewState('session'); // Transition immediately to show connecting state
    } catch {
      setMicDenied(true);
      setViewState('mic-denied');
    }
  }, [start]);

  const handleRetryMic = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
      setMicDenied(false);
      setViewState('welcome');
      start();
    } catch {
      // Still denied
      setMicDenied(true);
    }
  }, [start]);

  const handleRestart = useCallback(() => {
    wasConnectedRef.current = false;
    messageCountRef.current = 0;
    setViewState('welcome');
  }, []);

  // Determine what to show
  const currentView = micDenied ? 'mic-denied' : viewState;

  return (
    <AnimatePresence mode="wait">
      {/* Welcome view */}
      {currentView === 'welcome' && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={handleStart}
        />
      )}

      {/* Session view */}
      {currentView === 'session' && (
        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}
          audioVisualizerType={appConfig.audioVisualizerType}
          audioVisualizerColor={
            resolvedTheme === 'dark'
              ? appConfig.audioVisualizerColorDark
              : appConfig.audioVisualizerColor
          }
          audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
          audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
          audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
          audioVisualizerGridColumnCount={appConfig.audioVisualizerGridColumnCount}
          audioVisualizerRadialBarCount={appConfig.audioVisualizerRadialBarCount}
          audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
          audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
          className="fixed inset-0"
        />
      )}

      {/* Call ended view */}
      {currentView === 'ended' && (
        <motion.div key="ended" {...VIEW_MOTION_PROPS}>
          <CallEndedView
            messageCount={messageCount}
            onRestart={handleRestart}
          />
        </motion.div>
      )}

      {/* Mic permission denied */}
      {currentView === 'mic-denied' && (
        <motion.div key="mic-denied" {...VIEW_MOTION_PROPS}>
          <MicPermission onRetry={handleRetryMic} />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
