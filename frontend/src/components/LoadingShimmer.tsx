export function CardShimmer() {
  return (
    <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50 animate-pulse">
      <div className="w-12 h-12 rounded-xl bg-gray-200 dark:bg-gray-800 mb-4" />
      <div className="h-5 bg-gray-200 dark:bg-gray-800 rounded-lg w-3/4 mb-3" />
      <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded-lg w-full mb-2" />
      <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded-lg w-5/6" />
    </div>
  );
}

export function ListShimmer({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-3 animate-pulse">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
          <div className="w-9 h-9 rounded-lg bg-gray-200 dark:bg-gray-800 shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded-lg w-1/3" />
            <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded-lg w-1/4" />
          </div>
          <div className="h-3 w-12 bg-gray-200 dark:bg-gray-800 rounded-lg" />
        </div>
      ))}
    </div>
  );
}
