import { useState } from 'react';
import { ThumbsUp, ThumbsDown, Send, CircleCheck as CheckCircle2 } from 'lucide-react';
import { submitFeedback } from '../api/client';

export default function FeedbackWidget({ recommendationId }) {
  const [selected, setSelected] = useState(null);
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
        <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-3" />
        <p className="text-sm font-semibold text-gray-900 mb-1">Thank you for your feedback!</p>
        <p className="text-xs text-gray-500">Your input helps improve our recommendations.</p>
      </div>
    );
  }

  return (
    <div id="feedback-widget" className="glass-card p-6 animate-slide-up">
      <p className="text-sm font-semibold text-gray-700 mb-4">
        Was this recommendation helpful?
      </p>

      <div className="flex items-center gap-3 mb-4">
        <button
          id="feedback-thumbs-up"
          type="button"
          onClick={() => handleSelect(true)}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-medium transition-all duration-200 cursor-pointer border ${
            selected === true
              ? 'bg-emerald-100 border-emerald-300 text-emerald-700'
              : 'bg-white border-gray-200 text-gray-500 hover:bg-emerald-50 hover:text-emerald-600 hover:border-emerald-200'
          }`}
        >
          <ThumbsUp className="w-4 h-4" />
          Helpful
        </button>

        <button
          id="feedback-thumbs-down"
          type="button"
          onClick={() => handleSelect(false)}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-medium transition-all duration-200 cursor-pointer border ${
            selected === false
              ? 'bg-rose-100 border-rose-300 text-rose-700'
              : 'bg-white border-gray-200 text-gray-500 hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200'
          }`}
        >
          <ThumbsDown className="w-4 h-4" />
          Not Helpful
        </button>
      </div>

      {selected !== null && (
        <div className="animate-fade-in">
          <textarea
            id="feedback-comment"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Any additional comments? (optional)"
            rows={2}
            className="w-full bg-white border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-700 placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500/30 focus:border-purple-400 transition-all duration-200 mb-3"
          />
          <button
            id="feedback-submit"
            type="button"
            onClick={handleSubmit}
            disabled={submitting}
            className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 text-white text-sm font-semibold rounded-full shadow-lg shadow-purple-500/25 transition-all duration-200 disabled:opacity-50 cursor-pointer"
          >
            <Send className="w-3.5 h-3.5" />
            {submitting ? 'Submitting...' : 'Submit Feedback'}
          </button>
        </div>
      )}
    </div>
  );
}
