import React, { useEffect, useState } from "react";

export default function WelcomePage({ onEnter }) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(id);
  }, []);
  return (
    <main
      className={`relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-950 px-5 py-12 text-white transition-all duration-700 ${visible ? "opacity-100" : "opacity-0"}`}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(37,99,235,.35),transparent_34%),radial-gradient(circle_at_80%_80%,rgba(14,165,233,.2),transparent_35%)]" />
      <div className="absolute left-10 top-16 h-32 w-32 animate-pulse rounded-full bg-brand-500/20 blur-3xl" />
      <div className="absolute bottom-10 right-10 h-48 w-48 animate-pulse rounded-full bg-cyan-400/10 blur-3xl" />
      <section className="relative z-10 w-full max-w-4xl text-center">
        <div className="mx-auto mb-7 flex h-20 w-20 animate-bounce items-center justify-center rounded-3xl bg-white/10 text-4xl shadow-2xl ring-1 ring-white/20">
          ⚠️
        </div>
        <p className="mb-4 text-sm font-bold uppercase tracking-[.3em] text-blue-300">
          GIDS · Disaster intelligence
        </p>
        <h1 className="text-4xl font-black tracking-tight sm:text-6xl">
          Safer decisions when every minute matters.
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-base leading-8 text-slate-300 sm:text-lg">
          Identify affected communities, evaluate safe shelters, and generate a
          ranked evacuation plan from one clear operational dashboard.
        </p>
        <div className="mx-auto mt-10 grid max-w-2xl grid-cols-1 gap-3 text-left sm:grid-cols-3">
          <Feature
            icon="◉"
            title="Analyze"
            text="Population and radius analysis"
          />
          <Feature
            icon="⌖"
            title="Locate"
            text="Shelters on an interactive map"
          />
          <Feature
            icon="✓"
            title="Act"
            text="Ranked, actionable recommendations"
          />
        </div>
        <button
          onClick={onEnter}
          className="mt-10 rounded-2xl bg-white px-7 py-3.5 text-sm font-black text-slate-900 shadow-xl shadow-blue-950/30 transition hover:-translate-y-1 hover:bg-blue-50"
        >
          Open dashboard <span className="ml-2">→</span>
        </button>
        <p className="mt-8 text-xs text-slate-500">
          Powered by your existing Module 1 → Module 6 pipeline
        </p>
      </section>
    </main>
  );
}
function Feature({ icon, title, text }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur">
      <span className="text-xl text-blue-300">{icon}</span>
      <p className="mt-2 text-sm font-bold">{title}</p>
      <p className="mt-1 text-xs text-slate-400">{text}</p>
    </div>
  );
}
