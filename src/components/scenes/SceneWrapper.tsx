import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

interface SceneWrapperProps {
  id: string;
  sceneNumber: number;
  title: string;
  fr: string;
  children: React.ReactNode;
  className?: string;
}

export function SceneWrapper({ id, sceneNumber, title, fr, children, className }: SceneWrapperProps) {
  return (
    <section id={id} className={cn("py-12 scroll-mt-28", className)}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="mb-6 flex items-center gap-3">
          <span className="flex items-center justify-center w-8 h-8 rounded-full bg-fornest-orange text-white text-sm font-bold shrink-0">
            {sceneNumber}
          </span>
          <div>
            <h2 className="text-xl font-bold text-slate-900">{title}</h2>
            <p className="text-xs text-slate-500 mt-0.5">{fr}</p>
          </div>
        </div>
        {children}
      </div>
    </section>
  );
}
