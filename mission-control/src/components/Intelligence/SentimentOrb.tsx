import React from 'react';
import { motion } from 'framer-motion';

interface SentimentOrbProps {
  sentiment: 'NEUTRAL' | 'ACTIVE_EXPLOITATION' | 'CRITICAL_THREAT' | 'RESEARCH_HYPE';
  score: number;
}

const SentimentOrb: React.FC<SentimentOrbProps> = ({ sentiment, score }) => {
  const getColor = () => {
    switch (sentiment) {
      case 'CRITICAL_THREAT': return '#FF006E';
      case 'ACTIVE_EXPLOITATION': return '#FF5F00';
      case 'RESEARCH_HYPE': return '#00D9FF';
      default: return '#7B2D8E';
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-4 bg-black/40 border border-white/10 rounded-xl backdrop-blur-md">
      <div className="text-xs font-mono text-white/50 mb-2 uppercase tracking-widest">OSINT Sentiment</div>
      <motion.div
        animate={{
          scale: [1, 1.1, 1],
          opacity: [0.8, 1, 0.8],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut"
        }}
        className="w-16 h-16 rounded-full flex items-center justify-center shadow-lg"
        style={{ 
          background: `radial-gradient(circle, ${getColor()} 0%, transparent 70%)`,
          boxShadow: `0 0 20px ${getColor()}44`
        }}
      >
        <span className="text-xl font-bold text-white">{Math.round(score * 100)}%</span>
      </motion.div>
      <div className="mt-3 text-xs font-bold" style={{ color: getColor() }}>
        {sentiment.replace('_', ' ')}
      </div>
    </div>
  );
};

export default SentimentOrb;
