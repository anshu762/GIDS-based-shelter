import React, { useCallback, useEffect, useState } from "react";
import ScenarioForm from "./components/ScenarioForm.jsx";
import PipelineProgress from "./components/PipelineProgress.jsx";
import SummaryCards from "./components/SummaryCards.jsx";
import ShelterMap from "./components/ShelterMap.jsx";
import RecommendationsTable from "./components/RecommendationsTable.jsx";
import ChartsPanel from "./components/ChartsPanel.jsx";
import ScenarioHistory from "./components/ScenarioHistory.jsx";
import {
  createScenario,
  rerunScenario,
  pollJob,
  listScenarios,
  getScenario,
  deleteScenario,
} from "./lib/api.js";

export default function App() {
  const [submitting, setSubmitting] = useState(false);
  const [jobStatus, setJobStatus] = useState(null);
  const [scenarioData, setScenarioData] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [scenariosLoading, setScenariosLoading] = useState(true);
  const [activeScenarioId, setActiveScenarioId] = useState(null);
  const [banner, setBanner] = useState(null);

  useEffect(() => {
    if (!banner) return;
    const timer = setTimeout(() => setBanner(null), 6000);
    return () => clearTimeout(timer);
  }, [banner]);

  const refreshScenarios = useCallback(async () => {
    setScenariosLoading(true);
    try {
      const { scenarios: list } = await listScenarios();
      setScenarios(list);
    } catch (err) {
      setBanner({ type: "error", message: `Failed to load scenario history: ${err.message}` });
    } finally {
      setScenariosLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshScenarios();
  }, [refreshScenarios]);

  async function loadScenarioResult(scenarioId) {
    const data = await getScenario(scenarioId);
    setScenarioData(data);
    setActiveScenarioId(scenarioId);
  }

  async function runJobAndLoad(jobPromise) {
    setSubmitting(true);
    setBanner(null);
    try {
      const { job_id } = await jobPromise;
      setJobStatus({ status: "QUEUED" });

      const finalJob = await pollJob(job_id, {
        onTick: (job) => setJobStatus(job),
      });

      if (finalJob.status === "SUCCESS") {
        await loadScenarioResult(finalJob.scenario_id);
        await refreshScenarios();
        setBanner({ type: "success", message: "Pipeline completed successfully." });
      } else {
        setBanner({ type: "error", message: finalJob.error || "Pipeline failed." });
      }
    } catch (err) {
      setBanner({ type: "error", message: err.message });
      setJobStatus({ status: "FAILED", error: err.message });
    } finally {
      setSubmitting(false);
    }
  }

  function handleSubmit(payload) {
    runJobAndLoad(createScenario(payload));
  }

  function handleRerun(scenarioId) {
    runJobAndLoad(rerunScenario(scenarioId));
  }

  async function handleSelect(scenarioId) {
    setBanner(null);
    try {
      await loadScenarioResult(scenarioId);
    } catch (err) {
      setBanner({ type: "error", message: err.message });
    }
  }

  async function handleDelete(scenarioId) {
    try {
      await deleteScenario(scenarioId);
      if (activeScenarioId === scenarioId) {
        setScenarioData(null);
        setActiveScenarioId(null);
      }
      await refreshScenarios();
    } catch (err) {
      setBanner({ type: "error", message: err.message });
    }
  }

  const module6 = scenarioData?.Modules?.Module6;
  const module4 = scenarioData?.Modules?.Module4;
  const recommendation = module6?.final_recommendation;
  const summary = recommendation?.scenario_summary;
  const scenario = scenarioData?.Scenario;
  const mapShelters = recommendation?.top_recommendations || [];

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-8xl flex-col gap-1 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-lg text-white shadow-sm">
              <img src="/logo.png" alt="GIDS Logo" className="h-8 w-8" />
            </span>
            <div>
              <h1 className="text-lg font-bold leading-tight text-slate-900 sm:text-xl">
                GIDS Shelter Recommendation Dashboard
              </h1>
              <p className="text-xs text-slate-500 sm:text-sm">
                Disaster-aware evacuation shelter analysis. GIDS selection + multi-criteria ranking
              </p>
            </div>
          </div>
        </div>
      </header>

      {banner && (
        <div className="fixed right-4 top-20 z-30 w-[calc(100%-2rem)] max-w-sm animate-fadeIn sm:right-6">
          <div
            className={`flex items-start justify-between gap-3 rounded-lg px-4 py-3 text-sm font-medium shadow-lg ${
              banner.type === "error"
                ? "bg-red-600 text-white"
                : "bg-emerald-600 text-white"
            }`}
          >
            <span className="wrap-break-word">{banner.message}</span>
            <button
              onClick={() => setBanner(null)}
              className="shrink-0 text-white/80 hover:text-white"
              aria-label="Dismiss"
            >
              {"\u2715"}
            </button>
          </div>
        </div>
      )}

      <main className="mx-auto max-w-8xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[360px_1fr]">
          {/* Left column: input form + progress + history */}
          <div className="space-y-6 lg:sticky lg:top-24 lg:h-fit">
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="mb-4 text-sm font-semibold text-slate-700">
                New scenario input
              </h2>
              <ScenarioForm onSubmit={handleSubmit} submitting={submitting} />
            </div>

            {jobStatus && (
              <PipelineProgress
                status={jobStatus.status}
                progress={jobStatus.progress}
                error={jobStatus.error}
              />
            )}

            <ScenarioHistory
              scenarios={scenarios}
              activeScenarioId={activeScenarioId}
              onSelect={handleSelect}
              onRerun={handleRerun}
              onDelete={handleDelete}
              loading={scenariosLoading}
            />
          </div>

          {/* Right column: results */}
          <div className="min-w-0 space-y-6">
            {!scenarioData && (
              <div className="flex h-64 flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-slate-300 bg-white text-center text-sm text-slate-400">
                <span className="text-3xl">{"\uD83D\uDDFA\uFE0F"}</span>
                Run a scenario or select one from the history panel to see results.
              </div>
            )}

            {scenarioData && summary && (
              <>
                <SummaryCards summary={summary} />

                <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
                  <ShelterMap scenario={scenario} shelters={mapShelters} />
                  <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                    <h4 className="mb-3 text-sm font-semibold text-slate-700">
                      Recommendation message
                    </h4>
                    <dl className="space-y-3 text-xs text-slate-600">
                      <div>
                        <dt className="font-semibold text-slate-800">Headline</dt>
                        <dd className="mt-0.5">{recommendation.recommendation_message.Headline}</dd>
                      </div>
                      <div>
                        <dt className="font-semibold text-slate-800">Shelter solution</dt>
                        <dd className="mt-0.5">{recommendation.recommendation_message.ShelterSolution}</dd>
                      </div>
                      <div>
                        <dt className="font-semibold text-slate-800">Accommodation</dt>
                        <dd className="mt-0.5">{recommendation.recommendation_message.PopulationAccommodation}</dd>
                      </div>
                      <div>
                        <dt className="font-semibold text-slate-800">Unallocated</dt>
                        <dd className="mt-0.5">{recommendation.recommendation_message.UnallocatedPopulation}</dd>
                      </div>
                    </dl>
                  </div>
                </div>

                <ChartsPanel recommendation={recommendation} module4={module4} />

                <RecommendationsTable recommendation={recommendation} />
              </>
            )}
          </div>
        </div>
      </main>

      <footer className="mx-auto max-w-7xl px-4 py-6 text-center text-xs text-slate-400 sm:px-6 lg:px-8">
        Pipeline: Module 1 (affected population) through Module 6 (final
        recommendation). GIDS + Capacity Recovery selection, deterministic
        multi-criteria ranking.
      </footer>
    </div>
  );
}



























