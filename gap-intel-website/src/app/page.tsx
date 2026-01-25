"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import { motion, useScroll, useTransform, useSpring, useInView } from "framer-motion";
import {
  BarChart3,
  Sparkles,
  Zap,
  TrendingUp,
  Search,
  ArrowRight,
  CheckCircle2,
  PlayCircle,
  Users,
  Clock,
  Youtube,
  MousePointerClick
} from "lucide-react";

// --- Components ---

const FadeIn = ({ children, delay = 0, className = "" }: { children: React.ReactNode, delay?: number, className?: string }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.8, delay, ease: [0.21, 0.47, 0.32, 0.98] }}
      className={className}
    >
      {children}
    </motion.div>
  );
};

const FeatureCard = ({ title, description, icon: Icon, color, className = "", children }: any) => {
  return (
    <motion.div
      whileHover={{ y: -5 }}
      initial={{ opacity: 0, scale: 0.95 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      className={`p-8 rounded-[32px] bg-white border border-slate-100 shadow-xl shadow-slate-200/50 flex flex-col relative group overflow-hidden ${className}`}
    >
      <div className={`absolute top-0 right-0 w-64 h-64 bg-gradient-to-br ${color} opacity-[0.05] rounded-full blur-3xl -mr-32 -mt-32 group-hover:opacity-[0.1] transition-opacity duration-500`} />

      <div className="relative z-10 mb-8">
        <div className="w-12 h-12 rounded-2xl bg-slate-50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 ring-1 ring-slate-100">
          <Icon className="w-6 h-6 text-slate-700" strokeWidth={1.5} />
        </div>
        <h3 className="text-2xl font-serif font-medium text-slate-900 mb-3 tracking-tight">{title}</h3>
        <p className="text-slate-500 leading-relaxed">{description}</p>
      </div>

      {children && (
        <div className="mt-auto relative z-10 rounded-2xl bg-slate-50/50 border border-slate-100/50 overflow-hidden min-h-[180px] flex items-center justify-center group-hover:bg-slate-50 transition-colors">
          {children}
        </div>
      )}
    </motion.div>
  );
};

const StepCard = ({ number, title, description, children }: any) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.7 }}
      className="flex flex-col items-center text-center gap-6 group"
    >
      <div className="relative w-full aspect-[4/3] bg-slate-50 rounded-3xl border border-slate-100 overflow-hidden shadow-sm group-hover:shadow-md transition-shadow">
        {/* Visual Content */}
        <div className="absolute inset-0 flex items-center justify-center">
          {children}
        </div>

        {/* Number Badge */}
        <div className="absolute top-4 left-4 w-10 h-10 rounded-xl bg-white shadow-sm border border-slate-100 flex items-center justify-center text-slate-900 font-bold font-serif z-20">
          {number}
        </div>
      </div>

      <div className="px-4">
        <h3 className="text-xl font-serif font-medium text-slate-900 mb-2">{title}</h3>
        <p className="text-slate-500 text-sm leading-relaxed">{description}</p>
      </div>
    </motion.div>
  );
};

// Floating Icon Component
const FloatingIcon = ({ src, alt, top, left, right, rotate, delay, scale = 1, parallaxY, objectPosition = "object-cover" }: any) => {
  const { scrollYProgress } = useScroll();
  const yTransform = useTransform(scrollYProgress, [0, 1], [0, parallaxY]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 50, rotate: rotate - 10 }}
      animate={{ opacity: 1, y: 0, rotate }}
      style={{ y: yTransform, top, left, right }}
      transition={{ duration: 1, delay, ease: "easeOut" }}
      className="absolute z-0 hidden xl:block pointer-events-none"
    >
      <motion.div
        animate={{ y: [-10, 10, -10], rotate: [rotate - 2, rotate + 2, rotate - 2] }}
        transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 1 }}
        className="relative"
      >
        <div className={`w-20 h-20 rounded-2xl bg-white p-2 shadow-[0_20px_40px_-5px_rgba(0,0,0,0.1)] border border-slate-100 transform hover:scale-110 transition-transform duration-300`} style={{ transform: `scale(${scale})` }}>
          <div className="w-full h-full rounded-xl overflow-hidden bg-slate-50 relative">
            <img src={src} alt={alt} className={`w-full h-full ${objectPosition}`} />
            <div className="absolute inset-0 ring-1 ring-inset ring-black/5 rounded-xl" />
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

