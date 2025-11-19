/**
 * LoadingSpinner Component
 * Reusable loading spinner with customizable size and message
 */

import React from 'react';
import './LoadingSpinner.css';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  message?: string;
  fullScreen?: boolean;
  color?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'medium',
  message,
  fullScreen = false,
  color = '#4285f4',
}) => {
  const sizeMap = {
    small: 24,
    medium: 40,
    large: 60,
  };

  const spinnerSize = sizeMap[size];

  const spinnerElement = (
    <div className="loading-spinner-container">
      <div
        className="loading-spinner"
        style={{
          width: spinnerSize,
          height: spinnerSize,
          borderColor: `${color}20`,
          borderTopColor: color,
        }}
      />
      {message && <p className="loading-message">{message}</p>}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="loading-spinner-overlay">
        {spinnerElement}
      </div>
    );
  }

  return spinnerElement;
};

export default LoadingSpinner;