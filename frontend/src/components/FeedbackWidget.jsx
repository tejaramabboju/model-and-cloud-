import { useState } from 'react';
import { ThumbsUp, ThumbsDown, Send, CheckCircle2 } from 'lucide-react';
import { submitFeedback } from '../api/client';

export default function FeedbackWidget({ recommendationId }) {
  const [selected, setSelected] = useState(null); // true = up, false = down
  const [comment, setComment] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleSelect = (rating) => {
    if (submitted) return;
    setSelected(rating);
  };

  const handleSubmit = async () => {
    if (selected === null || submitting) return;
    setSubmitting(true);
    try {
      await submitFeedback({
        recommendation_id: recommendationId,
        rating: selected,
        comment: comment.trim() || null,
      });
      setSubmitted(true);
    } catch (err) {
      console.error('Feedback submission failed:', err);
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div
        id="feedback-thank-you"
        className="glass-card p-6 text-center animate-fade-in"
      >
        <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-3 step-check" />
        <p className="text-sm font-semibold text-slate-950 mb-1">Thank you for your feedback!</p>
        <p className="text-xs text-slate-500">Your input helps improve our recommendations.</p>
      </div>
    );
  }

  return (
    <div id="feedback-widget" className="glass-card p-6 animate-slide-up">
      <p className="text-sm font-semibold text-slate-300 mb-4">
        Was this recommendation helpful?
      </p>

      {/* Thumbs */}
      <div className="flex items-center gap-3 mb-4">
        <button
          id="feedback-thumbs-up"
          type="button"
          onClick={() => handleSelect(true)}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 cursor-pointer border ${
            selected === true
              ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-600'
              : 'bg-slate-900 border-slate-800 text-slate-600 hover:bg-emerald-500/10 hover:text-emerald-500 hover:border-emerald-500/20'
          }`}
        >
          <ThumbsUp className="w-4 h-4" />
          Helpful
        </button>

        <button
          id="feedback-thumbs-down"
          type="button"
          onClick={() => handleSelect(false)}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 cursor-pointer border ${
            selected === false
              ? 'bg-rose-500/20 border-rose-500/40 text-rose-600'
              : 'bg-slate-900 border-slate-800 text-slate-600 hover:bg-rose-500/10 hover:text-rose-500 hover:border-rose-500/20'
          }`}
        >
          <ThumbsDown className="w-4 h-4" />
          Not Helpful
        </button>
      </div>

      {/* Comment (shown after selection) */}
      {selected !== null && (
        <div className="animate-fade-in">
          <textarea
            id="feedback-comment"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Any additional comments? (optional)"
            rows={2}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-950 placeholder-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 transition-all duration-200 mb-3"
          />
          <button
            id="feedback-submit"
            type="button"
            onClick={handleSubmit}
            disabled={submitting}
            className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white text-sm font-semibold rounded-xl shadow-lg shadow-blue-500/25 transition-all duration-200 disabled:opacity-50 cursor-pointer"
          >
            <Send className="w-3.5 h-3.5" />
            {submitting ? 'Submitting...' : 'Submit Feedback'}
          </button>
        </div>
      )}
    </div>
  );
}