const FloatingStat = ({ top, left, right, rotate, delay, children }: any) => {
  const { scrollYProgress } = useScroll();
  const y = useTransform(scrollYProgress, [0, 1], [0, -60]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, rotate: rotate - 5 }}
      animate={{ opacity: 1, y: 0, rotate }}
      style={{ top, left, right, y }}
      transition={{ duration: 0.8, delay }}
      className="absolute z-0 hidden xl:block pointer-events-none"
    >
      <motion.div
        animate={{ y: [-8, 8, -8] }}
        transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
      >
        {children}
      </motion.div>
    </motion.div>
  );
};

// --- Visual Components for Bento Grid ---

const GapVisual = () => (
  <div className="w-full h-full min-h-[180px] p-6 flex flex-col justify-center relative overflow-hidden">
    <motion.div
      animate={{ y: [0, -10, 0] }}
      transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
      className="bg-white p-3 rounded-xl shadow-sm border border-slate-100 mb-3 w-3/4 self-start flex items-center gap-3 relative z-10"
    >
      <div className="w-6 h-6 rounded-full bg-rose-100 flex items-center justify-center text-[10px]">❤️</div>
      <div className="text-xs text-slate-600 font-medium">Pls do a 100 days survival challenge!!</div>
    </motion.div>
    <motion.div
      animate={{ y: [0, -20, 0] }}
      transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 1 }}
      className="bg-white p-3 rounded-xl shadow-sm border border-slate-100 mb-3 w-4/5 self-end flex items-center gap-3 relative z-10"
    >
      <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-[10px]">🔥</div>
      <div className="text-xs text-slate-600 font-medium">We need more hardcore survival...</div>
    </motion.div>
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      whileInView={{
        scale: 1, opacity: 1,
        transition: { duration: 0.5, delay: 0.5 }
      }}
      viewport={{ once: false }}
      transition={{ duration: 0 }}
      className="bg-gradient-to-r from-blue-600 to-indigo-600 p-3 rounded-xl shadow-lg shadow-blue-200 mb-3 w-3/4 self-center flex items-center gap-3 relative z-20"
    >
      <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center text-white text-xs">🚀</div>
      <div className="text-xs font-bold text-white">High Demand: "100 Days"</div>
    </motion.div>
  </div>
);

const ThumbnailVisual = () => (
  <div className="w-full h-full min-h-[180px] flex items-center justify-center relative p-4">
    <div className="relative w-48 h-28 bg-white rounded-lg shadow-md overflow-hidden border border-slate-200 group-hover:scale-105 transition-transform duration-500">
      <div className="absolute inset-0 bg-slate-100" />
      <div className="absolute inset-0">
        <img src="/images/mrbeast_thumb.png" alt="MrBeast Thumbnail" className="w-full h-full object-cover" />
      </div>

      {/* Scanning Line */}
      <motion.div
        animate={{ top: ['0%', '100%', '0%'] }}
        transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
        className="absolute left-0 right-0 h-[2px] bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.5)] z-20"
      />

      {/* Overlay Tags */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        whileInView={{
          opacity: 1, x: 0,
          transition: { delay: 1 }
        }}
        viewport={{ once: false }}
        transition={{ duration: 0 }}
        className="absolute top-2 right-2 bg-green-500 text-white text-[10px] font-bold px-2 py-0.5 rounded shadow-sm z-30"
      >
        CTR 12.4%
      </motion.div>
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        whileInView={{
          opacity: 1, x: 0,
          transition: { delay: 1.2 }
        }}
        viewport={{ once: false }}
        transition={{ duration: 0 }}
        className="absolute bottom-2 left-2 bg-white/90 backdrop-blur text-slate-600 text-[10px] font-bold px-2 py-0.5 rounded border border-slate-100 z-30"
      >
        Emotions: High
      </motion.div>
    </div>
  </div>
);

const VelocityVisual = () => (
  <div className="w-full h-full min-h-[180px] flex items-end justify-center px-10 pb-8 gap-2 relative">
    {[40, 65, 50, 80, 75, 90, 85, 95, 92, 100].map((h, i) => (
      <motion.div
        key={i}
        initial={{ height: 10 }}
        whileInView={{
          height: `${h}%`,
          transition: { duration: 1, delay: i * 0.1, type: "spring" }
        }}
        viewport={{ once: false }}
        transition={{ duration: 0.2 }}
        className={`w-full max-w-[40px] rounded-t-lg relative ${i >= 7 ? 'bg-emerald-500' : 'bg-slate-200'}`}
      >
        {i === 8 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            whileInView={{
              opacity: 1, y: -30,
              transition: { delay: 1.5 }
            }}
            viewport={{ once: false }}
            transition={{ duration: 0 }}
            className="absolute -top-12 left-1/2 -translate-x-1/2 bg-white px-3 py-1.5 rounded-lg shadow-lg border border-emerald-100 whitespace-nowrap z-20"
          >
            <div className="text-xs font-bold text-emerald-600">Viral Spike</div>
            <div className="absolute bottom-[-6px] left-1/2 -translate-x-1/2 w-3 h-3 bg-white rotate-45 border-b border-r border-emerald-100" />
          </motion.div>
        )}
      </motion.div>
    ))}
    {/* Dashed line overlay */}
    <div className="absolute inset-0 pointer-events-none">
      <svg className="w-full h-full" overflow="visible">
        <motion.path
          d="M 40 160 C 100 120, 200 140, 300 80 S 500 20, 600 10"
          fill="none"
          stroke="#10b981"
          strokeWidth="3"
          strokeDasharray="8 8"
          initial={{ pathLength: 0 }}
          whileInView={{
            pathLength: 1,
            transition: { duration: 2, delay: 1 }
          }}
          viewport={{ once: false }}
          transition={{ duration: 0 }}
        />
      </svg>
    </div>
  </div>
);