// ============== with welcome page updated once =================
// import React, { useCallback, useEffect, useState } from "react";
// import ScenarioForm from "./components/ScenarioForm.jsx";
// import WelcomePage from "./components/WelcomePage.jsx";
// import PipelineProgress from "./components/PipelineProgress.jsx";
// import SummaryCards from "./components/SummaryCards.jsx";
// import ShelterMap from "./components/ShelterMap.jsx";
// import RecommendationsTable from "./components/RecommendationsTable.jsx";
// import ChartsPanel from "./components/ChartsPanel.jsx";
// import ScenarioHistory from "./components/ScenarioHistory.jsx";
// import {
//   createScenario,
//   rerunScenario,
//   pollJob,
//   listScenarios,
//   getScenario,
//   deleteScenario,
// } from "./lib/api.js";
// export default function App() {
//   const [welcome, setWelcome] = useState(
//     () => sessionStorage.getItem("gids-welcome") !== "seen",
//   );
//   const [submitting, setSubmitting] = useState(false),
//     [job, setJob] = useState(null),
//     [data, setData] = useState(null),
//     [items, setItems] = useState([]),
//     [loading, setLoading] = useState(true),
//     [active, setActive] = useState(null),
//     [banner, setBanner] = useState(null);
//   const refresh = useCallback(async () => {
//     setLoading(true);
//     try {
//       setItems((await listScenarios()).scenarios || []);
//     } catch (e) {
//       setBanner({ type: "error", message: e.message });
//     } finally {
//       setLoading(false);
//     }
//   }, []);
//   useEffect(() => {
//     refresh();
//   }, [refresh]);
//   const open = () => {
//     sessionStorage.setItem("gids-welcome", "seen");
//     setWelcome(false);
//   };
//   async function load(id) {
//     const d = await getScenario(id);
//     setData(d);
//     setActive(id);
//   }
//   async function run(promise) {
//     setSubmitting(true);
//     setBanner(null);
//     setJob({ status: "QUEUED" });
//     try {
//       const start = await promise;
//       const end = await pollJob(start.job_id, setJob);
//       if (end.status === "FAILED")
//         throw new Error(end.error || "Pipeline failed");
//       await load(end.scenario_id);
//       await refresh();
//       setBanner({
//         type: "success",
//         message: "Pipeline completed successfully.",
//       });
//     } catch (e) {
//       setJob({ status: "FAILED", error: e.message });
//       setBanner({ type: "error", message: e.message });
//     } finally {
//       setSubmitting(false);
//     }
//   }
//   if (welcome) return <WelcomePage onEnter={open} />;
//   const m6 = data?.Modules?.Module6,
//     m4 = data?.Modules?.Module4,
//     rec = m6?.final_recommendation,
//     summary = rec?.scenario_summary;
//   return (
//     <div className="min-h-screen bg-slate-50">
//       <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
//         <div className="mx-auto flex max-w-[1500px] items-center gap-3 px-4 py-4 sm:px-6 lg:px-8">
//           <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-lg">
//             ⚠️
//           </span>
//           <div>
//             <h1 className="text-lg font-black text-slate-900 sm:text-xl">
//               GIDS Shelter Recommendation Dashboard
//             </h1>
//             <p className="text-xs text-slate-500">
//               Disaster intelligence · GIDS selection + multi-criteria ranking
//             </p>
//           </div>
//           <button
//             onClick={() => {
//               sessionStorage.removeItem("gids-welcome");
//               setWelcome(true);
//             }}
//             className="ml-auto rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50"
//           >
//             Welcome
//           </button>
//         </div>
//       </header>
//       {banner && (
//         <div
//           className={`fixed right-4 top-20 z-30 max-w-sm rounded-xl px-4 py-3 text-sm font-semibold text-white shadow-xl ${banner.type === "error" ? "bg-red-600" : "bg-emerald-600"}`}
//         >
//           {banner.message}
//         </div>
//       )}
//       <main className="mx-auto max-w-[1500px] px-4 py-6 sm:px-6 lg:px-8">
//         <div className="grid grid-cols-1 gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
//           <aside className="space-y-6 xl:sticky xl:top-24 xl:h-fit">
//             <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
//               <h2 className="mb-4 text-base font-black text-slate-900">
//                 New scenario input
//               </h2>
//               <ScenarioForm
//                 onSubmit={(p) => run(createScenario(p))}
//                 submitting={submitting}
//               />
//             </section>
//             {job && <PipelineProgress {...job} />}
//             <ScenarioHistory
//               items={items}
//               active={active}
//               onSelect={load}
//               onRerun={(id) => run(rerunScenario(id))}
//               onDelete={async (id) => {
//                 await deleteScenario(id);
//                 if (active === id) {
//                   setData(null);
//                   setActive(null);
//                 }
//                 await refresh();
//               }}
//               loading={loading}
//             />
//           </aside>
//           <section className="min-w-0 space-y-6">
//             {!summary ? (
//               <div className="flex min-h-[400px] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white text-center text-slate-400">
//                 <span className="text-4xl">🗺️</span>
//                 <p className="mt-3 text-sm">
//                   Run a scenario or select one from history to see results.
//                 </p>
//               </div>
//             ) : (
//               <>
//                 <SummaryCards summary={summary} />
//                 <div className="grid grid-cols-1 gap-4 2xl:grid-cols-[minmax(0,1fr)_350px]">
//                   <ShelterMap
//                     scenario={data.Scenario}
//                     shelters={rec.top_recommendations || []}
//                   />
//                   <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
//                     <h2 className="mb-4 text-sm font-black text-slate-900">
//                       Recommendation brief
//                     </h2>
//                     <div className="space-y-4 text-sm text-slate-600">
//                       <p>
//                         <b className="block text-xs uppercase tracking-wider text-slate-400">
//                           Headline
//                         </b>
//                         {rec.recommendation_message.Headline}
//                       </p>
//                       <p>
//                         <b className="block text-xs uppercase tracking-wider text-slate-400">
//                           Solution
//                         </b>
//                         {rec.recommendation_message.ShelterSolution}
//                       </p>
//                       <p>
//                         <b className="block text-xs uppercase tracking-wider text-slate-400">
//                           Accommodation
//                         </b>
//                         {rec.recommendation_message.PopulationAccommodation}
//                       </p>
//                       <p>
//                         <b className="block text-xs uppercase tracking-wider text-slate-400">
//                           Unallocated
//                         </b>
//                         {rec.recommendation_message.UnallocatedPopulation}
//                       </p>
//                     </div>
//                   </section>
//                 </div>
//                 <ChartsPanel recommendation={rec} module4={m4} />
//                 <RecommendationsTable recommendation={rec} />
//               </>
//             )}
//           </section>
//         </div>
//       </main>
//       <footer className="mx-auto max-w-[1500px] px-4 py-8 text-center text-xs text-slate-400 sm:px-6 lg:px-8">
//         Module 1 → Module 6 · Existing pipeline logic remains unchanged.
//       </footer>
//     </div>
//   );
// }