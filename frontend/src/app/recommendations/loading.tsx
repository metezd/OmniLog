import LoadingState from "@/components/states/LoadingState";

export default function RecommendationsLoading() {
  return (
    <div className="relative z-10 mx-auto w-full max-w-7xl space-y-6 px-4 py-8 sm:px-8">
      <div className="border-b border-white/10 pb-4">
        <h1 className="text-xl font-bold tracking-tight text-white">Recommendations</h1>
        <p className="text-xs text-slate-400">
          Personalized cross-media recommendations based on your library
        </p>
      </div>
      <LoadingState label="Loading recommendations..." />
    </div>
  );
}
