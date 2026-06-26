import { CheckCircle2, Circle, Loader2 } from 'lucide-react';

const steps = [
  'Analyzing use case...',
  'Classifying complexity...',
  'Retrieving knowledge base...',
  'Checking compliance...',
  'Generating recommendation...',
];

export default function LoadingSteps({ currentStep }) {
  return (
    <div id="loading-steps" className="glass-card pulsing-cyan-glow p-8 animate-fade-in">
      <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
        <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
        AI Command Center is analyzing
      </h3>
      <div className="space-y-4">
        {steps.map((label, i) => {
          const isCompleted = i < currentStep;
          const isCurrent = i === currentStep;
          const isPending = i > currentStep;

          return (
            <div
              key={i}
              id={`loading-step-${i}`}
              className={`flex items-center gap-4 transition-all duration-500 ${
                isPending ? 'opacity-40' : 'opacity-100'
              }`}
            >
              {/* Icon */}
              <div className="flex-shrink-0">
                {isCompleted && (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 step-check" />
                )}
                {isCurrent && (
                  <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
                )}
                {isPending && (
                  <Circle className="w-5 h-5 text-slate-700" />
                )}
              </div>

              {/* Label */}
              <span
                className={`text-sm font-medium transition-colors duration-300 ${
                  isCompleted
                    ? 'text-emerald-400'
                    : isCurrent
                    ? 'text-cyan-400 font-semibold'
                    : 'text-slate-500'
                }`}
              >
                {label}
              </span>

              {/* Progress line */}
              {isCurrent && (
                <div className="ml-auto flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse [animation-delay:0.2s]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse [animation-delay:0.4s]" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