const StepSearchVisual = () => (
  <div className="w-full h-full flex items-center justify-center bg-slate-50 relative overflow-hidden">
    <motion.div
      initial={{ width: "40%" }}
      whileInView={{
        width: "70%",
        transition: { duration: 1.5, ease: "easeInOut", delay: 0.2 }
      }}
      viewport={{ once: false }}
      transition={{ duration: 0.5 }}
      className="h-10 bg-white rounded-full shadow-sm border border-slate-200 flex items-center px-4 gap-3 relative z-10"
    >
      <div className="w-4 h-4 rounded-full border-2 border-slate-300 shrink-0" />
      <motion.div
        initial={{ width: 0, opacity: 0 }}
        whileInView={{
          width: "auto", opacity: 1,
          transition: { duration: 1.5, delay: 0.8, ease: "linear" }
        }}
        viewport={{ once: false }}
        transition={{ duration: 0 }}
        className="overflow-hidden whitespace-nowrap font-medium text-slate-700 text-sm"
      >
        @MrBeast
      </motion.div>
      <motion.div
        animate={{ opacity: [0, 1, 0] }}
        transition={{ duration: 0.8, repeat: Infinity }}
        className="w-0.5 h-4 bg-blue-500 ml-auto"
      />
    </motion.div>
    {/* Hand Cursor */}
    <motion.div
      initial={{ x: 100, y: 100, opacity: 0 }}
      whileInView={{
        x: 30, y: 30, opacity: 1,
        transition: { duration: 1, delay: 1 }
      }}
      viewport={{ once: false }}
      transition={{ duration: 0 }}
      className="absolute z-20"
    >
      <div className="w-8 h-8 bg-slate-900 rounded-full rounded-tl-none -rotate-12 shadow-xl border-2 border-white" />
    </motion.div>
  </div>
);

