/**
 * ErrorMessage Component
 * Display error messages with different severity levels
 */

import React from 'react';
import './ErrorMessage.css';

interface ErrorMessageProps {
  title?: string;
  message: string;
  type?: 'error' | 'warning' | 'info';
  onRetry?: () => void;
  onDismiss?: () => void;
  details?: string;
  showDetails?: boolean;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title,
  message,
  type = 'error',
  onRetry,
  onDismiss,
  details,
  showDetails = false,
}) => {
  const [detailsExpanded, setDetailsExpanded] = React.useState(showDetails);

  const icons = {
    error: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <circle cx="12" cy="12" r="10" strokeWidth="2" />
        <line x1="12" y1="8" x2="12" y2="12" strokeWidth="2" />
        <line x1="12" y1="16" x2="12.01" y2="16" strokeWidth="2" />
      </svg>
    ),
    warning: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" strokeWidth="2" />
        <line x1="12" y1="9" x2="12" y2="13" strokeWidth="2" />
        <line x1="12" y1="17" x2="12.01" y2="17" strokeWidth="2" />
      </svg>
    ),
    info: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <circle cx="12" cy="12" r="10" strokeWidth="2" />
        <line x1="12" y1="16" x2="12" y2="12" strokeWidth="2" />
        <line x1="12" y1="8" x2="12.01" y2="8" strokeWidth="2" />
      </svg>
    ),
  };

  const defaultTitles = {
    error: 'Error',
    warning: 'Warning',
    info: 'Information',
  };

  return (
    <div className={`error-message error-message--${type}`} role="alert">
      <div className="error-message__icon">{icons[type]}</div>

      <div className="error-message__content">
        <h3 className="error-message__title">
          {title || defaultTitles[type]}
        </h3>
        <p className="error-message__message">{message}</p>

        {details && (
          <div className="error-message__details-container">
            <button
              className="error-message__details-toggle"
              onClick={() => setDetailsExpanded(!detailsExpanded)}
            >
              {detailsExpanded ? 'Hide' : 'Show'} details
            </button>
            {detailsExpanded && (
              <pre className="error-message__details">{details}</pre>
            )}
          </div>
        )}

        <div className="error-message__actions">
          {onRetry && (
            <button
              className="error-message__button error-message__button--primary"
              onClick={onRetry}
            >
              Try Again
            </button>
          )}
          {onDismiss && (
            <button
              className="error-message__button error-message__button--secondary"
              onClick={onDismiss}
            >
              Dismiss
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorMessage;