'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence, type MotionProps } from 'motion/react';
import { useAgent, useSessionContext, useSessionMessages, useLocalParticipant } from '@livekit/components-react';
import { Landmark } from 'lucide-react';
import { useLanguage } from '@/hooks/useLanguage';
import { MoneyBuddyAvatar } from '@/components/moneybuddy/avatar';
import { StateIndicator, type CustomAgentState } from '@/components/moneybuddy/state-indicator';
import { TranscriptPanel } from '@/components/moneybuddy/transcript-panel';
import { TrustBanner } from '@/components/moneybuddy/trust-banner';
import {
  AgentControlBar,
  type AgentControlBarControls,
} from '@/components/agents-ui/agent-control-bar';
import { AudioVisualizer } from '@/components/agents-ui/blocks/agent-session-view-01/components/audio-visualizer';
import { cn } from '@/lib/shadcn/utils';

const SESSION_MOTION: MotionProps = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: { duration: 0.5, ease: 'easeOut' },
};

const CONTROLS_MOTION: MotionProps = {
  variants: {
    visible: { opacity: 1, translateY: '0%' },
    hidden: { opacity: 0, translateY: '100%' },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: { duration: 0.3, delay: 0.5, ease: 'easeOut' },
};

export interface MoneyBuddySessionViewProps {
  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;
  className?: string;
}

export function MoneyBuddySessionView({
  audioVisualizerType = 'wave',
  audioVisualizerColor,
  audioVisualizerColorShift,
  audioVisualizerBarCount,
  audioVisualizerGridRowCount,
  audioVisualizerGridColumnCount,
  audioVisualizerRadialBarCount,
  audioVisualizerRadialRadius,
  audioVisualizerWaveLineWidth,
  ref,
  className,
  ...props
}: React.ComponentProps<'section'> & MoneyBuddySessionViewProps) {
  const { t } = useLanguage();
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);
  const { state: agentState, attributes: agentAttributes } = useAgent();
  const { isMicrophoneEnabled } = useLocalParticipant();
  const [chatOpen] = useState(true); // Transcript always visible in MoneyBuddy

  // Detect whether Government Scheme Specialist is active
  const isSpecialistActive = agentAttributes?.active_agent === 'specialist';

  // Determine exactly what state to show based on connection lifecycle and mic priority
  const isAgentConnecting = !session.isConnected || agentState === 'disconnected';

  let displayState: CustomAgentState = agentState as CustomAgentState;
  
  if (isAgentConnecting) {
    displayState = 'connecting';
  } else if (agentState === 'speaking') {
    displayState = 'speaking';
  } else if (!isMicrophoneEnabled) {
    displayState = 'mic-off';
  } else {
    displayState = agentState as CustomAgentState;
  }

  const controls: AgentControlBarControls = {
    leave: true,
    microphone: true,
    chat: true,
    camera: false,
    screenShare: false,
  };

  return (
    <section
      ref={ref}
      className={cn(
        'bg-background relative z-10 h-full w-full overflow-hidden',
        className
      )}
      {...props}
    >
      {/* Desktop: Side-by-side layout | Mobile: Stacked */}
      <div className="flex h-full flex-col md:flex-row">
        {/* Left / Top: Voice experience */}
        <div className="relative flex flex-col items-center justify-center md:w-[55%] lg:w-[60%] min-h-[45vh] md:min-h-0">
          {/* Avatar */}
          <motion.div
            {...SESSION_MOTION}
            transition={{ ...SESSION_MOTION.transition, delay: 0.1 }}
            className="flex flex-col items-center gap-5"
          >
            <MoneyBuddyAvatar state={displayState} size="lg" />

            {/* State indicator */}
            <StateIndicator state={displayState} />

            {/* Active Specialist Badge */}
            <AnimatePresence>
              {isSpecialistActive && (
                <motion.div
                  initial={{ opacity: 0, y: -4, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -4, scale: 0.95 }}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-xs font-semibold text-emerald-600 dark:text-emerald-400 shadow-sm"
                >
                  <Landmark className="h-3.5 w-3.5" />
                  <span>{t('specialist.badge')}</span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Explainer Texts */}
            <AnimatePresence mode="wait">
              {displayState === 'connecting' && (
                <motion.div 
                  key="connecting"
                  initial={{ opacity: 0, y: -5 }} 
                  animate={{ opacity: 1, y: 0 }} 
                  exit={{ opacity: 0, y: -5 }}
                  className="text-sm font-medium text-amber-600 dark:text-amber-400/90 tracking-wide"
                >
                  Please wait while we connect you.
                </motion.div>
              )}
              {displayState === 'mic-off' && (
                <motion.div 
                  key="mic-off"
                  initial={{ opacity: 0, y: -5 }} 
                  animate={{ opacity: 1, y: 0 }} 
                  exit={{ opacity: 0, y: -5 }}
                  className="text-sm font-medium text-destructive dark:text-red-400 tracking-wide"
                >
                  Microphone is off. Turn on your microphone to continue.
                </motion.div>
              )}
            </AnimatePresence>

            {/* Audio Visualizer */}
            <div className="relative h-[80px] w-full max-w-xs">
              <AudioVisualizer
                audioVisualizerType={audioVisualizerType}
                audioVisualizerColor={audioVisualizerColor}
                audioVisualizerColorShift={audioVisualizerColorShift}
                audioVisualizerBarCount={audioVisualizerBarCount}
                audioVisualizerRadialBarCount={audioVisualizerRadialBarCount}
                audioVisualizerRadialRadius={audioVisualizerRadialRadius}
                audioVisualizerGridRowCount={audioVisualizerGridRowCount}
                audioVisualizerGridColumnCount={audioVisualizerGridColumnCount}
                audioVisualizerWaveLineWidth={audioVisualizerWaveLineWidth}
                isChatOpen={false}
                className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-background"
                style={{ color: audioVisualizerColor }}
                initial={{ scale: 1 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </motion.div>

          {/* Trust banner — visible on session */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2, duration: 0.5 }}
            className="absolute bottom-24 md:bottom-28 left-0 right-0 flex justify-center px-4"
          >
            <TrustBanner variant="session" className="max-w-xs" />
          </motion.div>

          {/* Controls — fixed at bottom of left panel */}
          <motion.div
            {...CONTROLS_MOTION}
            className="absolute bottom-3 left-3 right-3 z-50 md:bottom-6 md:left-6 md:right-6"
          >
            <div className="mx-auto max-w-sm">
              <AgentControlBar
                variant="livekit"
                controls={controls}
                isChatOpen={false}
                isConnected={session.isConnected}
                onDisconnect={session.end}
              />
            </div>
          </motion.div>
        </div>

        {/* Right / Bottom: Transcript panel */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4, duration: 0.5, ease: 'easeOut' }}
          className={cn(
            'flex-1 md:w-[45%] lg:w-[40%]',
            'p-3 md:py-4 md:pr-4 md:pl-0',
            'min-h-[30vh] md:min-h-0'
          )}
        >
          <TranscriptPanel
            messages={messages}
            agentState={agentState}
            className="h-full"
          />
        </motion.div>
      </div>
    </section>
  );
}
