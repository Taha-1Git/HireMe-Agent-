'use client';

export function ReportDashboard({ report }: { report: any }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold text-slate-900">Interview Report</h2>
      <pre className="max-h-96 overflow-auto rounded bg-slate-950 p-4 text-xs text-slate-100">
        {JSON.stringify(report, null, 2)}
      </pre>
    </div>
  );
}
