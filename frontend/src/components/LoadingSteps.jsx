import { CircleCheck as CheckCircle2, Circle, Loader as Loader2 } from 'lucide-react';

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
      <h3 className="text-lg font-semibold mb-6 flex items-center gap-2" style={{ color: '#1E1B4B' }}>
        <Loader2 className="w-5 h-5 text-purple-500 animate-spin" />
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
              <div className="flex-shrink-0">
                {isCompleted && (
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                )}
                {isCurrent && (
                  <Loader2 className="w-5 h-5 text-purple-500 animate-spin" />
                )}
                {isPending && (
                  <Circle className="w-5 h-5 text-gray-300" />
                )}
              </div>

              <span
                className={`text-sm font-medium transition-colors duration-300 ${
                  isCompleted
                    ? 'text-emerald-600'
                    : isCurrent
                    ? 'text-purple-700 font-semibold'
                    : 'text-gray-400'
                }`}
              >
                {label}
              </span>

              {isCurrent && (
                <div className="ml-auto flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" />
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse [animation-delay:0.2s]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse [animation-delay:0.4s]" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