const StepAnalysisVisual = () => (
  <div className="w-full h-full flex items-center justify-center bg-slate-50 relative overflow-hidden">
    {/* Radar Scan */}
    <motion.div
      className="absolute w-[200%] h-[200%] bg-[conic-gradient(from_0deg,transparent_0deg,transparent_270deg,rgba(99,102,241,0.1)_360deg)]"
      animate={{ rotate: 360 }}
      transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
    />

    {/* Concentric Circles */}
    <div className="absolute inset-0 flex items-center justify-center opacity-30">
      <div className="w-32 h-32 border border-indigo-200 rounded-full absolute" />
      <div className="w-48 h-48 border border-indigo-100 rounded-full absolute border-dashed" />
    </div>

    {/* Central AI Hub */}
    <div className="relative z-10 w-16 h-16 bg-white rounded-2xl shadow-[0_0_40px_-5px_rgba(99,102,241,0.4)] flex items-center justify-center border border-indigo-100">
      <motion.div
        className="text-3xl"
        animate={{ scale: [1, 1.2, 1] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        ✨
      </motion.div>
    </div>

    {/* Floating Data Particles */}
    {[0, 1, 2, 3, 4].map((i) => (
      <motion.div
        key={i}
        className="absolute w-2 h-2 bg-indigo-500 rounded-full shadow-lg shadow-indigo-500/50"
        initial={{ opacity: 0, scale: 0 }}
        animate={{
          x: [0, 50],
          y: [0, 50],
          opacity: [1, 0],
          scale: [1, 0]
        }}
        transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.3, ease: "easeOut" }}
      />
    ))}
  </div>
);

const StepReportVisual = () => (
  <div className="w-full h-full flex items-center justify-center bg-slate-50 relative p-8">
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      whileInView={{
        scale: 1, opacity: 1,
        transition: { type: "spring", delay: 0.2 }
      }}
      viewport={{ once: false }}
      transition={{ duration: 0.2 }}
      className="w-full h-full bg-white rounded-xl shadow-md border border-slate-100 flex flex-col p-3 gap-2 relative z-10"
    >
      <div className="flex gap-3 mb-2 items-center">
        <div className="w-10 h-10 rounded-full border border-slate-200 overflow-hidden shrink-0">
          <img src="/tjr-profile.jpg" alt="TJR" className="w-full h-full object-cover" />
        </div>
        <div>
          <div className="text-sm font-bold text-slate-900">TJRTrades</div>
          <div className="text-[10px] text-slate-500 font-medium">@tjrtrades</div>
        </div>
      </div>
      <div className="flex-1 bg-slate-50 rounded-lg flex items-end justify-around pb-2 px-2 gap-1">
        <div className="w-4 h-8 bg-slate-200 rounded-t-sm" />
        <div className="w-4 h-12 bg-blue-400 rounded-t-sm" />
        <div className="w-4 h-6 bg-slate-200 rounded-t-sm" />
        <div className="w-4 h-10 bg-slate-200 rounded-t-sm" />
      </div>
    </motion.div>
    {/* Checkmark Badge */}
    <motion.div
      initial={{ scale: 0, rotate: -45 }}
      whileInView={{
        scale: 1, rotate: 0,
        transition: { type: "spring", delay: 0.6 }
      }}
      viewport={{ once: false }}
      transition={{ duration: 0 }}
      className="absolute bottom-6 right-6 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center shadow-lg border-2 border-white z-20"
    >
      <div className="w-2.5 h-4 border-b-2 border-r-2 border-white rotate-45 mb-1" />
    </motion.div>
  </div>
);

const CTAVisual = () => (
  <div className="relative w-full h-[300px] flex items-center justify-center">
    <div className="absolute inset-0 bg-gradient-to-br from-blue-50/50 to-purple-50/50 rounded-3xl" />
    <motion.div
      className="bg-white p-8 rounded-3xl shadow-2xl shadow-slate-200/50 border border-slate-100 flex flex-col gap-6 w-72 items-center relative z-10"
      animate={{ y: [-10, 10, -10] }}
      transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
    >
      <div className="w-20 h-20 rounded-full bg-emerald-50 flex items-center justify-center text-4xl shadow-inner shadow-emerald-100">🚀</div>
      <div className="text-center w-full">
        <div className="text-slate-500 text-sm font-medium mb-1">Viral Probability</div>
        <motion.div
          className="text-5xl font-bold text-slate-900 tracking-tight"
          initial={{ scale: 0.5, opacity: 0 }}
          whileInView={{
            scale: 1, opacity: 1,
            transition: { type: "spring" }
          }}
          viewport={{ once: false }}
          transition={{ duration: 0 }}
        >
          98%
        </motion.div>
      </div>
      <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-emerald-400 to-emerald-500"
          initial={{ width: 0 }}
          whileInView={{
            width: "98%",
            transition: { duration: 1.5, ease: "easeOut", delay: 0.2 }
          }}
          viewport={{ once: false }}
          transition={{ duration: 0 }}
        />
      </div>
    </motion.div>
  </div>
);

export default function Home() {
  const { user } = useAuth();
  const { scrollYProgress } = useScroll();
  const y = useTransform(scrollYProgress, [0, 1], [0, -100]);

  return (
    <div className="min-h-screen bg-[#FAFAFA] text-slate-900 overflow-x-hidden selection:bg-blue-100 selection:text-blue-900">
      <Navbar />

      {/* --- HERO SECTION --- */}
      <section className="relative pt-24 pb-16 md:pt-32 lg:pt-48 md:pb-20 lg:pb-32 px-4 md:px-6 overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 opacity-40 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[radial-gradient(circle_at_center,_var(--color-brand-light)_0%,_transparent_70%)] blur-[100px] opacity-20" />
        </div>

        {/* Floating Creator Icons - Parallax & Animated */}
        <FloatingIcon
          src="/images/ishowspeed.jpg"
          alt="IShowSpeed"
          top="12%"
          left="4%"
          rotate={-12}
          delay={0.5}
          scale={1.2}
          parallaxY={-40}
          objectPosition="object-top object-cover"
        />

        <FloatingIcon
          src="/images/mrbeast.png"
          alt="MrBeast"
          top="18%"
          right="4%"
          rotate={12}
          delay={0.7}
          scale={1.3}
          parallaxY={-60}
        />
        <FloatingIcon
          src="/images/pewdiepie.png"
          alt="PewDiePie"
          top="55%"
          left="2%"
          rotate={6}
          delay={0.9}
          scale={1.1}
          parallaxY={-80}
        />
        <FloatingIcon
          src="/images/mkbhd.png"
          alt="MKBHD"
          top="62%"
          right="2%"
          rotate={-8}
          delay={1.1}
          scale={1.1}
          parallaxY={-30}
        />

        {/* Floating Stats */}
        <FloatingStat top="30%" left="8%" rotate={-6} delay={0.4}>
          <div className="bg-white px-4 py-3 rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.08)] border border-slate-100 flex items-center gap-3 transform hover:scale-105 transition-transform">
            <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-600">
              <TrendingUp size={18} strokeWidth={2.5} />
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Predicted Views</div>
              <div className="text-sm font-bold text-slate-900">+124%</div>
            </div>
          </div>
        </FloatingStat>

        <FloatingStat top="45%" right="10%" rotate={6} delay={0.6}>
          <div className="bg-white px-4 py-3 rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.08)] border border-slate-100 flex items-center gap-3 transform hover:scale-105 transition-transform">
            <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600">
              <MousePointerClick size={18} strokeWidth={2.5} />
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Click Rate</div>
              <div className="text-sm font-bold text-slate-900">15.2%</div>
            </div>
          </div>
        </FloatingStat>

        {/* New Additional Stats */}
        <FloatingStat top="60%" left="6%" rotate={8} delay={0.8}>
          <div className="bg-white px-4 py-3 rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.08)] border border-slate-100 flex items-center gap-3 transform hover:scale-105 transition-transform">
            <div className="w-8 h-8 rounded-lg bg-orange-100 flex items-center justify-center text-orange-600">
              <Clock size={18} strokeWidth={2.5} />
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Retention</div>
              <div className="text-sm font-bold text-slate-900">&gt; 60%</div>
            </div>
          </div>
        </FloatingStat>

        <FloatingStat top="25%" right="15%" rotate={-4} delay={1.0}>
          <div className="bg-white px-4 py-3 rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.08)] border border-slate-100 flex items-center gap-3 transform hover:scale-105 transition-transform">
            <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center text-purple-600">
              <Zap size={18} strokeWidth={2.5} />
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Viral Score</div>
              <div className="text-sm font-bold text-slate-900">9.8/10</div>
            </div>
          </div>
        </FloatingStat>

        <FloatingStat top="75%" right="8%" rotate={-8} delay={1.2}>
          <div className="bg-white px-4 py-3 rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.08)] border border-slate-100 flex items-center gap-3 transform hover:scale-105 transition-transform">
            <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-600">
              <Users size={18} strokeWidth={2.5} />
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Subscribers</div>
              <div className="text-sm font-bold text-slate-900">+12.4K</div>
            </div>
          </div>
        </FloatingStat>

        <div className="max-w-4xl mx-auto text-center relative z-10">

          <FadeIn>
            <motion.div
              animate={{ y: [-8, 8, -8] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              className="mb-8 inline-block relative z-10"
            >
              <div className="w-32 h-32 md:w-48 md:h-48 bg-white rounded-[2rem] shadow-[0_8px_30px_rgb(0,0,0,0.1)] border border-slate-100 flex items-center justify-center transform hover:scale-110 transition-transform duration-300">
                <img src="/images/youtube-logo.png" alt="YouTube" className="w-16 h-16 md:w-24 md:h-24 object-contain" />
              </div>
            </motion.div>
          </FadeIn>

          <FadeIn delay={0.1}>
            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl xl:text-8xl font-serif font-medium tracking-tight leading-[1.1] md:leading-[1] text-slate-900 mb-6 md:mb-8">
              <span className="block">Data-Driven</span>
              <span className="block text-slate-400 italic">Edge over Competitors</span>
            </h1>
          </FadeIn>

          <FadeIn delay={0.2}>
            {/* GAP Intel Value Prop */}
            <p className="text-base md:text-xl text-slate-500 max-w-2xl mx-auto mb-8 md:mb-12 leading-relaxed px-2">
              GAP Intel uses advanced AI to uncover YouTube content gaps, predict view velocity,
              and optimize thumbnails before you even hit record.
            </p>
          </FadeIn>

          <FadeIn delay={0.3}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
              <Link href={user ? "/dashboard" : "/pricing"} className="w-full sm:w-auto">
                <button className="w-full sm:w-auto h-12 sm:h-14 px-6 sm:px-8 rounded-full bg-[#1c1c1e] text-white text-base sm:text-lg font-medium hover:scale-105 hover:shadow-2xl transition-all duration-300 flex items-center justify-center gap-2 group">
                  Start Analysis
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </button>
              </Link>
              <Link href="/report/GAP-o0frkH6UHVIG" className="w-full sm:w-auto">
                <button className="w-full sm:w-auto h-12 sm:h-14 px-6 sm:px-8 rounded-full bg-white text-slate-900 border border-slate-200 text-base sm:text-lg font-medium hover:bg-slate-50 transition-colors">
                  View Sample Report
                </button>
              </Link>
            </div>
            <p className="mt-4 text-xs sm:text-sm text-slate-400">No credit card required for starter analysis</p>
          </FadeIn>
        </div>

        {/* Floating UI Mockup */}
        <motion.div
          initial={{ opacity: 0, rotateX: 20, y: 100 }}
          animate={{ opacity: 1, rotateX: 0, y: 0 }}
          transition={{ duration: 1.2, ease: "easeOut", delay: 0.4 }}
          style={{ perspective: 1000 }}
          className="mt-20 max-w-5xl mx-auto relative z-20 hidden md:block"
        >
          <div className="relative rounded-[2rem] shadow-[0_50px_100px_-20px_rgba(50,50,93,0.15)] bg-white border border-slate-200/60 p-2">
            <div className="absolute inset-0 bg-gradient-to-tr from-blue-50/50 via-purple-50/30 to-rose-50/50 rounded-[2rem]" />
            <div className="relative rounded-3xl overflow-hidden bg-white border border-slate-100">
              {/* Mock Dashboard UI */}
              <div className="flex h-[600px]">
                {/* Sidebar Mock */}
                <div className="w-64 border-r border-slate-100 bg-slate-50/50 p-6 flex flex-col gap-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="relative w-10 h-10 rounded-full overflow-hidden border border-slate-200">
                      <img src="/tjr-profile.jpg" alt="TJR" className="object-cover w-full h-full" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-slate-900">TJRTrades</div>
                      <div className="text-xs text-slate-500">@tjrtrades</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-3 px-3 py-2 bg-white rounded-lg border border-slate-200 shadow-sm text-sm font-medium text-slate-900">
                      <div className="w-2 h-2 rounded-full bg-blue-500" /> Dashboard
                    </div>
                    <div className="flex items-center gap-3 px-3 py-2 text-sm font-medium text-slate-500 hover:text-slate-900">
                      <div className="w-2 h-2 rounded-full bg-slate-300" /> Reports
                    </div>
                    <div className="flex items-center gap-3 px-3 py-2 text-sm font-medium text-slate-500 hover:text-slate-900">
                      <div className="w-2 h-2 rounded-full bg-slate-300" /> Analysis
                    </div>
                    <div className="flex items-center gap-3 px-3 py-2 text-sm font-medium text-slate-500 hover:text-slate-900">
                      <div className="w-2 h-2 rounded-full bg-slate-300" /> Settings
                    </div>
                  </div>

                  <div className="mt-auto bg-blue-900 rounded-xl p-4 text-white relative overflow-hidden">
                    <div className="relative z-10">
                      <div className="text-xs font-medium text-blue-200 mb-1">Pro Plan</div>
                      <div className="text-sm font-bold mb-3">20/25 Reports</div>
                      <div className="h-1.5 w-full bg-blue-800 rounded-full overflow-hidden">
                        <div className="h-full w-4/5 bg-blue-400" />
                      </div>
                    </div>
                  </div>
                </div>
                {/* Content Mock */}
                <div className="flex-1 p-8 bg-white/50 backdrop-blur-3xl">
                  <div className="flex justify-between items-center mb-10">
                    <div>
                      <h3 className="text-2xl font-serif font-medium text-slate-900">Welcome back, TJR</h3>
                      <p className="text-slate-500 text-sm">Here is what's happening with your channel today.</p>
                    </div>
                    <div className="flex gap-3">
                      <div className="px-4 py-2 bg-slate-900 rounded-full text-white text-sm font-medium shadow-lg shadow-slate-900/10">Create New Report</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-6 mb-8">
                    <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center text-blue-600 font-bold text-xs"><TrendingUp size={16} /></div>
                        <span className="text-sm text-slate-500 font-medium">Avg Views</span>
                      </div>
                      <div className="text-2xl font-bold text-slate-900">42.5K</div>
                      <div className="text-xs text-green-600 font-medium mt-1">+12% vs last month</div>
                    </div>
                    <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-full bg-purple-50 flex items-center justify-center text-purple-600 font-bold text-xs"><CheckCircle2 size={16} /></div>
                        <span className="text-sm text-slate-500 font-medium">Content Gaps</span>
                      </div>
                      <div className="text-2xl font-bold text-slate-900">7 Found</div>
                      <div className="text-xs text-slate-500 font-medium mt-1">In last analysis</div>
                    </div>
                    <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-full bg-orange-50 flex items-center justify-center text-orange-600 font-bold text-xs"><Sparkles size={16} /></div>
                        <span className="text-sm text-slate-500 font-medium">Thumbnails</span>
                      </div>
                      <div className="text-2xl font-bold text-slate-900">92/100</div>
                      <div className="text-xs text-green-600 font-medium mt-1">Excellent Score</div>
                    </div>
                  </div>

                  <div className="h-64 rounded-3xl bg-slate-50 border border-slate-100 p-6 relative overflow-hidden">
                    <div className="flex justify-between mb-6 relative z-10">
                      <div>
                        <h4 className="font-bold text-slate-900">Engagement Velocity</h4>
                        <p className="text-xs text-slate-500">Last 30 days performance</p>
                      </div>
                    </div>
                    <div className="flex items-end gap-3 h-40 relative z-10">
                      {[35, 45, 40, 60, 55, 75, 65, 85, 80, 70, 90, 95].map((h, i) => (
                        <motion.div
                          key={i}
                          initial={{ height: 0 }}
                          whileInView={{ height: `${h}%` }}
                          transition={{ duration: 0.8, delay: i * 0.05 }}
                          className={`flex-1 rounded-t-lg opacity-90 hover:opacity-100 transition-opacity ${i === 11 ? 'bg-blue-600' : 'bg-slate-300'}`}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            {/* Floating Elements on Mockup */}

          </div>
        </motion.div>
      </section>

      {/* --- FEATURES GRID --- */}
      <section className="py-16 md:py-32 px-4 md:px-6">
        <div className="max-w-7xl mx-auto">
          <FadeIn className="text-center mb-12 md:mb-20">
            <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-serif font-medium text-slate-900 mb-4 md:mb-6">
              Four ways we accelerate <br className="hidden sm:block" /> your channel growth
            </h2>
          </FadeIn>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <FeatureCard
              title="Content Gap Detection"
              description="Identify high-demand topics that your competitors are missing. Our AI scans thousands of comments to find what viewers are actually begging for."
              icon={Search}
              color="from-blue-200 to-indigo-100"
              className="md:col-span-1"
            >
              <GapVisual />
            </FeatureCard>

            <FeatureCard
              title="Thumbnail Optimization"
              description="Upload your thumbnail before publishing. Gemini Vision AI analyzes color balance, face emotion, and text legibility to predict CTR."
              icon={Sparkles}
              color="from-purple-200 to-fuchsia-100"
              className="md:col-span-1"
            >
              <ThumbnailVisual />
            </FeatureCard>

            <FeatureCard
              title="View Velocity Prediction"
              description="Stop guessing. We forecast the potential 7-day view count of your video ideas based on historical channel performance and current trends."
              icon={TrendingUp}
              color="from-emerald-200 to-green-100"
              className="md:col-span-2"
            >
              <VelocityVisual />
            </FeatureCard>
          </div>
        </div>
      </section>

      {/* --- STEPS SECTION --- */}
      <section className="py-16 md:py-32 bg-white border-y border-slate-100">
        <div className="max-w-7xl mx-auto px-4 md:px-6">
          <FadeIn className="text-center mb-12 md:mb-20">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-serif font-medium text-slate-900 mb-3 md:mb-4">Analysis in 3 simple steps</h2>
            <p className="text-slate-500 text-sm md:text-base">From idea to fully optimized video plan in seconds.</p>
          </FadeIn>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-16 relative">
            {/* Connecting Line (Desktop) */}
            <div className="absolute top-10 left-[16%] right-[16%] h-[1px] bg-gradient-to-r from-transparent via-slate-200 to-transparent hidden md:block" />

            <StepCard
              number="1"
              title="Paste Channel URL"
              description="Enter your channel or a competitor's handle. We instantly fetch the latest upload data."
            >
              <StepSearchVisual />
            </StepCard>
            <StepCard
              number="2"
              title="AI Analysis"
              description="Our engines process transcripts, thumbnails, and comments to find patterns."
            >
              <StepAnalysisVisual />
            </StepCard>
            <StepCard
              number="3"
              title="Get The Report"
              description="Receive a comprehensive strategy document with ready-to-film video ideas."
            >
              <StepReportVisual />
            </StepCard>
          </div>
        </div>
      </section>

      {/* --- CTA SECTION --- */}
      <section className="py-32 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            className="bg-white rounded-[3rem] p-8 md:p-12 shadow-2xl shadow-slate-200/50 border border-slate-100 overflow-hidden relative"
          >
            <div className="grid md:grid-cols-2 gap-12 items-center relative z-10">
              <div className="text-left md:pl-8">
                <h2 className="text-4xl md:text-5xl font-serif font-medium text-slate-900 mb-6 leading-tight">
                  Ready to find your next <span className="text-blue-600">viral video?</span>
                </h2>
                <p className="text-slate-500 text-lg mb-8 max-w-md">
                  Join smart creators using data instead of luck.
                  Start your free analysis today and stop guessing.
                </p>
                <Link href="/pricing">
                  <button className="h-14 px-8 rounded-full bg-slate-900 text-white text-lg font-medium hover:scale-105 hover:bg-slate-800 transition-all duration-300 shadow-lg shadow-slate-900/20">
                    Get Started for Free
                  </button>
                </Link>
              </div>

              <div className="relative">
                <CTAVisual />
              </div>
            </div>

            {/* Background Gradients */}
            <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-gradient-to-b from-blue-50 to-transparent rounded-full blur-3xl opacity-50 -mr-20 -mt-20 -z-10" />
            <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-gradient-to-t from-purple-50 to-transparent rounded-full blur-3xl opacity-50 -ml-20 -mb-20 -z-10" />
          </motion.div>
        </div>
      </section>

      {/* --- FOOTER --- */}
      <footer className="py-12 px-6 border-t border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white font-serif font-bold">G</div>
            <span className="font-serif text-xl font-medium tracking-tight">GAP Intel</span>
          </div>
          <div className="flex gap-8 text-sm text-slate-500 font-medium">
            <Link href="/pricing" className="hover:text-slate-900 transition-colors">Pricing</Link>
            <Link href="/dashboard" className="hover:text-slate-900 transition-colors">Login</Link>
            <Link href="#" className="hover:text-slate-900 transition-colors">Legal</Link>
          </div>
          <div className="text-sm text-slate-400">
            © 2024 GAP Intel. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
